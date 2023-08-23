# coding=utf-8
# Copyright 2022 ylacombe and The HuggingFace Inc. team. All rights reserved.
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
""" SeamlessM4T model configuration """

from ...configuration_utils import PretrainedConfig
from ...utils import logging


logger = logging.get_logger(__name__)

SEAMLESS_M4T_PRETRAINED_CONFIG_ARCHIVE_MAP = {
    "meta-private/m4t_large": "https://huggingface.co/meta-private/m4t_large/resolve/main/config.json",
    # See all SeamlessM4T models at https://huggingface.co/models?filter=seamless_m4t
}


# TODO: docstrings is a mix of wav2vec2_conformer, mBart, nllb
class SeamlessM4TConfig(PretrainedConfig):
    r"""
    This is the configuration class to store the configuration of a [`~SeamlessM4TModel`].
    It is used to instantiate an SeamlessM4T model according to the specified arguments, defining the model
    architecture. Instantiating a configuration with the defaults will yield a similar configuration to that of
    the SeamlessM4T [meta-private/m4t_large](https://huggingface.co/meta-private/m4t_large) architecture.

    Configuration objects inherit from  [`PretrainedConfig`] and can be used
    to control the model outputs. Read the documentation from  [`PretrainedConfig`]
    for more information.


    Args:
        vocab_size (`int`, *optional*, defaults to 30522):
            Vocabulary size of the SeamlessM4T model. Defines the number of different tokens that can be represented by the
            `inputs_ids` passed when calling [`~SeamlessM4TModel`] or
            [`~TFSeamlessM4TModel`].
        hidden_size (`int`, *optional*, defaults to 768):
            Dimension of the encoder layers and the pooler layer.
        num_hidden_layers (`int`, *optional*, defaults to 12):
            Number of hidden layers in the Transformer encoder.
        num_attention_heads (`int`, *optional*, defaults to 12):
            Number of attention heads for each attention layer in the Transformer encoder.
        intermediate_size (`int`, *optional*, defaults to 3072):
            Dimension of the "intermediate" (i.e., feed-forward) layer in the Transformer encoder.
        hidden_act (`str` or `function`, *optional*, defaults to `"gelu"`):
            The non-linear activation function (function or string) in the encoder and pooler.
            If string, `"gelu"`, `"relu"`, `"selu"` and `"gelu_new"` are supported.
        hidden_dropout_prob (`float`, *optional*, defaults to 0.1):
            The dropout probabilitiy for all fully connected layers in the embeddings, encoder, and pooler.
        attention_probs_dropout_prob (`float`, *optional*, defaults to 0.1):
            The dropout ratio for the attention probabilities.
        max_position_embeddings (`int`, *optional*, defaults to 512):
            The maximum sequence length that this model might ever be used with.
            Typically set this to something large just in case (e.g., 512 or 1024 or 2048).
        type_vocab_size (`int`, *optional*, defaults to 2):
            The vocabulary size of the `token_type_ids` passed when calling [`~SeamlessM4TModel`] or
            [`~TFSeamlessM4TModel`].
        initializer_range (`float`, *optional*, defaults to 0.02):
            The standard deviation of the truncated_normal_initializer for initializing all weight matrices.
        layer_norm_eps (`float`, *optional*, defaults to 1e-12):
            The epsilon used by the layer normalization layers.
        use_cache (`bool`, *optional*, defaults to `True`):
            Whether or not the model should return the last key/values attentions (not used by all models). Only
            relevant if `config.is_decoder=True`.
        Example:

    ```python
    >>> from transformers import SeamlessM4TModel, SeamlessM4TConfig

    >>> # Initializing a SeamlessM4T meta-private/m4t_large style configuration
    >>> configuration = SeamlessM4TConfig()

    >>> # Initializing a model from the meta-private/m4t_large style configuration
    >>> model = SeamlessM4TModel(configuration)

    >>> # Accessing the model configuration
    >>> configuration = model.config
    ```"""
    model_type = "seamless_m4t"

    def __init__(
        self,
        vocab_size=256102,
        unit_vocab_size=10082,
        # overall_config
        hidden_size=1024,  # works for speech encoder
        use_text_encoder=True,
        use_speech_encoder=True,
        num_hidden_layers=24,  # works for speech encoder
        num_attention_heads=16,  # works for speech encoder
        intermediate_size=4096,
        initializer_range=0.02,
        layer_norm_eps=1e-5,
        max_position_embeddings=2048,
        use_cache=True,
        is_encoder_decoder=True,
        # text|unit encoder|decoder
        encoder_layers=24,
        encoder_ffn_dim=8192,
        encoder_attention_heads=16,
        decoder_layers=24,
        decoder_ffn_dim=8192,
        decoder_attention_heads=16,
        encoder_layerdrop=0.05,
        decoder_layerdrop=0.05,
        activation_function="relu",
        dropout=0.1,
        attention_dropout=0.1,
        activation_dropout=0.0,
        init_std=0.02,
        decoder_start_token_id=2,
        scale_embedding=True,
        # speech_encoder
        speech_encoder_hidden_act="swish",
        speech_encoder_dropout=0.0,
        add_adapter=True,
        layerdrop=0.1,
        conv_dim=(512, 512, 512, 512, 512, 512, 160),
        conv_stride=(5, 2, 2, 2, 2, 2, 2),
        conv_kernel=(10, 3, 3, 3, 3, 2, 2),
        conv_bias=False,
        num_conv_pos_embeddings=128,
        num_conv_pos_embedding_groups=16,
        adaptor_kernel_size=8,
        adaptor_stride=8,
        adaptor_layer_norm=True,
        adaptor_dropout=0.1,
        num_adapter_layers=1,
        output_hidden_size=None,
        position_embeddings_type="relative",
        rotary_embedding_base=10000,
        max_source_positions=4096,  # works
        conv_depthwise_kernel_size=31,
        conformer_conv_dropout=0.1,
        # t2u config
        unit_pad_token_id=1,
        t2u_encoder_layers=6,  # works
        t2u_encoder_ffn_dim=8192,  # works
        t2u_encoder_attention_heads=16,  # works
        t2u_decoder_layers=6,  # works
        t2u_decoder_ffn_dim=8192,  # works
        t2u_decoder_attention_heads=16,  # works
        hidden_act="gelu",
        attention_probs_dropout_prob=0.1,
        pad_token_id=0,
        bos_token_id=2,
        eos_token_id=3,
        # unk_token_id=1, TODO
        **kwargs,
    ):
        # overall_config
        self.vocab_size = vocab_size
        self.unit_vocab_size = unit_vocab_size
        self.hidden_size = hidden_size
        self.use_text_encoder = use_text_encoder
        self.use_speech_encoder = use_speech_encoder
        self.num_hidden_layers = num_hidden_layers
        self.num_attention_heads = num_attention_heads
        self.intermediate_size = intermediate_size
        self.initializer_range = initializer_range
        self.layer_norm_eps = layer_norm_eps
        self.max_position_embeddings = max_position_embeddings
        self.use_cache = use_cache
        self.layerdrop = layerdrop

        # text|unit encoder|decoder
        self.encoder_layers = encoder_layers
        self.encoder_ffn_dim = encoder_ffn_dim
        self.encoder_attention_heads = encoder_attention_heads
        self.decoder_layers = decoder_layers
        self.decoder_ffn_dim = decoder_ffn_dim
        self.decoder_attention_heads = decoder_attention_heads
        self.encoder_layerdrop = encoder_layerdrop
        self.decoder_layerdrop = decoder_layerdrop
        self.activation_function = activation_function
        self.dropout = dropout
        self.attention_dropout = attention_dropout
        self.activation_dropout = activation_dropout
        self.init_std = init_std
        self.scale_embedding = scale_embedding

        # speech_encoder
        self.speech_encoder_hidden_act = speech_encoder_hidden_act
        self.speech_encoder_dropout = speech_encoder_dropout
        self.conv_dim = conv_dim
        self.conv_stride = conv_stride
        self.conv_kernel = conv_kernel
        self.conv_bias = conv_bias
        self.num_conv_pos_embeddings = num_conv_pos_embeddings
        self.num_conv_pos_embedding_groups = num_conv_pos_embedding_groups
        self.adaptor_kernel_size = adaptor_kernel_size
        self.adaptor_stride = adaptor_stride
        self.adaptor_layer_norm = adaptor_layer_norm
        self.adaptor_dropout = adaptor_dropout
        self.num_adapter_layers = num_adapter_layers
        self.output_hidden_size = output_hidden_size
        self.position_embeddings_type = position_embeddings_type
        self.rotary_embedding_base = rotary_embedding_base
        self.max_source_positions = max_source_positions
        self.conv_depthwise_kernel_size = conv_depthwise_kernel_size
        self.add_adapter = add_adapter

        # t2u config
        self.unit_pad_token_id = unit_pad_token_id
        self.hidden_act = hidden_act
        # self.type_vocab_size = type_vocab_size
        self.t2u_encoder_layers = t2u_encoder_layers
        self.t2u_encoder_ffn_dim = t2u_encoder_ffn_dim
        self.t2u_encoder_attention_heads = t2u_encoder_attention_heads
        self.t2u_decoder_layers = t2u_decoder_layers
        self.t2u_decoder_ffn_dim = t2u_decoder_ffn_dim
        self.t2u_decoder_attention_heads = t2u_decoder_attention_heads

        super().__init__(
            pad_token_id=pad_token_id,
            bos_token_id=bos_token_id,
            eos_token_id=eos_token_id,
            decoder_start_token_id=decoder_start_token_id,
            is_encoder_decoder=is_encoder_decoder,
            **kwargs,
        )
