# Copyright 2024 The HuggingFace Inc. team. All rights reserved.
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
from typing import TYPE_CHECKING, Optional

from .base import HfQuantizer


if TYPE_CHECKING:
    from ..modeling_utils import PreTrainedModel

from ..integrations import replace_with_quanto_linear
from ..utils import is_quanto_available, is_torch_available, logging
from ..utils.quantization_config import QuantoConfig


if is_torch_available():
    import torch

logger = logging.get_logger(__name__)


class QuantoHfQuantizer(HfQuantizer):
    """
    Quantizer for the quanto library
    """

    required_packages = ["quanto", "accelerate"]

    def __init__(self, quantization_config: QuantoConfig, **kwargs):
        self.requires_calibration = quantization_config.activations is not None
        super().__init__(quantization_config, **kwargs)

    def validate_environment(self, *args, **kwargs):
        if is_quanto_available():
            raise ImportError("Loading a quanto quantized model requires quanto library (`pip install quanto`)")

    def update_torch_dtype(self, torch_dtype: "torch.dtype") -> "torch.dtype":
        if torch_dtype is None:
            if torch.cuda.is_available():
                torch_dtype = torch.float16
                logger.info(
                    "CUDA available. Assuming Quanto inference on GPU and loading the model in `torch.float16`. To overwrite it, set `torch_dtype` manually."
                )
            else:
                torch_dtype = torch.float32
                logger.info(
                    "CUDA is unavailable. Assuming AQLM inference on CPU and loading the model in `torch.float32`. To overwrite it, set `torch_dtype` manually."
                )
        return torch_dtype

    def _process_model_before_weight_loading(self, model: "PreTrainedModel", **kwargs):
        if self.pre_quantized:
            replace_with_quanto_linear(model, quantization_config=self.quantization_config)
        model.config.quantization_config = self.quantization_config

    def _process_model_after_weight_loading(self, model):
        if not self.pre_quantized:
            from quanto import freeze, quantize

            quantize(model, weights=self.quantization_config.weights, activations=self.quantization_config)
            freeze(model)

    @property
    def is_trainable(self, model: Optional["PreTrainedModel"] = None):
        return False

    @property
    def is_serializable(self):
        return True
