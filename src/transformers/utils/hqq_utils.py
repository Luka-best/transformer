# Copyright 2024 The HuggingFace Team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from . import is_hqq_available, is_torch_available


if is_torch_available():
    import torch

if is_hqq_available():
    from hqq.core.quantize import HQQLinear
else:
    HQQLinear = None


# Name all modules inside the model
def autoname_modules(model):
    for name, module in model.named_modules():
        module.name = name


# Get the linear_tag from a modul name. For example: model.layers.31.self_attn.k_proj -> self_attn.k_proj
def name_to_linear_tag(name):
    return ".".join([n for n in name.split(".") if ((n not in ["model", "layers"]) and (not n.isnumeric()))])


# Get all linear tags available
def get_linear_tags(model):
    linear_tags = set()
    for name, module in model.named_modules():
        if type(module) in [torch.nn.Linear, HQQLinear]:
            linear_tags.add(name_to_linear_tag(name))
    return list(linear_tags)


# Finds the parent of a node module named "name"
def find_parent(model, name):
    module_tree = name.split(".")[:-1]
    parent = model
    for m in module_tree:
        parent = parent._modules[m]
    return parent


# checks if a module is a leaf: doesn't have another module inside
def is_leaf_module(module):
    return len(module._modules) == 0


# Returns layers to ignores. These layers are typically not leaves we are interested in for storage and loading
def get_ignore_layers(model):
    layers = {""}
    for name, module in model.named_modules():
        if not is_leaf_module(module):
            layers.add(name)
    return list(layers)


# Checks if a quant config is an HQQ quant config
def check_if_hqq_quant_config(quant_config):
    if quant_config is None:
        return False
    q_keys = list(quant_config.keys())
    q_vals = [quant_config[k] for k in quant_config][0]
    if isinstance(q_vals, dict):
        q_keys = q_keys + list([quant_config[k] for k in quant_config][0].keys())
    return "weight_quant_params" in q_keys


# Returns a new module from a dummy (meta) module and a dictionary of module name -> state_dict
@torch.no_grad()
def load_hqq_module(module, weights, compute_dtype, device):
    if module.name not in weights:
        try:
            return module.to(compute_dtype).cuda(device)
        except Exception:
            return module

    state_dict = weights[module.name]
    if ("W_q" in state_dict) and ("meta" in state_dict):
        module = HQQLinear(linear_layer=None, quant_config=None, compute_dtype=compute_dtype, device=device)
        module.load_state_dict(state_dict)
    else:
        for key in state_dict:
            setattr(module, key, torch.nn.Parameter(state_dict[key].to(compute_dtype).to(device), requires_grad=False))

    return module
