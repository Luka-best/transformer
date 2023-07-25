# coding=utf-8
# Copyright 2022 EleutherAI and the HuggingFace Inc. team. All rights reserved.
#
# This code is based on EleutherAI's GPT-NeoX library and the GPT-NeoX
# and OPT implementations in this library. It has been modified from its
# original forms to accommodate minor architectural differences compared
# to GPT-NeoX and OPT used by the Meta AI team that trained the model.
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
""" Idefics model configuration"""
import os
from typing import Union

from transformers import AutoConfig
from transformers.configuration_utils import PretrainedConfig
from transformers.utils import logging


logger = logging.get_logger(__name__)

IDEFICS_PRETRAINED_CONFIG_ARCHIVE_MAP = {
    "HuggingFaceM4/idefics-9b": "https://huggingface.co/HuggingFaceM4/idefics-9b/blob/main/config.json",
    "HuggingFaceM4/idefics-80b": "https://huggingface.co/HuggingFaceM4/idefics-80b/blob/main/config.json",
}


class IdeficsConfig(PretrainedConfig):
    r"""
    TODO: update docstring with respect to new arguments

    e.g. [HuggingFaceM4/idefics-80b](https://huggingface.co/HuggingFaceM4/idefics-80b)

    This is the configuration class to store the configuration of a [`~IdeficsModel`]. It is used to instantiate an
    Idefics model according to the specified arguments, defining the model architecture. Instantiating a configuration
    with the defaults will yield a similar configuration to that of the Idefics-9B.

    Configuration objects inherit from [`PretrainedConfig`] and can be used to control the model outputs. Read the
    documentation from [`PretrainedConfig`] for more information.


    Args:
        vocab_size (`int`, *optional*, defaults to 32000):
            Vocabulary size of the Idefics model. Defines the number of different tokens that can be represented by the
            `inputs_ids` passed when calling [`~IdeficsModel`]
        hidden_size (`int`, *optional*, defaults to 4096):
            Dimension of the hidden representations.
        intermediate_size (`int`, *optional*, defaults to 11008):
            Dimension of the MLP representations.
        num_hidden_layers (`int`, *optional*, defaults to 32):
            Number of hidden layers in the Transformer encoder.
        num_attention_heads (`int`, *optional*, defaults to 32):
            Number of attention heads for each attention layer in the Transformer encoder.
        hidden_act (`str` or `function`, *optional*, defaults to `"silu"`):
            The non-linear activation function (function or string) in the decoder.
        initializer_range (`float`, *optional*, defaults to 0.02):
            The standard deviation of the truncated_normal_initializer for initializing all weight matrices.
        rms_norm_eps (`float`, *optional*, defaults to 1e-12):
            The epsilon used by the rms normalization layers.
        use_cache (`bool`, *optional*, defaults to `True`):
            Whether or not the model should return the last key/values attentions (not used by all models). Only
            relevant if `config.is_decoder=True`.
        tie_word_embeddings(`bool`, *optional*, defaults to `False`):
            Whether to tie weight embeddings
        Example:

    ```python
    >>> from transformers import IdeficsModel, IdeficsConfig

    >>> # Initializing a Idefics idefics-9b style configuration
    >>> configuration = IdeficsConfig()

    >>> # Initializing a model from the idefics-9b style configuration
    >>> model = IdeficsModel(configuration)

    >>> # Accessing the model configuration
    >>> configuration = model.config
    ```"""
    model_type = "idefics"

    def __init__(
        self,
        vocab_size=32000,
        additional_vocab_size=0,
        hidden_size=4096,
        intermediate_size=11008,
        num_hidden_layers=32,
        num_attention_heads=32,
        dropout=0.0,
        hidden_act="silu",
        initializer_range=0.02,
        alpha_initializer="ones",
        alphas_initializer_range=0.0,
        alpha_type="vector",
        rms_norm_eps=1e-6,
        use_cache=True,
        pad_token_id=0,
        bos_token_id=1,
        eos_token_id=2,
        tie_word_embeddings=False,
        cross_layer_interval=1,
        qk_layer_norms=False,
        freeze_text_layers=True,
        freeze_text_module_exceptions=[],
        freeze_lm_head=False,
        freeze_vision_layers=True,
        freeze_vision_module_exceptions=[],
        vision_model_params="{}",
        vision_config=None,
        vision_model_name="google/vit-base-patch16-224",
        vision_embed_dim=768,
        vision_image_size=224,
        vision_intermediate_size=5120,
        vision_patch_size=14,
        use_resampler=False,
        resampler_n_latents=64,
        resampler_depth=6,
        resampler_n_heads=16,
        resampler_head_dim=96,
        **kwargs,
    ):
        self.vocab_size = vocab_size
        self.additional_vocab_size = additional_vocab_size
        self.hidden_size = hidden_size
        self.intermediate_size = intermediate_size
        self.num_hidden_layers = num_hidden_layers
        self.num_attention_heads = num_attention_heads
        self.dropout = dropout
        self.hidden_act = hidden_act
        self.initializer_range = initializer_range
        self.alpha_initializer = alpha_initializer
        self.alphas_initializer_range = alphas_initializer_range
        self.alpha_type = alpha_type
        self.rms_norm_eps = rms_norm_eps
        self.use_cache = use_cache
        self.vision_model_params = vision_model_params
        super().__init__(
            pad_token_id=pad_token_id,
            bos_token_id=bos_token_id,
            eos_token_id=eos_token_id,
            tie_word_embeddings=tie_word_embeddings,
            **kwargs,
        )

        self.cross_layer_interval = cross_layer_interval
        self.qk_layer_norms = qk_layer_norms
        self.freeze_vision_layers = freeze_vision_layers
        self.vision_model_name = vision_model_name

        self.freeze_text_layers = freeze_text_layers
        self.freeze_text_module_exceptions = freeze_text_module_exceptions
        self.freeze_vision_module_exceptions = freeze_vision_module_exceptions
        self.freeze_lm_head = freeze_lm_head

        self.vision_embed_dim = vision_embed_dim
        self.vision_image_size = vision_image_size
        self.vision_intermediate_size = vision_intermediate_size
        self.vision_patch_size = vision_patch_size

        if vision_config is None:
            self.vision_config = {}
            self.vision_config["hidden_size"] = vision_embed_dim
            self.vision_config["image_size"] = vision_image_size
            self.vision_config["num_attention_heads"] = num_attention_heads
            self.vision_config["num_hidden_layers"] = num_hidden_layers
            self.vision_config["intermediate_size"] = vision_intermediate_size
            self.vision_config["patch_size"] = vision_patch_size
        elif not isinstance(vision_config, dict):
            raise ValueError("vision_config must be a dict")
        else:
            self.vision_config = vision_config

        # Resampler params
        self.use_resampler = use_resampler
        self.resampler_n_latents = resampler_n_latents
        self.resampler_depth = resampler_depth
        self.resampler_n_heads = resampler_n_heads
        self.resampler_head_dim = resampler_head_dim

        # IMPORTANT: Do not do any __init__ args-based checks in the constructor, since
        # PretrainedConfig.from_dict first instantiates the class with the config dict and only then
        # updates the config object with `kwargs` from from_pretrained, so during the instantiation
        # of this object many attributes have default values and haven't yet been overridden.
        # Do any required checks inside `from_pretrained` once the superclass' `from_pretrained` was run.

    def check_compatibilities(self):
        vision_model_params = eval(self.vision_model_params)
        config = AutoConfig.from_pretrained(self.vision_model_name, **vision_model_params)
        if hasattr(config, "vision_config"):
            vision_config = config.vision_config
        else:
            vision_config = config
        vision_embed_dim = vision_config.hidden_size
        if self.vision_embed_dim != vision_embed_dim:
            raise ValueError(
                f"vision_embed_dim ({self.vision_embed_dim}) must match the hidden size of the vision model"
                f" ({vision_embed_dim})"
            )
        vision_image_size = vision_config.image_size
        if self.vision_image_size != vision_image_size:
            raise ValueError(
                f"vision_image_size ({self.vision_image_size}) must match the hidden size of the vision model"
                f" ({vision_image_size})"
            )

    @classmethod
    def from_pretrained(cls, pretrained_model_name_or_path: Union[str, os.PathLike], **kwargs) -> "PretrainedConfig":
        outputs = super(IdeficsConfig, cls).from_pretrained(pretrained_model_name_or_path, **kwargs)
        # if isinstance(outputs, Tuple):
        #     # When called with return_unused_kwargs=True, the first item will be the config
        #     outputs[0].check_compatibilities()
        # else:
        #     outputs.check_compatibilities()
        return outputs
