# coding=utf-8
# Copyright 2023 The OpenAI Team Authors and HuggingFace Inc. team.
# Copyright (c) 2018, NVIDIA CORPORATION.  All rights reserved.
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
""" MAMBA configuration"""
import math

from ...configuration_utils import PretrainedConfig
from ...utils import logging


logger = logging.get_logger(__name__)

MAMBA_PRETRAINED_CONFIG_ARCHIVE_MAP = {
    "state-spaces/mamba-2.8b": "https://huggingface.co/state-spaces/mamba-2.8b/resolve/main/config.json",
}



class MambaConfig(PretrainedConfig):
    """
    This is the configuration class to store the configuration of a [`MambaModel`]. It is used to instantiate a MAMBA
    model according to the specified arguments, defining the model architecture. Instantiating a configuration with the
    defaults will yield a similar configuration to that of the RWVK-4
    [state-spaces/mamba-2.8b](https://huggingface.co/state-spaces/mamba-2.8b) architecture.

    Configuration objects inherit from [`PretrainedConfig`] and can be used to control the model outputs. Read the
    documentation from [`PretrainedConfig`] for more information.


    Args:
        vocab_size (`int`, *optional*, defaults to 50277):
            Vocabulary size of the MAMBA model. Defines the number of different tokens that can be represented by the
            `inputs_ids` passed when calling [`MambaModel`].
        context_length (`int`, *optional*, defaults to 1024):
            The maximum sequence length that this model can be be used with in a single forward (using it in RNN mode
            lets use any sequence length).
        hidden_size (`int`, *optional*, defaults to 4096):
            Dimensionality of the embeddings and hidden states.
        num_hidden_layers (`int`, *optional*, defaults to 32):
            Number of hidden layers in the model.
        attention_hidden_size (`int`, *optional*):
            Dimensionality of the attention hidden states. Will default to `hidden_size` if unset.
        intermediate_size (`int`, *optional*):
            Dimensionality of the inner feed-forward layers. Will default to 4 times `hidden_size` if unset.
        layer_norm_epsilon (`float`, *optional*, defaults to 1e-05):
            The epsilon to use in the layer normalization layers.
        bos_token_id (`int`, *optional*, defaults to 0):
            The id of the beginning of sentence token in the vocabulary. Defaults to 0 as MAMBA uses the same tokenizer
            as GPTNeoX.
        eos_token_id (`int`, *optional*, defaults to 0):
            The id of the end of sentence token in the vocabulary. Defaults to 0 as MAMBA uses the same tokenizer as
            GPTNeoX.
        rescale_every (`int`, *optional*, defaults to 6):
            At inference, the hidden states (and weights of the correponding output layers) are divided by 2 every
            `rescale_every` layer. If set to 0 or a negative number, no rescale is done.
        tie_word_embeddings (`bool`, *optional*, defaults to `True`):
            Whether or not to tie the word embeddings with the input token embeddings.
        use_cache (`bool`, *optional*, defaults to `True`):
            Whether or not the model should return the last state.


    Example:

    ```python
    >>> from transformers import MambaConfig, MambaModel

    >>> # Initializing a Mamba configuration
    >>> configuration = MambaConfig()

    >>> # Initializing a model (with random weights) from the configuration
    >>> model = MambaModel(configuration)

    >>> # Accessing the model configuration
    >>> configuration = model.config
    ```"""

    model_type = "mamba"
    attribute_map = {"max_position_embeddings": "context_length"}

    def __init__(
        self,
        vocab_size=50280,
        hidden_size=768,
        state_size=16,
        num_hidden_layers=32,
        layer_norm_epsilon=1e-5,
        pad_token_id=0,
        bos_token_id=1,
        eos_token_id=2,
        expand=2,
        dt_rank="auto",
        tie_word_embeddings=True,
        use_bias=False,
        use_conv_bias=True,
        hidden_act="silu",
        initializer_range=0.1,
        **kwargs,
    ):
        self.vocab_size = vocab_size
        self.hidden_size = hidden_size
        self.state_size = state_size
        self.num_hidden_layers = num_hidden_layers
        self.layer_norm_epsilon = layer_norm_epsilon
        self.d_inner = hidden_size * 2
        self.conv_kernel = 4
        self.state_size = state_size
        self.expand = expand
        self.time_step_rank = math.ceil(self.hidden_size / 16) if dt_rank == "auto" else dt_rank
        self.bos_token_id = bos_token_id
        self.eos_token_id = eos_token_id
        self.pad_token_id = pad_token_id
        self.use_bias = use_bias
        self.use_conv_bias = use_conv_bias
        self.hidden_act=hidden_act
        self.initializer_range = initializer_range

        super().__init__(
            tie_word_embeddings=tie_word_embeddings, bos_token_id=bos_token_id, eos_token_id=eos_token_id, **kwargs
        )
