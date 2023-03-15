# Copyright 2020 The HuggingFace Team. All rights reserved.
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
from typing import TYPE_CHECKING

from ...utils import  _LazyModule, OptionalDependencyNotAvailable, is_tokenizers_available
from ...utils import is_tf_available



from ...utils import is_torch_available



from ...utils import is_flax_available




_import_structure = {
    "configuration_codegeex": ["CODEGEEX_PRETRAINED_CONFIG_ARCHIVE_MAP", "CodeGeeXConfig"],
    "tokenization_codegeex": ["CodeGeeXTokenizer"],
}

try:
    if not is_tokenizers_available():
        raise OptionalDependencyNotAvailable()
except OptionalDependencyNotAvailable:
    pass
else:
    _import_structure["tokenization_codegeex_fast"] = ["CodeGeeXTokenizerFast"]

try:
    if not is_torch_available():
        raise OptionalDependencyNotAvailable()
except OptionalDependencyNotAvailable:
    pass
else:
    _import_structure["modeling_codegeex"] = [
        "CODEGEEX_PRETRAINED_MODEL_ARCHIVE_LIST",
        "CodeGeeXForConditionalGeneration",
        "CodeGeeXForQuestionAnswering",
        "CodeGeeXForSequenceClassification",
        "CodeGeeXForCausalLM",
        "CodeGeeXModel",
        "CodeGeeXPreTrainedModel",
    ]



try:
    if not is_tf_available():
        raise OptionalDependencyNotAvailable()
except OptionalDependencyNotAvailable:
    pass
else:
    _import_structure["modeling_tf_codegeex"] = [
        "TFCodeGeeXForConditionalGeneration",
        "TFCodeGeeXModel",
        "TFCodeGeeXPreTrainedModel",
    ]



try:
    if not is_flax_available():
        raise OptionalDependencyNotAvailable()
except OptionalDependencyNotAvailable:
    pass
else:
    _import_structure["modeling_flax_codegeex"] = [
        "FlaxCodeGeeXForConditionalGeneration",
        "FlaxCodeGeeXForQuestionAnswering",
        "FlaxCodeGeeXForSequenceClassification",
        "FlaxCodeGeeXModel",
        "FlaxCodeGeeXPreTrainedModel",
    ]




if TYPE_CHECKING:
    from .configuration_codegeex import CODEGEEX_PRETRAINED_CONFIG_ARCHIVE_MAP, CodeGeeXConfig
    from .tokenization_codegeex import CodeGeeXTokenizer

    try:
        if not is_tokenizers_available():
            raise OptionalDependencyNotAvailable()
    except OptionalDependencyNotAvailable:
        pass
    else:
        from .tokenization_codegeex_fast import CodeGeeXTokenizerFast

    try:
        if not is_torch_available():
            raise OptionalDependencyNotAvailable()
    except OptionalDependencyNotAvailable:
        pass
    else:
        from .modeling_codegeex import (
            CODEGEEX_PRETRAINED_MODEL_ARCHIVE_LIST,
            CodeGeeXForConditionalGeneration,
            CodeGeeXForCausalLM,
            CodeGeeXForQuestionAnswering,
            CodeGeeXForSequenceClassification,
            CodeGeeXModel,
            CodeGeeXPreTrainedModel,
        )



    try:
        if not is_tf_available():
            raise OptionalDependencyNotAvailable()
    except OptionalDependencyNotAvailable:
        pass
    else:
        from .modeling_tf_codegeex import (
            TFCodeGeeXForConditionalGeneration,
            TFCodeGeeXModel,
            TFCodeGeeXPreTrainedModel,
        )



    try:
        if not is_flax_available():
            raise OptionalDependencyNotAvailable()
    except OptionalDependencyNotAvailable:
        pass
    else:
        from .modeling_codegeex import (
            FlaxCodeGeeXForConditionalGeneration,
            FlaxCodeGeeXForQuestionAnswering,
            FlaxCodeGeeXForSequenceClassification,
            FlaxCodeGeeXModel,
            FlaxCodeGeeXPreTrainedModel,
        )



else:
    import sys

    sys.modules[__name__] = _LazyModule(__name__, globals()["__file__"], _import_structure, module_spec=__spec__)
