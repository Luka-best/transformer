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
from __future__ import annotations

import os
from typing import TYPE_CHECKING

from ..utils import is_torch_available


if TYPE_CHECKING:
    from torch import nn


def is_fsdp_managed_module(module: nn.Module) -> bool:
    if not is_torch_available():
        return False

    import torch.distributed.fsdp

    return isinstance(module, torch.distributed.fsdp.FullyShardedDataParallel) or getattr(
        module, "_is_fsdp_managed_module", False
    )


def enable_cpu_ram_efficient_loading():
    """
    Enable CPU RAM efficient loading of model weights by setting `FSDP_CPU_RAM_EFFICIENT_LOADING`.
    """
    os.environ["FSDP_CPU_RAM_EFFICIENT_LOADING"] = "true"


def disable_cpu_ram_efficient_loading():
    """
    Disable CPU RAM efficient loading of model weights by unsetting `FSDP_CPU_RAM_EFFICIENT_LOADING`.
    """
    os.environ["FSDP_CPU_RAM_EFFICIENT_LOADING"] = "false"


def set_cpu_ram_efficient_loading(value: bool):
    """
    Set CPU RAM efficient loading of model weights by setting `FSDP_CPU_RAM_EFFICIENT_LOADING`.
    """
    os.environ["FSDP_CPU_RAM_EFFICIENT_LOADING"] = str(bool(value)).lower()
