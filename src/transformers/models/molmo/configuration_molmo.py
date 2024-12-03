#                🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨
#           This file was automatically generated from src/transformers/models/molmo/modular_molmo.py.
#               Do NOT edit this file manually as any edits will be overwritten by the generation of
#             the file from the modular. If any change should be done, please apply the change to the
#                          modular_molmo.py file directly. One of our CI enforces this.
#                🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨
# coding=utf-8
# Copyright 2024 HuggingFace Inc. team. All rights reserved.
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

from ...configuration_utils import PretrainedConfig
from ...modeling_rope_utils import rope_config_validation
from ...utils import logging


logger = logging.get_logger(__name__)


class MolmoVisionConfig(PretrainedConfig):
    r"""
    This is the configuration class to store the configuration of a [`MolmoVisionModel`]. It is used to instantiate a
    `MolmoVisionModel` according to the specified arguments, defining the model architecture. Instantiating a
    configuration with the defaults will yield a similar configuration to that of the vision encoder of the Molmo
    [allenai/Molmo-7B-D-0924-hf](https://huggingface.co/allenai/Molmo-7B-D-0924-hf) architecture.

    Configuration objects inherit from [`PretrainedConfig`] and can be used to control the model outputs. Read the
    documentation from [`PretrainedConfig`] for more information.

    Args:
        hidden_size (`int`, *optional*, defaults to 768):
            Dimensionality of the encoder layers and the pooler layer.
        intermediate_size (`int`, *optional*, defaults to 3072):
            Dimensionality of the "intermediate" (i.e., feed-forward) layer in the Transformer encoder.
        num_hidden_layers (`int`, *optional*, defaults to 12):
            Number of hidden layers in the Transformer encoder.
        num_attention_heads (`int`, *optional*, defaults to 12):
            Number of attention heads for each attention layer in the Transformer encoder.
        image_size (`int`, *optional*, defaults to 224):
            The size (resolution) of each image.
        patch_size (`int`, *optional*, defaults to 32):
            The size (resolution) of each patch.
        hidden_act (`str` or `function`, *optional*, defaults to `"quick_gelu"`):
            The non-linear activation function (function or string) in the encoder and pooler. If string, `"gelu"`,
            `"relu"`, `"selu"` and `"gelu_new"` `"quick_gelu"` are supported.
        layer_norm_eps (`float`, *optional*, defaults to 1e-05):
            The epsilon used by the layer normalization layers.
        attention_dropout (`float`, *optional*, defaults to 0.0):
            The dropout ratio for the attention probabilities.
        initializer_range (`float`, *optional*, defaults to 0.02):
            The standard deviation of the truncated_normal_initializer for initializing all weight matrices.
    Example:

    ```python
    >>> from transformers import MolmoVisionConfig, MolmoVisionModel

    >>> # Initializing a MolmoVisionConfig with allenai/Molmo-7B-D-0924-hf style configuration
    >>> configuration = MolmoVisionConfig()

    >>> # Initializing a MolmoVisionModel (with random weights) from the allenai/Molmo-7B-D-0924-hf style configuration
    >>> model = MolmoVisionModel(configuration)

    >>> # Accessing the model configuration
    >>> configuration = model.config
    ```"""

    model_type = "molmo_vision_model"
    base_config_key = "vision_config"

    def __init__(
        self,
        hidden_size=1024,
        intermediate_size=4096,
        projection_dim=512,
        num_hidden_layers=23,
        num_attention_heads=16,
        num_channels=3,
        image_size=576,
        patch_size=14,
        hidden_act="quick_gelu",
        layer_norm_eps=1e-5,
        attention_dropout=0.0,
        initializer_range=0.02,
        initializer_factor=1.0,
        num_image_positions=577,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.hidden_size = hidden_size
        self.intermediate_size = intermediate_size
        self.projection_dim = projection_dim
        self.num_hidden_layers = num_hidden_layers
        self.num_attention_heads = num_attention_heads
        self.num_channels = num_channels
        self.patch_size = patch_size
        self.image_size = image_size
        self.initializer_range = initializer_range
        self.initializer_factor = initializer_factor
        self.attention_dropout = attention_dropout
        self.layer_norm_eps = layer_norm_eps
        self.hidden_act = hidden_act
        self.num_image_positions = num_image_positions


class MolmoPoolingConfig(PretrainedConfig):
    r"""
    This is the configuration class to store the configuration of a [`MolmoAdapterModel`]. It is used to instantiate an
    `MolmoAdapterModel` according to the specified arguments, defining the model architecture. Instantiating a configuration
    with the defaults will yield a similar configuration to that of the Molmo-7B-D.

    e.g. [allenai/Molmo-7B-D-0924-hf](https://huggingface.co/allenai/Molmo-7B-D-0924-hf)

    Configuration objects inherit from [`PretrainedConfig`] and can be used to control the model outputs. Read the
    documentation from [`PretrainedConfig`] for more information.

    Args:
        hidden_size (`int`, *optional*, defaults to 768):
            Dimensionality of the pooler attention layer.
        text_hidden_size (`int`, *optional*, defaults to 768):
            Dimensionality of the text encoder layers.
        text_intermediate_size (`int`, *optional*, defaults to 3072):
            Dimensionality of the "intermediate" (i.e., feed-forward) layer in the text Transformer encoder.
        num_attention_heads (`int`, *optional*, defaults to 12):
            Number of attention heads for each attention layer in the Transformer pooler.
        head_dim (`int`, *optional*, defaults to 64):
            The poolinng attention head dimension.
        projector_hidden_act (`str`, *optional*, defaults to `"gelu"`):
            The activation function used by the multimodal projector.
        pooling_height (`int`, *optional*, defaults to 2):
            The height of image features requred for pooling operation.
        pooling_width (`int`, *optional*, defaults to 2):
            The width of image features requred for pooling operation.
        pad_embed_dim (`int`, *optional*, defaults to 2048):
            Dimensionality of a padding tensor which is multiplied with the image mask.
        image_num_patches (`int`, *optional*, defaults to 24):
            Number of patches each image feature has after the vision tower.
        image_feature_dropout (`float`, *optional*, defaults to 0.9):
            The dropout ratio for the image features after vision tower.
        image_pooling_type (`str`, *optional*, defaults to `"attention_meanq"`):
            Type of pooling to apply on image features. Can be one of ["attention", "attention_meanq", "attention_2wide", "attention_v2", "stack"] or `None`
        image_padding_embed (`str`, *optional*, defaults to `"pad_and_partial_pad"`):
            Type of padding to apply of image masks. Can be one of ["pad_embed", "regress", "pad_and_partial_pad]
        attention_dropout (`float`, *optional*, defaults to 0.0):
            The dropout ratio for the attention probabilities.
        initializer_range (`float`, *optional*, defaults to 0.02):
            The standard deviation of the truncated_normal_initializer for initializing all weight matrices.

    Example:

    ```python
    >>> from transformers import MolmoAdapterModel, MolmoPoolingConfig

    >>> # Initializing a Molmo-pooling config
    >>> pooling_config = MolmoPoolingConfig()

    >>> # Initializing a adapter model from the allenai/Molmo-7B-D-0924-hf style configuration
    >>> model = MolmoAdapterModel(pooling_config)

    >>> # Accessing the model configuration
    >>> configuration = model.config
    ```"""

    def __init__(
        self,
        hidden_size=2048,
        num_attention_heads=16,
        head_dim=64,
        attention_dropout=0.0,
        initializer_range=0.02,
        pooling_height=2,
        pooling_width=2,
        pad_embed_dim=2048,
        image_num_patches=24,
        image_feature_dropout=0.0,
        text_intermediate_size=37888,
        text_hidden_size=3584,
        image_pooling_type="attention_meanq",
        image_padding_embed="pad_and_partial_pad",
        projector_hidden_act="silu",
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.hidden_size = hidden_size
        self.num_attention_heads = num_attention_heads
        self.head_dim = head_dim
        self.pooling_height = pooling_height
        self.pooling_width = pooling_width
        self.initializer_range = initializer_range
        self.attention_dropout = attention_dropout
        self.pad_embed_dim = pad_embed_dim
        self.image_num_patches = image_num_patches
        self.image_feature_dropout = image_feature_dropout
        self.text_intermediate_size = text_intermediate_size
        self.text_hidden_size = text_hidden_size
        self.image_pooling_type = image_pooling_type
        self.image_padding_embed = image_padding_embed
        self.projector_hidden_act = projector_hidden_act


class MolmoTextConfig(PretrainedConfig):
    r"""
    This is the configuration class to store the configuration of a [`MolmoModel`]. It is used to instantiate a
    Molmo model according to the specified arguments, defining the model architecture. Instantiating a configuration
    with the defaults will yield a similar configuration to that of
    Molmo-7B-beta [Qwen/Molmo-7B-beta](https://huggingface.co/Qwen/Molmo-7B-beta).

    Configuration objects inherit from [`PretrainedConfig`] and can be used to control the model outputs. Read the
    documentation from [`PretrainedConfig`] for more information.


    Args:
        vocab_size (`int`, *optional*, defaults to 152192):
            Vocabulary size of the Molmo model. Defines the number of different tokens that can be represented by the
            `inputs_ids` passed when calling [`MolmoTextModel`]
        hidden_size (`int`, *optional*, defaults to 3584):
            Dimension of the hidden representations.
        intermediate_size (`int`, *optional*, defaults to 37888):
            Dimension of the MLP representations.
        num_hidden_layers (`int`, *optional*, defaults to 28):
            Number of hidden layers in the Transformer encoder.
        head_dim (`int`, *optional*, defaults to 128):
            The poolinng attention head dimension.
        num_attention_heads (`int`, *optional*, defaults to 28):
            Number of attention heads for each attention layer in the Transformer encoder.
        num_key_value_heads (`int`, *optional*, defaults to 4):
            This is the number of key_value heads that should be used to implement Grouped Query Attention. If
            `num_key_value_heads=num_attention_heads`, the model will use Multi Head Attention (MHA), if
            `num_key_value_heads=1` the model will use Multi Query Attention (MQA) otherwise GQA is used. When
            converting a multi-head checkpoint to a GQA checkpoint, each group key and value head should be constructed
            by meanpooling all the original heads within that group. For more details checkout [this
            paper](https://arxiv.org/pdf/2305.13245.pdf). If it is not specified, will default to `32`.
        hidden_act (`str` or `function`, *optional*, defaults to `"swiglu"`):
            The non-linear activation function (function or string) in the decoder.
        max_position_embeddings (`int`, *optional*, defaults to 4096):
            The maximum sequence length that this model might ever be used with.
        initializer_range (`float`, *optional*, defaults to 0.02):
            The standard deviation of the truncated_normal_initializer for initializing all weight matrices.
        rms_norm_eps (`float`, *optional*, defaults to 1e-06):
            The epsilon used by the rms normalization layers.
        use_cache (`bool`, *optional*, defaults to `True`):
            Whether or not the model should return the last key/values attentions (not used by all models). Only
            relevant if `config.is_decoder=True`.
        tie_word_embeddings (`bool`, *optional*, defaults to `False`):
            Whether the model's input and output word embeddings should be tied.
        rope_theta (`float`, *optional*, defaults to 1000000.0):
            The base period of the RoPE embeddings.
        rope_scaling (`Dict`, *optional*):
            Dictionary containing the scaling configuration for the RoPE embeddings. NOTE: if you apply new rope type
            and you expect the model to work on longer `max_position_embeddings`, we recommend you to update this value
            accordingly.
            Expected contents:
                `rope_type` (`str`):
                    The sub-variant of RoPE to use. Can be one of ['default', 'linear', 'dynamic', 'yarn', 'longrope',
                    'llama3'], with 'default' being the original RoPE implementation.
                `factor` (`float`, *optional*):
                    Used with all rope types except 'default'. The scaling factor to apply to the RoPE embeddings. In
                    most scaling types, a `factor` of x will enable the model to handle sequences of length x *
                    original maximum pre-trained length.
                `original_max_position_embeddings` (`int`, *optional*):
                    Used with 'dynamic', 'longrope' and 'llama3'. The original max position embeddings used during
                    pretraining.
                `attention_factor` (`float`, *optional*):
                    Used with 'yarn' and 'longrope'. The scaling factor to be applied on the attention
                    computation. If unspecified, it defaults to value recommended by the implementation, using the
                    `factor` field to infer the suggested value.
                `beta_fast` (`float`, *optional*):
                    Only used with 'yarn'. Parameter to set the boundary for extrapolation (only) in the linear
                    ramp function. If unspecified, it defaults to 32.
                `beta_slow` (`float`, *optional*):
                    Only used with 'yarn'. Parameter to set the boundary for interpolation (only) in the linear
                    ramp function. If unspecified, it defaults to 1.
                `short_factor` (`List[float]`, *optional*):
                    Only used with 'longrope'. The scaling factor to be applied to short contexts (<
                    `original_max_position_embeddings`). Must be a list of numbers with the same length as the hidden
                    size divided by the number of attention heads divided by 2
                `long_factor` (`List[float]`, *optional*):
                    Only used with 'longrope'. The scaling factor to be applied to long contexts (<
                    `original_max_position_embeddings`). Must be a list of numbers with the same length as the hidden
                    size divided by the number of attention heads divided by 2
                `low_freq_factor` (`float`, *optional*):
                    Only used with 'llama3'. Scaling factor applied to low frequency components of the RoPE
                `high_freq_factor` (`float`, *optional*):
                    Only used with 'llama3'. Scaling factor applied to high frequency components of the RoPE
        use_sliding_window (`bool`, *optional*, defaults to `False`):
            Whether to use sliding window attention.
        sliding_window (`int`, *optional*, defaults to 4096):
            Sliding window attention (SWA) window size. If not specified, will default to `4096`.
        max_window_layers (`int`, *optional*, defaults to 28):
            The number of layers that use SWA (Sliding Window Attention). The bottom layers use SWA while the top use full attention.
        attention_dropout (`float`, *optional*, defaults to 0.0):
            The dropout ratio for the attention probabilities.
        attention_bias (`bool`, *optional*, defaults to `False`):
            Whether to use a bias in the query, key, value and output projection layers during self-attention.
        use_qk_norm (`bool), *optional*, defaults to `False`):
            Whther to apply layer norm to keys and queries in attention module.
        use_postnorm (`bool), *optional*, defaults to `True`):
            Whther to apply pre or post layer normalization in each decoder layer.
        use_attention_layer_norm (`bool`, *optional*, defaults to `False`):
            Whether to apply norm to keys and queries in the attention layer.

    ```python
    >>> from transformers import MolmoTextModel, MolmoTextConfig

    >>> # Initializing a Molmo style configuration
    >>> configuration = MolmoTextConfig()

    >>> # Initializing a model from the Molmo-7B style configuration
    >>> model = MolmoTextModel(configuration)

    >>> # Accessing the model configuration
    >>> configuration = model.config
    ```"""

    model_type = "molmo_text"
    keys_to_ignore_at_inference = ["past_key_values"]

    def __init__(
        self,
        hidden_size=3584,
        num_key_value_heads=4,
        num_attention_heads=28,
        num_hidden_layers=28,
        head_dim=128,
        vocab_size=152192,
        intermediate_size=37888,
        hidden_act="swiglu",
        max_position_embeddings=4096,
        initializer_range=0.02,
        rms_norm_eps=1e-6,
        use_cache=True,
        tie_word_embeddings=False,
        rope_theta=1000000.0,
        rope_scaling=None,
        use_sliding_window=False,
        sliding_window=4096,
        max_window_layers=28,
        attention_dropout=0.0,
        attention_bias=False,
        use_qk_norm=False,
        use_postnorm=True,
        use_attention_layer_norm=False,
        **kwargs,
    ):
        super().__init__(
            tie_word_embeddings=tie_word_embeddings,
            **kwargs,
        )
        self.head_dim = head_dim
        self.attention_bias = attention_bias
        self.use_qk_norm = use_qk_norm
        self.use_postnorm = use_postnorm
        self.use_attention_layer_norm = use_attention_layer_norm
        self.vocab_size = vocab_size
        self.max_position_embeddings = max_position_embeddings
        self.hidden_size = hidden_size
        self.intermediate_size = intermediate_size
        self.num_hidden_layers = num_hidden_layers
        self.num_attention_heads = num_attention_heads
        self.use_sliding_window = use_sliding_window
        self.sliding_window = sliding_window if use_sliding_window else None
        self.max_window_layers = max_window_layers

        # for backward compatibility
        if num_key_value_heads is None:
            num_key_value_heads = num_attention_heads

        self.num_key_value_heads = num_key_value_heads
        self.hidden_act = hidden_act
        self.initializer_range = initializer_range
        self.rms_norm_eps = rms_norm_eps
        self.use_cache = use_cache
        self.rope_theta = rope_theta
        self.rope_scaling = rope_scaling
        self.attention_dropout = attention_dropout
        # Validate the correctness of rotary position embeddings parameters
        # BC: if there is a 'type' field, move it to 'rope_type'.
        if self.rope_scaling is not None and "type" in self.rope_scaling:
            self.rope_scaling["rope_type"] = self.rope_scaling["type"]
        rope_config_validation(self)


class MolmoConfig(PretrainedConfig):
    r"""
    This is the configuration class to store the configuration of a [`MolmoForConditionalGeneration`]. It is used to instantiate an
    Llava model according to the specified arguments, defining the model architecture. Instantiating a configuration
    with the defaults will yield a similar configuration to that of the Molmo-7B-D.

    e.g. [allenai/Molmo-7B-D-0924-hf](https://huggingface.co/allenai/Molmo-7B-D-0924-hf)

    Configuration objects inherit from [`PretrainedConfig`] and can be used to control the model outputs. Read the
    documentation from [`PretrainedConfig`] for more information.

    Args:
        vision_config (`Union[AutoConfig, dict]`,  *optional*, defaults to `MolmoVisionConfig`):
            The config object or dictionary of the vision backbone.
        text_config (`Union[AutoConfig, dict]`, *optional*, defaults to `MolmoTextConfig`):
            The config object or dictionary of the text backbone.
        pooling_config (`Union[AutoConfig, dict]`, *optional*, defaults to `MolmoPoolingConfig`):
            The config object or dictionary of the adapter backbone.
        image_token_index (`int`, *optional*, defaults to 152069):
            The image token index to encode the image prompt.
        image_seq_length (`int`, *optional*, defaults to 576):
            Sequence length of one image embedding.
        initializer_range (`float`, *optional*, defaults to 0.02):
            The standard deviation of the truncated_normal_initializer for initializing all weight matrices.
        vision_feature_select_strategy (`str`, *optional*, defaults to `"default"`):
            The feature selection strategy used to select the vision feature from the vision backbone.
            Can be one of `"default"` or `"full"`.
        vision_feature_layers (`List[int]`, *optional*, defaults to `(-2, -9)`):
            The indices of the layers to select the vision feature.

    Example:

    ```python
    >>> from transformers import MolmoForConditionalGeneration, MolmoConfig, MolmoVisionConfig, MolmoTextConfig, MolmoPoolingConfig

    >>> # Initializing a Molmo-vision config
    >>> vision_config = MolmoVisionConfig()

    >>> # Initializing a Molmo-text config
    >>> text_config = MolmoTextConfig()

    >>> # Initializing a Molmo-pooling config
    >>> pooling_config = MolmoPoolingConfig()

    >>> # Initializing a Molmo allenai/Molmo-7B-D-0924-hf style configuration
    >>> configuration = MolmoConfig.from_text_vision_configs(vision_config, text_config, pooling_config)

    >>> # Initializing a model from the allenai/Molmo-7B-D-0924-hf style configuration
    >>> model = MolmoForConditionalGeneration(configuration)

    >>> # Accessing the model configuration
    >>> configuration = model.config
    ```"""

    model_type = "molmo"
    sub_configs = {
        "text_config": MolmoTextConfig,
        "vision_config": MolmoVisionConfig,
        "pooling_config": MolmoPoolingConfig,
    }

    def __init__(
        self,
        vision_config=None,
        text_config=None,
        pooling_config=None,
        image_token_index=152069,
        image_seq_length=576,
        initializer_range=0.02,
        vision_feature_select_strategy="default",
        vision_feature_layers=(-2, -9),
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.image_token_index = image_token_index
        self.image_seq_length = image_seq_length
        self.vision_feature_select_strategy = vision_feature_select_strategy
        self.vision_feature_layers = vision_feature_layers
        if vision_config is None:
            vision_config = {}
            logger.info("vision_config is None. initializing the MolmoVisionConfig with default values.")
        if text_config is None:
            text_config = {}
            logger.info("text_config is None. initializing the MolmoTextConfig with default values.")
        if pooling_config is None:
            pooling_config = {}
            logger.info("pooling_config is None. initializing the MolmoPoolingConfig with default values.")
        self.vision_config = MolmoVisionConfig(**vision_config)
        self.text_config = MolmoTextConfig(**text_config)
        self.pooling_config = MolmoPoolingConfig(**pooling_config)
        self.initializer_range = initializer_range

    @classmethod
    def from_text_vision_configs(
        cls,
        text_config: MolmoTextConfig,
        vision_config: MolmoVisionConfig,
        pooling_config: MolmoPoolingConfig,
        **kwargs,
    ):
        r"""
        Instantiate a [`MolmoConfig`] (or a derived class) from molmo text model configuration, molmo vision model
        configuration and molmo pooling module conffiguration.

        Returns:
            [`MolmoConfig`]: An instance of a configuration object
        """

        return cls(
            text_config=text_config.to_dict(),
            vision_config=vision_config.to_dict(),
            pooling_config=pooling_config.to_dict(),
            **kwargs,
        )


__all__ = ["MolmoConfig", "MolmoVisionConfig"]
