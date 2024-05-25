import argparse
import glob
import importlib
import re

import libcst as cst
from check_copies import fix_ruff
from libcst import ClassDef, CSTTransformer, CSTVisitor
from libcst import matchers as m
from libcst.metadata import MetadataWrapper, ParentNodeProvider, ScopeProvider



def get_module_source_from_name(module_name: str) -> str:
    spec = importlib.util.find_spec(module_name)
    if spec is None or spec.origin is None:
        return f"Module {module_name} not found"

    with open(spec.origin, "r") as file:
        source_code = file.read()

    return source_code



class ClassFinder(CSTVisitor):
    METADATA_DEPENDENCIES = (ParentNodeProvider,ScopeProvider)

    def __init__(self, python_module):
        self.python_module = python_module
        self.classes = {}  # class LlamaAttentino
        self.imports = {}  # from flash_attn import
        self.function_def = {}  # def repeat_kv
        self.assignments = {}  # LLAMA_DOCSTRING
        self.protected_imports = {}  # if is_xxx_available()
        self.class_dependency_mapping = {} # "LlamaModel":["LlamaDecoderLayer, "LlamaRMSNorm", "LlamaPreTrainedModel"], "LlamaDecoderLayer":["LlamaAttention","Llama"]

    def visit_ClassDef(self, node: ClassDef) -> None:
        self.classes[node.name.value] = node
        for k in node.bases:
            name = self.python_module.code_for_node(k)
            self.class_dependency_mapping.update(
                {
                    node.name.value: {
                        name: self.class_dependency_mapping.get(name) , **self.class_dependency_mapping.get(node.name.value, {})
                    }
                }
            )


    def visit_SimpleStatementLine(self, node):
        match node:
            case cst.SimpleStatementLine(body=[cst.Assign(targets=[_], value=_)]):
                if m.matches(self.get_metadata(cst.metadata.ParentNodeProvider, node), m.Module()):
                    self.assignments[node.body[0].targets[0].target.value] = node
            case cst.SimpleStatementLine(body=[cst.Import(names=[_])]):
                self.imports[node.body[0].names] = node
            case cst.SimpleStatementLine(body=[cst.ImportFrom(_)]):
                self.imports[node.body[0].names] = node

    def visit_FunctionDef(self, node):
        parent_node = self.get_metadata(cst.metadata.ParentNodeProvider, node)
        if m.matches(parent_node, m.Module()):
            self.function_def[node.name.value] = node

    def leave_If(self, node):
        for stmt in node.body.body:
            if m.matches(stmt, m.SimpleStatementLine(body=[m.ImportFrom() | m.Import()])):
                self.imports[stmt.body[0].names] = node  # match the visit simple statement line to overwrite it

    def leave_Name(self, node): 
        if node.value in self.classes.keys() | self.assignments.keys() | self.function_def.keys():
            dad = self.get_metadata(cst.metadata.ScopeProvider,node)
            if not isinstance(dad, cst.metadata.scope_provider.GlobalScope):
                print(f"Name:\t\t{node.value:<45} called in {dad._name_prefix}") 
                if hasattr(dad.parent, "name"):
                    name = dad._name_prefix.split(".")[0]
                    if name not in self.class_dependency_mapping:
                        self.class_dependency_mapping[name] = {node.value:self.class_dependency_mapping.get(node.value)}
                    else:
                        self.class_dependency_mapping[name].update({node.value:self.class_dependency_mapping.get(node.value)})
                elif hasattr(dad, "name"):
                    name = dad.name
                    if dad.name not in self.class_dependency_mapping:
                        self.class_dependency_mapping[dad.name] = {node.value:self.class_dependency_mapping.get(node.value)}
                    else:
                        self.class_dependency_mapping[dad.name].update( {node.value:self.class_dependency_mapping.get(node.value)}) 

    def leave_Dict(self, node):
        dad = self.get_metadata(cst.metadata.ParentNodeProvider, node)
        if m.matches(dad,m.Assign(targets=[m.AssignTarget()])):
            name = dad.targets[0].target.value
            if name in self.assignments:
                for k in node.elements:
                    if k.value.value in self.classes:

                        if name not in self.class_dependency_mapping:
                            self.class_dependency_mapping[name] = {k.value.value:self.class_dependency_mapping.get(k.value.value)}
                        else:
                            self.class_dependency_mapping[name].update( {k.value.value:self.class_dependency_mapping.get(k.value.value)}) 
                        print(f"Dict:\t\t{k.value.value:<45} called in {name}")  

    # Decorator: handle in leave_FunctionDef and leave_ClassDef instead
    def leave_Decorator(self, node):
        if hasattr(node.decorator, "args"):
            for k in node.decorator.args:
                if k.value.value in self.assignments:
                    dad = self.get_metadata(cst.metadata.ParentNodeProvider, node)
                    print(f"Decorator:\t{k.value.value:<45} called in {dad.name.value}")
                    if dad.name.value not in self.class_dependency_mapping:
                        self.class_dependency_mapping[dad.name.value] = {k.value.value:self.class_dependency_mapping.get(k.value.value)}
                    else:
                        self.class_dependency_mapping[dad.name.value].update( {k.value.value:self.class_dependency_mapping.get(k.value.value)}) 

    def leave_Module(self, node):
        self.global_node = {**self.assignments, **self.classes, **self.function_def}
class ReplaceNameTransformer(m.MatcherDecoratableTransformer):
    def __init__(self, old_name, new_name):
        super().__init__()
        self.new_name = new_name
        self.old_name = old_name
        self.regex = re.compile(re.escape(self.old_name), re.IGNORECASE)

    def preserve_case_replace(self, text):
        def replace(match):
            word = match.group()
            if word.isupper():
                return self.new_name.upper()
            elif word.istitle():
                return self.new_name.title()
            elif word.islower():
                return self.new_name.lower()
            else:
                return self.new_name.title()

        return self.regex.sub(replace, text)

    @m.leave(m.Name() | m.SimpleString() | m.Comment())
    def replace_name(self, original_node, updated_node):
        update = self.preserve_case_replace(updated_node.value)
        return updated_node.with_changes(value=update)


def find_classes_in_file(module, old_id="llama", new_id="gemma"):
    transformer = ReplaceNameTransformer(old_id, new_id)
    new_module = module.visit(transformer)

    wrapper = MetadataWrapper(new_module)

    class_finder = ClassFinder(new_module)
    wrapper.visit(class_finder)
    return class_finder


class DiffConverterTransformer(CSTTransformer):
    def __init__(self, python_module):
        super().__init__()
        self.python_module = python_module
        self.transformers_imports = {}
        self.transformers_mapping = {}
        self.class_mapping = {}
        self.visited_module = {}
        self.python_module = python_module
        self.functions_to_insert = {}
        self.inserted_functions = set()
        self.new_body = []

    def visit_ImportFrom(self, node: cst.ImportFrom) -> None:
        if m.matches(node.module, m.Attribute()):
            full_statement = self.python_module.code_for_node(node.module)
            for imported_ in node.names:
                if re.search(r"transformers\.models\..*\.modeling_.*", full_statement):
                    if full_statement not in self.transformers_imports:
                        source_code = get_module_source_from_name(full_statement)
                        tree = cst.parse_module(source_code)
                        self.transformers_imports[full_statement] = tree
                    self.transformers_mapping[self.python_module.code_for_node(imported_.name)] = full_statement
                if re.search(r"transformers\.models\..*\.configuration_.*", full_statement):
                    if full_statement not in self.transformers_imports:
                        source_code = get_module_source_from_name(full_statement)
                        tree = cst.parse_module(source_code)
                        self.transformers_imports[full_statement] = tree
                    self.transformers_mapping[self.python_module.code_for_node(imported_.name)] = full_statement

    def visit_ClassDef(self, node: cst.Assign) -> None:
        if m.matches(node.name, m.Name()):
            super_class = [k.value.value for k in node.bases if k.value.value in self.transformers_mapping]
            class_name = node.name.value
            if len(super_class) > 0:
                super_class = super_class[0]
                parent_package = self.transformers_mapping.get(super_class, None)
                if parent_package and parent_package not in self.visited_module:
                    old_name = re.findall(r"[A-Z][a-z0-9]*", super_class)[0].lower()
                    new_name = re.findall(r"[A-Z][a-z0-9]*", class_name)[0].lower()
                    # We need to find all the classes, to copy everything, if they are used
                    class_finder = find_classes_in_file(
                        self.transformers_imports[parent_package], old_name, new_name
                    )
                    self.visited_module[parent_package] = class_finder

                    # I don't know what this is
                    self.class_mapping[self.python_module.code_for_node(node)] = class_finder.classes[class_name]

                if self.visited_module[parent_package]:
                    class_finder = self.visited_module[parent_package]
                    list_dependencies = class_finder.class_dependency_mapping[class_name]
                    for dependency in list_dependencies:
                        # TODO the dependencies needs to be properly handled
                        node = class_finder.global_node.get(dependency, None)
                        if node is not None and node not in self.new_body:
                            self.new_body += [node]
                    # finally add the code of the current class
                    self.new_body += [class_finder.classes[class_name]]


    def leave_SimpleStatementLine(self, original_node: cst.Assign, updated_node: cst.CSTNode):
        match updated_node:
            # note: this is just a plain copy & paste of the pattern as seen in the CST
            case cst.SimpleStatementLine(body=[cst.Assign(targets=[_], value=_)]):
                assign = self.python_module.code_for_node(original_node.body[0])
                node = original_node.body[0]
                if m.matches(node.value, m.Name()) and assign in self.class_mapping:
                    return self.class_mapping[assign]
        if m.matches(updated_node, m.SimpleStatementLine(body=[m.ImportFrom()])):
            full_statement = self.python_module.code_for_node(updated_node.body[0].module)
            if re.search(r"transformers\.models\..*\.[modeling|configuration]_.*", full_statement):
                return cst.RemoveFromParent()
        return updated_node

    def leave_ClassDef(self, original_node: cst.Assign, updated_node):
        for base in original_node.bases:
            base_name = self.python_module.code_for_node(base)
            if base_name in self.transformers_mapping:
                super_classes = self.visited_module[self.transformers_mapping[base_name]].classes
                replacement_class = super_classes[updated_node.name.value]
                dependencies = self.visited_module[self.transformers_mapping[base_name]].class_dependency_mapping
                # Copy methods from original node to replacement node, preserving decorators
                updated_methods = {f.name.value: f for f in updated_node.body.body if m.matches(f, m.FunctionDef())}
                replacement_methods = {
                    f.name.value: f for f in replacement_class.body.body if m.matches(f, m.FunctionDef())
                }

                for name, func in updated_methods.items():
                    if name in replacement_methods:
                        # Replace the method in the replacement class, preserving decorators
                        replacement_func = replacement_methods[name].with_changes(
                            decorators=replacement_methods[name].decorators,  # TODO a union or set might be better
                            body=func.body,
                        )
                        replacement_methods[name] = replacement_func

                # Rebuild the class body with updated methods
                new_body = [
                    replacement_methods.get(f.name.value, f) if m.matches(f, m.FunctionDef()) else f
                    for f in replacement_class.body.body
                ]

                new_replacement_class = replacement_class.with_changes(body=cst.IndentedBlock(body=new_body))

                temp_module = cst.Module(body=[new_replacement_class])
                new_module = MetadataWrapper(temp_module)
                # Ensure calls to `super()` in `__init__` are preserved
                new_replacement_class = new_module.visit(
                    SuperTransformer(
                        temp_module,
                        {f.name.value: f for f in replacement_class.body.body if m.matches(f, m.FunctionDef())},
                    )
                ).body[0]

                return new_replacement_class

        return updated_node

    def leave_Call(self, original_node, updated_node):
        func_name = None
        if m.matches(original_node.func, m.Name()):
            func_name = original_node.func.value
        elif m.matches(original_node.func, m.Attribute()):
            func_name = original_node.func.attr.value

        if func_name and func_name in self.functions_to_insert and func_name not in self.inserted_functions:
            self.new_body.append(self.functions_to_insert[func_name])
            self.inserted_functions.add(func_name)

        self.new_body.append(updated_node)
        return updated_node
    
    def leave_Module(self, original_node: cst.Assign, node):
        new_body = self.new_body
        for visiter in self.visited_module.values():
            new_body += list(visiter.imports.values())
        #     new_body += list(visiter.assignments.values())
        #     new_body += list(visiter.function_def.values())

        return node.with_changes(body=[*new_body, *node.body])



class SuperTransformer(cst.CSTTransformer):
    METADATA_DEPENDENCIES = (ParentNodeProvider,)

    def __init__(self, python_module, original_methods):
        self.original_methods = original_methods
        self.python_module = python_module

    def leave_FunctionDef(self, original_node: cst.Call, updated_node: cst.Call) -> cst.CSTNode:
        if updated_node.name.value in self.original_methods:
            updated_body = cst.ensure_type(updated_node.body, cst.IndentedBlock)
            new_body = self.replace_super_calls(updated_body, updated_node.name.value)
            return updated_node.with_changes(body=new_body)
        return updated_node

    def replace_super_calls(self, node: cst.IndentedBlock, func_name: str) -> cst.CSTNode:
        new_body = []
        for expr in node.body:
            if m.matches(
                expr,
                m.SimpleStatementLine(
                    body=[m.Call(func=m.Attribute(value=m.Call(func=m.Name("super")), attr=m.Name(func_name)))]
                ),
            ):
                # Replace the SimpleStatementLine containing super().__init__() with the new body from func_to_body_mapping
                new_body.extend(self.original_methods[func_name].body.body)
            elif m.matches(
                expr,
                m.SimpleStatementLine(
                    body=[
                        m.Return(
                            value=m.Call(func=m.Attribute(value=m.Call(func=m.Name("super")), attr=m.Name(func_name)))
                        )
                    ]
                ),
            ):
                new_body.extend(self.update_body(self.original_methods[func_name].body.body, node.body))
            else:
                new_body.append(expr)
        return node.with_changes(body=new_body)

    def update_body(self, existing_body, new_statements):
        """
        Helper method to update the body by removing duplicates before adding new statements.
        """
        de_duplicated_new_body = []
        existing_nodes = {
            self.python_module.code_for_node(node).strip() for node in new_statements if isinstance(node, cst.CSTNode)
        }
        for stmt in existing_body:
            if self.python_module.code_for_node(stmt).strip() not in existing_nodes:
                de_duplicated_new_body.append(stmt)
                existing_nodes.add(stmt)
            else:
                print(f"\n{30*'#'}found duplicate{self.python_module.code_for_node(stmt)}{30*'#'}")
        return de_duplicated_new_body

    def leave_Return(self, original_node: cst.Return, updated_node: cst.Return) -> cst.CSTNode:
        if m.matches(updated_node.value, m.Call(func=m.Attribute(attr=m.Name("super")))):
            func_def = self.get_metadata(ParentNodeProvider, updated_node)
            if isinstance(func_def, cst.FunctionDef) and func_def.name.value in self.original_methods:
                updated_return_value = updated_node.value.with_changes(
                    args=[
                        cst.Arg(
                            value=cst.Call(func=cst.Name("super"), args=[cst.Arg(value=cst.Name(func_def.name.value))])
                        )
                    ]
                )
                return updated_node.with_changes(value=updated_return_value)
        return updated_node




def convert_file(diff_file):
    # Parse the Python file
    with open(diff_file, "r") as file:
        code = file.read()
    module = cst.parse_module(code)
    transformers = DiffConverterTransformer(module)
    new_mod = module.visit(transformers)
    ruffed_code = fix_ruff(new_mod.code)

    # with open(diff_file.replace("diff_", "modeling_"), "w") as f:
    #     f.write(ruffed_code)
    with open(diff_file.replace("diff_", "modeling_draft_"), "w") as f:
        f.write(ruffed_code)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--files_to_parse",
        default="all",
        help="A list of `diff_xxxx` files that should be converted to single model file",
    )
    args = parser.parse_args()
    if args.files_to_parse == "all":
        args.files_to_parse = glob.glob("src/transformers/models/**/diff_*.py", recursive=True)
    for file_name in args.files_to_parse:
        print(f"Converting {file_name} to a single model single file format")
        module_path = file_name.replace("/", ".").replace(".py", "").replace("src.", "")
        converter = convert_file(file_name)
