import math
from functools import cached_property
from typing import Dict, List, Optional, Tuple, Union

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.utils.checkpoint

from ...cache_utils import Cache, StaticCache
from ...configuration_utils import PretrainedConfig
from ...generation import GenerationMixin
from ...modeling_attn_mask_utils import AttentionMaskConverter
from ...modeling_outputs import (
    BaseModelOutputWithPast,
    CausalLMOutputWithPast,
)
from ...modeling_rope_utils import rope_config_validation
from ...modeling_utils import PreTrainedModel
from ...utils import (
    add_start_docstrings,
    add_start_docstrings_to_model_forward,
    is_flash_attn_2_available,
    logging,
)
from ..chameleon.modeling_chameleon import (
    ChameleonLayerNorm,
    ChameleonPreTrainedModel,
    ChameleonVQVAEEncoderConvDownsample,
)
from ..llama.modeling_llama import (
    LlamaAttention,
    LlamaDecoderLayer,
    LlamaDynamicNTKScalingRotaryEmbedding,
    LlamaFlashAttention2,
    LlamaLinearScalingRotaryEmbedding,
    LlamaMLP,
    LlamaRMSNorm,
    LlamaRotaryEmbedding,
    LlamaSdpaAttention,
)


if is_flash_attn_2_available():
    from flash_attn.bert_padding import index_first_axis, pad_input, unpad_input  # noqa


_CHECKPOINT_FOR_DOC = "Emu3-community/Emu3-Chat-hf"

logger = logging.get_logger(__name__)


class Emu3VQVAEConfig(PretrainedConfig):
    r"""
    This is the configuration class to store the configuration of a [`Emu3VQVAE`]. It is used to instantiate an VQ-VAE
    model according to the specified arguments, defining the model architecture. Instantiating a configuration with the
    defaults will yield a configuration to the VQ model presented in Emu3 paper.

    Configuration objects inherit from [`PretrainedConfig`] and can be used to control the model outputs. Read the
    documentation from [`PretrainedConfig`] for more information.
    Args:
        codebook_size (`int`, *optional*, defaults to 32768):
            Codebook size of the VQ model.
        embed_dim (`int`, *optional*, defaults to 4):
            Dimension of the quantized vector in codebook.
        latent_channels (`int`, *optional*, defaults to 4):
            Dimension of the output channel of encoder and the input channel of decoder
        double_latent (`bool`, *optional*, defaults to `False`):
            Whether double the output dim of the encoder.
        in_channels (`int`, *optional*, defaults to 3):
            Input channel of encoder.
        out_channels (`int`, *optional*, defaults to 3):
            Output channel of decoder.
        temporal_downsample_factor (`int`, *optional*, defaults to 4):
            Temporal downsample factor.
        base_channels (`int`, *optional*, defaults to 256):
            Basic channel number of the intermediate blocks.
        channel_multiplier (`List[int]`, *optional*, defaults to `[1, 2, 2, 4]`):
            Channel scaling factor of the intermediate blocks.
        num_res_blocks (`int`, *optional*, defaults to 2):
            Residual block number in each stage.
        attn_resolutions (`List[int]`, *optional*, defaults to `[3]`):
            Stage indices to apply attention.
        initializer_range (`<float>`, *optional*, defaults to 0.02):
            The standard deviation of the truncated_normal_initializer for initializing all weight matrices.

    ```python
    >>> from transformers import Emu3VQVAE, Emu3VQVAEConfig

    >>> # Initializing a video VQ model of Emu3 configuration
    >>> configuration = Emu3VQVAEConfig()

    >>> # Initializing a model from the Emu3 VQ model style configuration
    >>> model = Emu3VQVAE(configuration)

    >>> # Accessing the model configuration
    >>> configuration = model.config
    ```"""

    model_type = "emu3_vqgan"

    def __init__(
        self,
        codebook_size: int = 32768,
        embed_dim: int = 4,
        latent_channels: int = 4,
        double_latent: bool = False,
        in_channels: int = 3,
        out_channels: int = 3,
        temporal_downsample_factor: int = 4,
        base_channels: int = 256,
        channel_multiplier: List[int] = [1, 2, 2, 4],
        num_res_blocks: int = 2,
        attn_resolutions: List[int] = [3],
        initializer_range=0.02,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self.codebook_size = codebook_size
        self.embed_dim = embed_dim
        self.latent_channels = latent_channels
        self.double_latent = double_latent
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.temporal_downsample_factor = temporal_downsample_factor
        self.base_channels = base_channels
        self.channel_multiplier = channel_multiplier
        self.num_res_blocks = num_res_blocks
        self.attn_resolutions = attn_resolutions
        self.initializer_range = initializer_range


class Emu3TextConfig(PretrainedConfig):
    r"""
    This is the configuration class to store the configuration of a [`Emu3TextModel`]. It is used to instantiate a
    emu3 model according to the specified arguments, defining the model architecture. Instantiating a
    configuration with the defaults will yield a similar configuration to that of the
    [BAAI/Emu3-Chat-hf](https://huggingface.co/BAAI/Emu3-Chat-hf).

    Configuration objects inherit from [`PretrainedConfig`] and can be used to control the model outputs. Read the
    documentation from [`PretrainedConfig`] for more information.


    Args:
        vocab_size (`int`, *optional*, defaults to 184622):
            Vocabulary size of the Emu3 model. Defines the number of different tokens that can be represented by the
            `inputs_ids` passed when calling [`Emu3Model`]
        hidden_size (`int`, *optional*, defaults to 4096):
            Dimension of the hidden representations.
        intermediate_size (`int`, *optional*, defaults to 14336):
            Dimension of the MLP representations.
        num_hidden_layers (`int`, *optional*, defaults to 32):
            Number of hidden layers in the Transformer decoder.
        num_attention_heads (`int`, *optional*, defaults to 32):
            Number of attention heads for each attention layer in the Transformer decoder.
        num_key_value_heads (`int`, *optional*, defaults to 8):
            This is the number of key_value heads that should be used to implement Grouped Query Attention. If
            `num_key_value_heads=num_attention_heads`, the model will use Multi Head Attention (MHA), if
            `num_key_value_heads=1 the model will use Multi Query Attention (MQA) otherwise GQA is used. When
            converting a multi-head checkpoint to a GQA checkpoint, each group key and value head should be constructed
            by meanpooling all the original heads within that group. For more details checkout [this
            paper](https://arxiv.org/pdf/2305.13245.pdf). If it is not specified, will default to
            `num_attention_heads`.
        hidden_act (`str` or `function`, *optional*, defaults to `"silu"`):
            The non-linear activation function (function or string) in the decoder.
        max_position_embeddings (`int`, *optional*, defaults to 9216):
            The maximum sequence length that this model might ever be used with. Emu supports up to 9216 tokens,
        initializer_range (`float`, *optional*, defaults to 0.02):
            The standard deviation of the truncated_normal_initializer for initializing all weight matrices.
        rms_norm_eps (`float`, *optional*, defaults to 1e-05):
            The epsilon used by the rms normalization layers.
        use_cache (`bool`, *optional*, defaults to `True`):
            Whether or not the model should return the last key/values attentions (not used by all models). Only
            relevant if `config.is_decoder=True`.
        pad_token_id (`int`, *optional*, defaults to 151643):
            Padding token id.
        bos_token_id (`int`, *optional*, defaults to 151849):
            Beginning of stream token id.
        eos_token_id (`int`, *optional*, defaults to 151850):
            End of stream token id.
        pretraining_tp (`int`, *optional*, defaults to 1):
            Experimental feature. Tensor parallelism rank used during pretraining. Please refer to [this
            document](https://huggingface.co/docs/transformers/parallelism) to understand more about it. This value is
            necessary to ensure exact reproducibility of the pretraining results. Please refer to [this
            issue](https://github.com/pytorch/pytorch/issues/76232).
        tie_word_embeddings (`bool`, *optional*, defaults to `False`):
            Whether to tie weight embeddings
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
        attention_bias (`bool`, *optional*, defaults to `False`):
            Whether to use a bias in the query, key, value and output projection layers during self-attention.
        mlp_bias (`bool`, *optional*, defaults to `False`):
            Whether to use a bias in up_proj, down_proj and gate_proj layers in the MLP layers.
        attention_dropout (`float`, *optional*, defaults to 0.1):
            The dropout ratio for the attention probabilities.


    ```python
    >>> from transformers import Emu3Model, Emu3Config

    >>> # Initializing a BAAI/Emu3-Chat-hf style configuration
    >>> configuration = Emu3Config()

    >>> # Initializing a model from the BAAI/Emu3-Chat-hf style configuration
    >>> model = Emu3Model(configuration)

    >>> # Accessing the model configuration
    >>> configuration = model.config
    ```"""

    model_type = "emu3_text_model"
    keys_to_ignore_at_inference = ["past_key_values"]

    def __init__(
        self,
        vocab_size: int = 184622,
        hidden_size: int = 4096,
        intermediate_size: int = 14336,
        num_hidden_layers: int = 32,
        num_attention_heads: int = 32,
        num_key_value_heads: Optional[int] = 8,
        hidden_act: str = "silu",
        max_position_embeddings: int = 9216,
        initializer_range: float = 0.02,
        rms_norm_eps: float = 1e-5,
        use_cache: bool = True,
        pad_token_id: int = 151643,
        bos_token_id: int = 151849,
        eos_token_id: int = 151850,
        pretraining_tp: int = 1,
        tie_word_embeddings: bool = False,
        rope_theta: float = 1000000.0,
        rope_scaling: Optional = None,
        mlp_bias=False,
        attention_bias=False,
        attention_dropout: float = 0.1,
        **kwargs,
    ):
        self.vocab_size = vocab_size
        self.max_position_embeddings = max_position_embeddings
        self.hidden_size = hidden_size
        self.intermediate_size = intermediate_size
        self.num_hidden_layers = num_hidden_layers
        self.num_attention_heads = num_attention_heads
        self.num_key_value_heads = num_key_value_heads
        self.hidden_act = hidden_act
        self.initializer_range = initializer_range
        self.rms_norm_eps = rms_norm_eps
        self.use_cache = use_cache
        self.rope_theta = rope_theta
        self.rope_scaling = rope_scaling
        self.mlp_bias = mlp_bias
        self.attention_bias = attention_bias
        rope_config_validation(self)

        self.attention_dropout = attention_dropout
        self.pretraining_tp = pretraining_tp

        super().__init__(
            pad_token_id=pad_token_id,
            bos_token_id=bos_token_id,
            eos_token_id=eos_token_id,
            tie_word_embeddings=tie_word_embeddings,
            **kwargs,
        )


class Emu3Config(PretrainedConfig):
    """
    This is the configuration class to store the configuration of a [`Emu3Model`]. It is used to instantiate a
    emu3 model according to the specified arguments, defining the model architecture. Instantiating a
    configuration with the defaults will yield a similar configuration to that of the
    [BAAI/Emu3-Chat-hf](https://huggingface.co/BAAI/Emu3-Chat-hf).

    Configuration objects inherit from [`PretrainedConfig`] and can be used to control the model outputs. Read the
    documentation from [`PretrainedConfig`] for more information.


    Args:
        vq_config (`Union[Dict, Emu3VQVAEConfig]`, *optional*):
            Emu3VQVAEConfig instance containing the configuration for the VQ-VAE model.
        text_config (`Union[Dict, Emu3TextConfig]``, *optional*):
            Emu3TextConfig instance containing the configuration for the language model.
        vocabulary_map (`dict`, *optional*):
            A dictionary containing the vocabulary map from the tokenizer. Used to obtain tokens from the image inputs.
    """

    model_type = "emu3"
    keys_to_ignore_at_inference = ["past_key_values"]

    def __init__(
        self,
        vq_config: Union[Dict, Emu3VQVAEConfig] = None,
        text_config: Union[Dict, Emu3TextConfig] = None,
        vocabulary_map: Dict[int, int] = None,
        **kwargs,
    ):
        if vq_config is None:
            vq_config = Emu3VQVAEConfig()
            logger.info("Passed `vq_config` is None. initializing the `Emu3VQVAEConfig` with default values.")
        elif isinstance(vq_config, dict):
            vq_config = Emu3VQVAEConfig(**vq_config)

        if text_config is None:
            text_config = Emu3TextConfig()
            logger.info("Passed `text_config` is None. initializing the `Emu3TextConfig` with default values.")
        elif isinstance(text_config, dict):
            text_config = Emu3TextConfig(**text_config)

        self.vq_config = vq_config
        self.text_config = text_config
        self.vocabulary_map = vocabulary_map

        super().__init__(**kwargs)


class Emu3RMSNorm(LlamaRMSNorm):
    pass


class Emu3RotaryEmbedding(LlamaRotaryEmbedding):
    pass


class Emu3LinearScalingRotaryEmbedding(LlamaLinearScalingRotaryEmbedding, Emu3RotaryEmbedding):
    pass


class Emu3DynamicNTKScalingRotaryEmbedding(LlamaDynamicNTKScalingRotaryEmbedding, Emu3RotaryEmbedding):
    pass


class Emu3MLP(LlamaMLP):
    pass


class Emu3LayerNorm(ChameleonLayerNorm):
    pass


class Emu3Attention(LlamaAttention):
    pass


class Emu3FlashAttention2(LlamaFlashAttention2, Emu3Attention):
    pass


class Emu3SdpaAttention(LlamaSdpaAttention, Emu3Attention):
    pass


class Emu3DecoderLayer(LlamaDecoderLayer, Emu3MLP, Emu3RMSNorm):
    def __init__(self, config: Emu3Config, layer_idx: int):
        super().__init__(config, layer_idx)
        self.dropout = nn.Dropout(config.attention_dropout)

    def forward(
        self,
        hidden_states: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        position_ids: Optional[torch.LongTensor] = None,
        past_key_value: Optional[Cache] = None,
        output_attentions: Optional[bool] = False,
        use_cache: Optional[bool] = False,
        cache_position: Optional[torch.LongTensor] = None,
        position_embeddings: Optional[Tuple[torch.Tensor, torch.Tensor]] = None,
        **kwargs,
    ) -> Tuple[torch.FloatTensor, Optional[Tuple[torch.FloatTensor, torch.FloatTensor]]]:
        """
        Args:
            hidden_states (`torch.FloatTensor`): input to the layer of shape `(batch, seq_len, embed_dim)`
            attention_mask (`torch.FloatTensor`, *optional*):
                attention mask of size `(batch_size, sequence_length)` if flash attention is used or `(batch_size, 1,
                query_sequence_length, key_sequence_length)` if default attention is used.
            output_attentions (`bool`, *optional*):
                Whether or not to return the attentions tensors of all attention layers. See `attentions` under
                returned tensors for more detail.
            use_cache (`bool`, *optional*):
                If set to `True`, `past_key_values` key value states are returned and can be used to speed up decoding
                (see `past_key_values`).
            past_key_value (`Tuple(torch.FloatTensor)`, *optional*): cached past key and value projection states
            cache_position (`torch.LongTensor` of shape `(sequence_length)`, *optional*):
                Indices depicting the position of the input sequence tokens in the sequence
            kwargs (`dict`, *optional*):
                Arbitrary kwargs to be ignored, used for FSDP and other methods that injects code
                into the model
        """
        residual = hidden_states

        hidden_states = self.input_layernorm(hidden_states)

        # Self Attention
        hidden_states, self_attn_weights, present_key_value = self.self_attn(
            hidden_states=hidden_states,
            attention_mask=attention_mask,
            position_ids=position_ids,
            past_key_value=past_key_value,
            output_attentions=output_attentions,
            use_cache=use_cache,
            cache_position=cache_position,
            position_embeddings=position_embeddings,
            **kwargs,
        )
        hidden_states = residual + self.dropout(hidden_states)

        # Fully Connected
        residual = hidden_states
        hidden_states = self.post_attention_layernorm(hidden_states)
        hidden_states = self.mlp(hidden_states)
        hidden_states = residual + hidden_states

        outputs = (hidden_states,)

        if output_attentions:
            outputs += (self_attn_weights,)

        if use_cache:
            outputs += (present_key_value,)

        return outputs


class Emu3VQVAEVectorQuantizer(nn.Module):
    """
    A module for vector quantization using learned embedding vectors.

    This module implements the quantization process similar to te one described in
    the VQ-VAE (Vector Quantized Variational AutoEncoder) paper. It quantizes continuous
    input vectors into discrete codebook vectors, which are learned during training.
    Current implementation improves over previous ones by avoiding costly matrix multiplications
    and allowing for post-hoc remapping of indices.
    """

    def __init__(self, config: Emu3VQVAEConfig):
        super().__init__()
        self.embedding = nn.Embedding(config.codebook_size, config.embed_dim)
        self.embedding.weight.data.uniform_(-1.0 / config.codebook_size, 1.0 / config.codebook_size)

    def forward(self, hidden_state: torch.Tensor):
        batch_size, temporal, channels, height, width = hidden_state.shape
        hidden_state = hidden_state.permute(0, 1, 3, 4, 2).contiguous()
        hidden_state_flattened = hidden_state.view(-1, channels)

        # distances from z to embeddings e_j (z - e)^2 = z^2 + e^2 - 2 e * z
        distances = (
            torch.sum(hidden_state_flattened**2, dim=1, keepdim=True)
            + torch.sum(self.embedding.weight**2, dim=1)
            - 2 * torch.einsum("bd,dn->bn", hidden_state_flattened, self.embedding.weight.transpose(0, 1))
        )

        min_encoding_indices = torch.argmin(distances, dim=1)
        min_encoding_indices = min_encoding_indices.view(batch_size, temporal, height, width)
        return min_encoding_indices


class Emu3VQVAEEncoderConvDownsample(ChameleonVQVAEEncoderConvDownsample):
    pass


class Emu3VQVAEEncoderConvUpsample(nn.Module):
    def __init__(self, in_channels):
        super().__init__()
        self.conv = nn.Conv2d(in_channels, in_channels, kernel_size=3, stride=1, padding=1)

    def forward(self, hidden_states):
        hidden_states = F.interpolate(hidden_states, scale_factor=2.0, mode="nearest")
        hidden_states = self.conv(hidden_states)
        return hidden_states


class Emu3VQVAEConv3d(nn.Module):
    def __init__(
        self,
        in_channel: int,
        out_channel: int,
        kernel_size: Union[int, tuple],
        stride: Union[int, tuple],
    ):
        super().__init__()

        if isinstance(kernel_size, int):
            kernel_size = (kernel_size,) * 3
        if isinstance(stride, int):
            stride = (stride,) * 3

        padding_sizes = [one_kernel - one_stride for one_kernel, one_stride in zip(kernel_size[1:], stride[1:])]
        self.padding = ()
        for pad_size in padding_sizes[::-1]:
            self.padding += (pad_size // 2 + pad_size % 2, pad_size // 2)
        self.padding += (2, 0)

        self.conv = nn.Conv3d(
            in_channel,
            out_channel,
            kernel_size,
            stride=stride,
        )

    def forward(self, hidden_states: torch.Tensor):
        hidden_states = F.pad(hidden_states, self.padding)
        hidden_states = self.conv(hidden_states)
        return hidden_states


class Emu3VQVAESpatialNorm(nn.Module):
    def __init__(
        self,
        in_channels: int,
        out_channels: int,
    ):
        super().__init__()
        self.norm_layer = nn.GroupNorm(
            num_channels=out_channels,
            num_groups=32,
            eps=1e-6,
            affine=True,
        )

        self.conv_y = nn.Conv2d(
            in_channels,
            out_channels,
            kernel_size=1,
            stride=1,
            padding=0,
        )
        self.conv_b = nn.Conv2d(
            in_channels,
            out_channels,
            kernel_size=1,
            stride=1,
            padding=0,
        )

    def forward(self, hidden_states: torch.Tensor, quant_states: torch.Tensor):
        quant_states = F.interpolate(quant_states, size=hidden_states.shape[-2:], mode="nearest")
        hidden_states = self.norm_layer(hidden_states)
        hidden_states = hidden_states * self.conv_y(quant_states) + self.conv_b(quant_states)
        return hidden_states


class Emu3VQVAETemporalUpsample(nn.Module):
    def __init__(
        self,
        in_channel: int,
        out_channel: int,
    ):
        super().__init__()
        self.in_channel = in_channel
        self.out_channel = out_channel
        self.conv = Emu3VQVAEConv3d(
            in_channel,
            out_channel,
            kernel_size=3,
            stride=1,
        )

    def forward(self, hidden_states: torch.Tensor):
        batch_size, channels, temporal, height, width = hidden_states.shape
        hidden_states = hidden_states.permute(0, 1, 3, 4, 2).contiguous().view(batch_size, -1, temporal)
        hidden_states = F.interpolate(hidden_states, scale_factor=2.0, mode="nearest")
        hidden_states = hidden_states.view(batch_size, channels, height, width, -1).permute(0, 1, 4, 2, 3).contiguous()
        hidden_states = self.conv(hidden_states)
        return hidden_states


class Emu3VQVAETemporalDownsample(nn.Module):
    def __init__(
        self,
        in_channel: int,
        out_channel: int,
    ):
        super().__init__()
        self.in_channel = in_channel
        self.out_channel = out_channel

        self.conv = Emu3VQVAEConv3d(
            in_channel,
            out_channel,
            kernel_size=(4, 3, 3),
            stride=(2, 1, 1),
        )

    def forward(self, hidden_states: torch.Tensor):
        hidden_states = self.conv(hidden_states)
        return hidden_states


class Emu3VQVAETemporalResnetBlock(nn.Module):
    def __init__(
        self,
        in_channels,
        out_channels=None,
    ):
        super().__init__()
        self.in_channels = in_channels
        self.out_channels = in_channels if out_channels is None else out_channels

        self.norm1 = nn.BatchNorm3d(in_channels)
        self.conv1 = Emu3VQVAEConv3d(
            in_channels,
            out_channels,
            kernel_size=3,
            stride=1,
        )
        self.norm2 = nn.BatchNorm3d(out_channels)
        self.conv2 = Emu3VQVAEConv3d(
            out_channels,
            out_channels,
            kernel_size=3,
            stride=1,
        )
        if self.in_channels != self.out_channels:
            self.nin_shortcut = nn.Conv3d(
                in_channels,
                out_channels,
                kernel_size=1,
                stride=1,
                padding=0,
            )

    def forward(self, hidden_states):
        residual = hidden_states
        hidden_states = self.norm1(hidden_states)
        hidden_states *= torch.sigmoid(hidden_states)
        hidden_states = self.conv1(hidden_states)

        hidden_states = self.norm2(hidden_states)
        hidden_states *= torch.sigmoid(hidden_states)
        hidden_states = self.conv2(hidden_states)

        if self.in_channels != self.out_channels:
            residual = self.nin_shortcut(residual)

        return residual + hidden_states


class Emu3VQVAEResnetBlock(nn.Module):
    def __init__(
        self,
        in_channels: int,
        out_channels: Optional[int] = None,
        quant_channels: Optional[int] = None,
    ):
        super().__init__()
        self.in_channels = in_channels
        out_channels = in_channels if out_channels is None else out_channels
        self.out_channels = out_channels
        self.quant_channels = quant_channels

        if quant_channels is None:
            self.norm1 = nn.GroupNorm(num_channels=in_channels, num_groups=32, eps=1e-6, affine=True)
            self.norm2 = nn.GroupNorm(num_channels=out_channels, num_groups=32, eps=1e-6, affine=True)
        else:
            self.norm1 = Emu3VQVAESpatialNorm(quant_channels, in_channels)
            self.norm2 = Emu3VQVAESpatialNorm(quant_channels, out_channels)

        self.conv1 = nn.Conv2d(
            in_channels,
            out_channels,
            kernel_size=3,
            stride=1,
            padding=1,
        )

        self.conv2 = nn.Conv2d(
            out_channels,
            out_channels,
            kernel_size=3,
            stride=1,
            padding=1,
        )

        if self.in_channels != self.out_channels:
            self.nin_shortcut = nn.Conv2d(
                in_channels,
                out_channels,
                kernel_size=1,
                stride=1,
                padding=0,
            )

    def forward(self, hidden_states: torch.Tensor, quant_channels: Optional[torch.Tensor] = None):
        norm_args = () if self.quant_channels is None else (quant_channels,)

        residual = hidden_states
        hidden_states = self.norm1(hidden_states, *norm_args)
        hidden_states *= torch.sigmoid(hidden_states)
        hidden_states = self.conv1(hidden_states)

        hidden_states = self.norm2(hidden_states, *norm_args)
        hidden_states *= torch.sigmoid(hidden_states)
        hidden_states = self.conv2(hidden_states)

        if self.in_channels != self.out_channels:
            residual = self.nin_shortcut(residual)

        return residual + hidden_states


class Emu3VQVAEAttnBlock(nn.Module):
    def __init__(self, in_channels, quant_channels=None):
        super().__init__()
        self.in_channels = in_channels
        self.quant_channels = quant_channels

        if quant_channels is None:
            self.norm = nn.GroupNorm(num_channels=in_channels, num_groups=32, eps=1e-6, affine=True)
        else:
            self.norm = Emu3VQVAESpatialNorm(quant_channels, in_channels)

        self.q = nn.Conv2d(in_channels, in_channels, kernel_size=1, stride=1, padding=0)
        self.k = nn.Conv2d(in_channels, in_channels, kernel_size=1, stride=1, padding=0)
        self.v = nn.Conv2d(in_channels, in_channels, kernel_size=1, stride=1, padding=0)
        self.proj_out = nn.Conv2d(in_channels, in_channels, kernel_size=1, stride=1, padding=0)

    def forward(self, hidden_states, quant_channels=None):
        norm_args = () if self.quant_channels is None else (quant_channels,)

        residual = hidden_states
        hidden_states = self.norm(hidden_states, *norm_args)
        query_states = self.q(hidden_states)
        key_states = self.k(hidden_states)
        value_states = self.v(hidden_states)

        # compute attention
        batch_size, channels, height, width = query_states.shape
        query_states = query_states.reshape(batch_size, channels, height * width).permute(0, 2, 1)
        key_states = key_states.reshape(batch_size, channels, height * width)
        attn_weights = torch.bmm(query_states, key_states)
        attn_weights = attn_weights * (int(channels) ** (-0.5))
        attn_weights = F.softmax(attn_weights, dim=2)

        # attend to values
        value_states = value_states.reshape(batch_size, channels, height * width)
        attn_weights = attn_weights.permute(0, 2, 1)
        attn_output = torch.bmm(value_states, attn_weights).reshape(batch_size, channels, height, width)

        attn_output = self.proj_out(attn_output)
        return residual + attn_output


class Emu3VQVAEEncoder(nn.Module):
    def __init__(self, config):
        super().__init__()

        self.num_resolutions = len(config.channel_multiplier)
        self.num_res_blocks = config.num_res_blocks
        base_channels = config.base_channels
        in_channels = config.in_channels
        double_latent = config.double_latent
        latent_channels = config.latent_channels
        channel_multiplier = config.channel_multiplier

        self.conv_in = torch.nn.Conv2d(in_channels, base_channels, kernel_size=3, stride=1, padding=1)

        in_channel_multiplier = (1,) + tuple(channel_multiplier)
        self.in_channel_multiplier = in_channel_multiplier
        self.down = nn.ModuleList()
        for i_level in range(self.num_resolutions):
            block = nn.ModuleList()
            attn = nn.ModuleList()
            block_in = base_channels * in_channel_multiplier[i_level]
            block_out = base_channels * channel_multiplier[i_level]
            for i_block in range(self.num_res_blocks):
                block.append(
                    Emu3VQVAEResnetBlock(
                        in_channels=block_in,
                        out_channels=block_out,
                    )
                )
                block_in = block_out
                if config.attn_resolutions is not None and i_level in config.attn_resolutions:
                    attn.append(Emu3VQVAEAttnBlock(block_in))

            down = nn.Module()
            down.block = block
            down.attn = attn
            if i_level != self.num_resolutions - 1:
                down.downsample = Emu3VQVAEEncoderConvDownsample(block_in)
            self.down.append(down)

        self.mid = nn.Module()
        self.mid.block_1 = Emu3VQVAEResnetBlock(
            in_channels=block_in,
            out_channels=block_in,
        )
        self.mid.attn_1 = Emu3VQVAEAttnBlock(block_in)
        self.mid.block_2 = Emu3VQVAEResnetBlock(
            in_channels=block_in,
            out_channels=block_in,
        )

        self.norm_out = torch.nn.GroupNorm(num_groups=32, num_channels=block_in, eps=1e-6, affine=True)
        out_channels = 2 * latent_channels if double_latent else latent_channels
        self.conv_out = torch.nn.Conv2d(
            block_in,
            out_channels,
            kernel_size=3,
            stride=1,
            padding=1,
        )

        temporal_down_blocks = int(math.log2(config.temporal_downsample_factor))
        self.time_conv = nn.ModuleList()

        for i in range(temporal_down_blocks):
            conv = Emu3VQVAETemporalDownsample(out_channels, out_channels)
            self.time_conv.append(conv)

        self.time_res_stack = nn.Sequential(
            *[
                Emu3VQVAETemporalResnetBlock(
                    in_channels=out_channels,
                    out_channels=out_channels,
                )
                for _ in range(self.num_res_blocks)
            ]
        )

    def forward(self, pixel_values: torch.LongTensor):
        temporal_dim = pixel_values.shape[1]
        pixel_values = pixel_values.reshape(-1, *pixel_values.shape[2:])

        # downsampling
        hidden_states = self.conv_in(pixel_values)
        for i_level in range(self.num_resolutions):
            for i_block in range(self.num_res_blocks):
                hidden_states = self.down[i_level].block[i_block](
                    hidden_states,
                )
                if len(self.down[i_level].attn) > 0:
                    hidden_states = self.down[i_level].attn[i_block](hidden_states)
            if i_level != self.num_resolutions - 1:
                hidden_states = self.down[i_level].downsample(hidden_states)

        # middle
        hidden_states = self.mid.block_1(hidden_states)
        hidden_states = self.mid.attn_1(hidden_states)
        hidden_states = self.mid.block_2(hidden_states)

        # end
        hidden_states = self.norm_out(hidden_states)
        hidden_states *= torch.sigmoid(hidden_states)
        hidden_states = self.conv_out(hidden_states)

        hidden_states = hidden_states.reshape(-1, temporal_dim, *hidden_states.shape[1:])
        hidden_states = hidden_states.permute(0, 2, 1, 3, 4)

        for conv in self.time_conv:
            hidden_states = conv(hidden_states)
            hidden_states *= torch.sigmoid(hidden_states)

        hidden_states = self.time_res_stack(hidden_states)
        hidden_states = hidden_states.permute(0, 2, 1, 3, 4)

        return hidden_states


class Emu3VQVAEDecoder(nn.Module):
    def __init__(self, config: Emu3VQVAEConfig):
        super().__init__()
        self.base_channels = config.base_channels
        self.num_resolutions = len(config.channel_multiplier)
        self.num_res_blocks = config.num_res_blocks

        quant_channels = config.embed_dim
        block_in = config.base_channels * config.channel_multiplier[-1]
        self.time_res_stack = nn.Sequential(
            *[
                Emu3VQVAETemporalResnetBlock(
                    in_channels=config.latent_channels,
                    out_channels=config.latent_channels,
                )
                for _ in range(config.num_res_blocks)
            ]
        )

        temp_upsample_block_num = int(math.log2(config.temporal_downsample_factor))
        self.time_conv = nn.ModuleList()
        for i in range(temp_upsample_block_num):
            conv = Emu3VQVAETemporalUpsample(config.latent_channels, config.latent_channels)
            self.time_conv.append(conv)

        self.conv_in = nn.Conv2d(
            config.latent_channels,
            block_in,
            kernel_size=3,
            stride=1,
            padding=1,
        )

        # middle
        self.mid = nn.Module()
        self.mid.block_1 = Emu3VQVAEResnetBlock(
            in_channels=block_in,
            out_channels=block_in,
            quant_channels=quant_channels,
        )
        self.mid.attn_1 = Emu3VQVAEAttnBlock(block_in, quant_channels)
        self.mid.block_2 = Emu3VQVAEResnetBlock(
            in_channels=block_in,
            out_channels=block_in,
            quant_channels=quant_channels,
        )

        # upsampling
        self.up = nn.ModuleList()
        for i_level in reversed(range(self.num_resolutions)):
            block = nn.ModuleList()
            attn = nn.ModuleList()
            block_out = config.base_channels * config.channel_multiplier[i_level]
            for i_block in range(self.num_res_blocks + 1):
                block.append(
                    Emu3VQVAEResnetBlock(
                        in_channels=block_in,
                        out_channels=block_out,
                        quant_channels=quant_channels,
                    )
                )
                block_in = block_out
                if i_level in config.attn_resolutions:
                    attn.append(Emu3VQVAEAttnBlock(block_in, quant_channels))

            up = nn.Module()
            up.block = block
            up.attn = attn
            if i_level != 0:
                up.upsample = Emu3VQVAEEncoderConvUpsample(block_in)

            self.up.insert(0, up)

        self.norm_out = Emu3VQVAESpatialNorm(quant_channels, block_in)
        self.conv_out = nn.Conv2d(
            block_in,
            config.out_channels,
            kernel_size=3,
            stride=1,
            padding=1,
        )

    def forward(self, hidden_states: torch.Tensor, quant_states: torch.Tensor):
        hidden_quant_states = torch.cat((hidden_states, quant_states), dim=0)
        hidden_quant_states = hidden_quant_states.permute(0, 2, 1, 3, 4)
        hidden_quant_states = self.time_res_stack(hidden_quant_states)

        for conv in self.time_conv:
            hidden_quant_states = conv(hidden_quant_states)
            hidden_quant_states *= torch.sigmoid(hidden_quant_states)

        hidden_quant_states = hidden_quant_states.permute(0, 2, 1, 3, 4)

        hidden_states, quant_states = torch.chunk(hidden_quant_states, 2, dim=0)

        hidden_states = hidden_states.reshape(-1, *hidden_states.shape[2:])
        quant_states = quant_states.reshape(-1, *quant_states.shape[2:])

        hidden_states = self.conv_in(hidden_states)

        # middle
        hidden_states = self.mid.block_1(hidden_states, quant_states)
        hidden_states = self.mid.attn_1(hidden_states, quant_states)
        hidden_states = self.mid.block_2(hidden_states, quant_states)

        # upsampling
        for i_level in reversed(range(self.num_resolutions)):
            for i_block in range(self.num_res_blocks + 1):
                hidden_states = self.up[i_level].block[i_block](hidden_states, quant_states)
                if len(self.up[i_level].attn) > 0:
                    hidden_states = self.up[i_level].attn[i_block](hidden_states, quant_states)

            if i_level != 0:
                hidden_states = self.up[i_level].upsample(hidden_states)

        hidden_states = self.norm_out(hidden_states, quant_states)
        hidden_states *= torch.sigmoid(hidden_states)
        hidden_states = self.conv_out(hidden_states)

        return hidden_states


EMU3_VQ_START_DOCSTRING = r"""
    This model inherits from [`PreTrainedModel`]. Check the superclass documentation for the generic methods the
    library implements for all its model (such as downloading or saving, resizing the input embeddings, pruning heads
    etc.)

    This model is also a PyTorch [torch.nn.Module](https://pytorch.org/docs/stable/nn.html#torch.nn.Module) subclass.
    Use it as a regular PyTorch Module and refer to the PyTorch documentation for all matter related to general usage
    and behavior.

    Parameters:
        config ([`Emu3VQVAEConfig`]):
            Model configuration class with all the parameters of the model. Initializing with a config file does not
            load the weights associated with the model, only the configuration. Check out the
            [`~PreTrainedModel.from_pretrained`] method to load the model weights.
"""


@add_start_docstrings(
    """The VQ-VAE model used in Emu3 for encoding/decoding images into discrete tokens.
    This model follows the "Make-a-scene: Scene-based text-to-image generation with human priors" paper from
    [ Oran Gafni, Adam Polyak, Oron Ashual, Shelly Sheynin, Devi Parikh, and Yaniv Taigman](https://arxiv.org/abs/2203.13131).
    """,
    EMU3_VQ_START_DOCSTRING,
)
class Emu3VQVAE(PreTrainedModel):
    config_class = Emu3VQVAEConfig
    base_model_prefix = "emuvideovq"
    main_input_name = "pixel_values"
    _no_split_modules = [
        "Emu3VQVAETemporalResnetBlock",
        "Emu3VQVAEAttnBlock",
        "Emu3VQVAEResnetBlock",
        "Emu3VQVAEVectorQuantizer",
    ]

    def _init_weights(self, module):
        if isinstance(module, (nn.Conv2d, nn.Conv3d)):
            nn.init.kaiming_normal_(module.weight, mode="fan_out", nonlinearity="relu")
        elif isinstance(module, nn.Linear):
            nn.init.kaiming_uniform_(module.weight, a=math.sqrt(5))
            if module.bias is not None:
                fan_in, _ = nn.init._calculate_fan_in_and_fan_out(module.weight)
                bound = 1 / math.sqrt(fan_in) if fan_in > 0 else 0
                nn.init.uniform_(module.bias, -bound, bound)
        elif isinstance(module, (nn.BatchNorm2d, nn.BatchNorm3d, nn.GroupNorm)):
            nn.init.constant_(module.weight, 1)
            nn.init.constant_(module.bias, 0)

    def __init__(self, config: Emu3VQVAEConfig):
        super().__init__(config)

        self.config = config

        self.encoder = Emu3VQVAEEncoder(config)
        self.decoder = Emu3VQVAEDecoder(config)
        self.quantize = Emu3VQVAEVectorQuantizer(config)
        self.vision_spatial_factor = 2 ** (len(config.channel_multiplier) - 1)

        self.quant_conv = Emu3VQVAEConv3d(
            config.latent_channels, config.embed_dim, kernel_size=(3, 1, 1), stride=(1, 1, 1)
        )
        self.post_quant_conv = Emu3VQVAEConv3d(
            config.embed_dim, config.latent_channels, kernel_size=(3, 1, 1), stride=(1, 1, 1)
        )
        self.spatial_scale_factor = 2 ** (len(config.channel_multiplier) - 1)
        self.eval()  # Emu3's VQ model is frozen

        self.post_init()

    def encode(self, pixel_values: torch.Tensor, image_sizes: torch.Tensor):
        is_image = pixel_values.ndim == 4
        if is_image:
            temporal = self.config.temporal_downsample_factor
            batch_size, channels, height, width = pixel_values.shape
            pixel_values = pixel_values.unsqueeze(1).repeat(1, temporal, 1, 1, 1)
        else:
            batch_size, temporal, channels, height, width = pixel_values.shape

        hidden_states = self.encoder(pixel_values)

        # b t c h w -> b c t h w
        hidden_states = hidden_states.permute(0, 2, 1, 3, 4)
        hidden_states = self.quant_conv(hidden_states)

        # b c t h w -> b t c h w
        hidden_states = hidden_states.permute(0, 2, 1, 3, 4)
        codes = self.quantize(hidden_states)

        image_tokens = codes.squeeze(1) if is_image else codes

        image_tokens = [
            single_image[: int(size[0] / self.vision_spatial_factor), : int(size[1] / self.vision_spatial_factor)]
            for single_image, size in zip(image_tokens, image_sizes)
        ]

        return image_tokens

    def decode(self, hidden_states: torch.Tensor):
        is_image = hidden_states.ndim == 3
        if is_image:
            hidden_states = hidden_states.unsqueeze(1)

        batch_size, temporal, height, width = hidden_states.shape
        quant = self.quantize.embedding(hidden_states.flatten())

        channels = quant.shape[-1]
        quant = quant.view(batch_size, temporal, height, width, channels).permute(0, 4, 1, 2, 3).contiguous()
        post_quant = self.post_quant_conv(quant)

        quant = quant.permute(0, 2, 1, 3, 4)
        post_quant = post_quant.permute(0, 2, 1, 3, 4)

        video = self.decoder(post_quant, quant)
        video = video.reshape(
            batch_size,
            temporal * self.config.temporal_downsample_factor,
            self.config.out_channels,
            height * self.spatial_scale_factor,
            width * self.spatial_scale_factor,
        )
        return video[:, 0] if is_image else video


class Emu3ImageVocabularyMapping:
    """
    A class for mapping discrete image tokens from VQGAN to BPE tokens.
    """

    def __init__(self, vocab_map):
        self.vocab_map = vocab_map
        self.eol_token_id = vocab_map.get("<|extra_200|>")
        self.image_token_id = vocab_map.get("<image>")

    @cached_property
    def image_tokens(self):
        return sorted([val for name, val in self.vocab_map.items() if name.startswith("<|visual token")])

    @cached_property
    def image_tokens_str(self):
        return sorted([name for name, val in self.vocab_map.items() if name.startswith("<|visual token")])

    @cached_property
    def img2bpe(self):
        return {int(token[-8:-2]): self.vocab_map[token] for token in self.image_tokens_str}

    @cached_property
    def bpe2img(self):
        return {v: k for k, v in self.img2bpe.items()}

    @cached_property
    def bpe2img_mapping_tensor(self):
        mapping = torch.zeros(max(self.bpe2img.keys()) + 1, dtype=torch.int)
        for k, v in self.bpe2img.items():
            mapping[k] = v
        return mapping

    @cached_property
    def img2bpe_mapping_tensor(self):
        mapping = torch.zeros(max(self.img2bpe.keys()) + 1, dtype=torch.int)
        for k, v in self.img2bpe.items():
            mapping[k] = v
        return mapping

    def convert_img2bpe(self, img_batch: List[torch.Tensor]) -> torch.Tensor:
        device = img_batch.device
        eol_row = torch.ones((img_batch.shape[0], 1), dtype=torch.int) * self.eol_token_id
        img_tokens = self.img2bpe_mapping_tensor[img_batch.to("cpu")]
        img_tokens = torch.cat([img_tokens, eol_row], dim=-1)
        return img_tokens.to(device)

    def convert_bpe2img(self, img_batch: torch.Tensor) -> torch.Tensor:
        device = img_batch.device
        img_batch = img_batch[..., :-1]  # remove last row of EOL tokens
        img_tokens = self.bpe2img_mapping_tensor[img_batch.to("cpu")]
        return img_tokens.to(device)


EMU3_START_DOCSTRING = r"""
    This model inherits from [`PreTrainedModel`]. Check the superclass documentation for the generic methods the
    library implements for all its model (such as downloading or saving, resizing the input embeddings, pruning heads
    etc.)

    This model is also a PyTorch [torch.nn.Module](https://pytorch.org/docs/stable/nn.html#torch.nn.Module) subclass.
    Use it as a regular PyTorch Module and refer to the PyTorch documentation for all matter related to general usage
    and behavior.

    Parameters:
        config ([`Emu3Config`]):
            Model configuration class with all the parameters of the model. Initializing with a config file does not
            load the weights associated with the model, only the configuration. Check out the
            [`~PreTrainedModel.from_pretrained`] method to load the model weights.
"""


@add_start_docstrings(
    "The bare Emu3 Model outputting raw hidden-states without any specific head on top.",
    EMU3_START_DOCSTRING,
)
class Emu3PreTrainedModel(ChameleonPreTrainedModel, Emu3VQVAE):
    _no_split_modules = [
        "Emu3DecoderLayer",
    ]

    def _init_weights(self, module):
        std = self.config.get_text_config().initializer_range
        if isinstance(module, Emu3VQVAE):
            module.apply(module._init_weights)
        elif isinstance(module, (nn.Linear, nn.Conv2d)):
            module.weight.data.normal_(mean=0.0, std=std)
            if module.bias is not None:
                module.bias.data.zero_()
        elif isinstance(module, nn.Embedding):
            module.weight.data.normal_(mean=0.0, std=std)
            if module.padding_idx is not None:
                module.weight.data[module.padding_idx].zero_()


EMU3_TEXT_INPUTS_DOCSTRING = r"""
    Args:
        input_ids (`torch.LongTensor` of shape `(batch_size, sequence_length)`):
            Indices of input sequence tokens in the vocabulary. Padding will be ignored by default should you provide
            it.

            Indices can be obtained using [`AutoTokenizer`]. See [`PreTrainedTokenizer.encode`] and
            [`PreTrainedTokenizer.__call__`] for details.

            [What are input IDs?](../glossary#input-ids)
        attention_mask (`torch.Tensor` of shape `(batch_size, sequence_length)`, *optional*):
            Mask to avoid performing attention on padding token indices. Mask values selected in `[0, 1]`:

            - 1 for tokens that are **not masked**,
            - 0 for tokens that are **masked**.

            [What are attention masks?](../glossary#attention-mask)

            Indices can be obtained using [`AutoTokenizer`]. See [`PreTrainedTokenizer.encode`] and
            [`PreTrainedTokenizer.__call__`] for details.

            If `past_key_values` is used, optionally only the last `input_ids` have to be input (see
            `past_key_values`).

            If you want to change padding behavior, you should read [`modeling_opt._prepare_decoder_attention_mask`]
            and modify to your needs. See diagram 1 in [the paper](https://arxiv.org/abs/1910.13461) for more
            information on the default strategy.

            - 1 indicates the head is **not masked**,
            - 0 indicates the head is **masked**.
        position_ids (`torch.LongTensor` of shape `(batch_size, sequence_length)`, *optional*):
            Indices of positions of each input sequence tokens in the position embeddings. Selected in the range `[0,
            config.n_positions - 1]`.

            [What are position IDs?](../glossary#position-ids)
        past_key_values (`Cache`, *optional*):
            Pre-computed hidden-states (key and values in the self-attention blocks and in the cross-attention
            blocks) that can be used to speed up sequential decoding. This typically consists in the `past_key_values`
            returned by the model at a previous stage of decoding, when `use_cache=True` or `config.use_cache=True`.

            Has to be an instance of [`~cache_utils.Cache`] instance, see our
            [kv cache guide](https://huggingface.co/docs/transformers/en/kv_cache).

            The model will output the same cache type that is fed as input. If no `past_key_values` are passed, the
            legacy cache format will be returned.

            If `past_key_values` are used, the user can optionally input only the last `input_ids` (those that don't
            have their past key value states given to this model) of shape `(batch_size, 1)` instead of all `input_ids`
            of shape `(batch_size, sequence_length)`.
        inputs_embeds (`torch.FloatTensor` of shape `(batch_size, sequence_length, hidden_size)`, *optional*):
            Optionally, instead of passing `input_ids` you can choose to directly pass an embedded representation. This
            is useful if you want more control over how to convert `input_ids` indices into associated vectors than the
            model's internal embedding lookup matrix.
        use_cache (`bool`, *optional*):
            If set to `True`, `past_key_values` key value states are returned and can be used to speed up decoding (see
            `past_key_values`).
        output_attentions (`bool`, *optional*):
            Whether or not to return the attentions tensors of all attention layers. See `attentions` under returned
            tensors for more detail.
        output_hidden_states (`bool`, *optional*):
            Whether or not to return the hidden states of all layers. See `hidden_states` under returned tensors for
            more detail.
        return_dict (`bool`, *optional*):
            Whether or not to return a [`~utils.ModelOutput`] instead of a plain tuple.
        cache_position (`torch.LongTensor` of shape `(sequence_length)`, *optional*):
            Indices depicting the position of the input sequence tokens in the sequence. Contrarily to `position_ids`,
            this tensor is not affected by padding. It is used to update the cache in the correct position and to infer
            the complete sequence length.
"""


EMU3_INPUTS_DOCSTRING = r"""
    Args:
        input_ids (`torch.LongTensor` of shape `(batch_size, sequence_length)`):
            Indices of input sequence tokens in the vocabulary. Padding will be ignored by default should you provide
            it.

            Indices can be obtained using [`AutoTokenizer`]. See [`PreTrainedTokenizer.encode`] and
            [`PreTrainedTokenizer.__call__`] for details.

            [What are input IDs?](../glossary#input-ids)
        pixel_values (`torch.FloatTensor` of shape `(batch_size, max_num_images, max_num_tiles, channels, image_size, image_size)):
            The tensors corresponding to the input images. Pixel values can be obtained using
            [`AutoImageProcessor`]. See [`Emu3ImageProcessor.__call__`] for details ([]`Emu3Processor`] uses
            [`Emu3ImageProcessor`] for processing images).
        image_sizes (`torch.LongTensor` of shape `(batch_size, 2)`):
                The sizes of the images in the batch, being (height, width) for each image. Image sizes can be obtained using
            [`AutoImageProcessor`]. See [`Emu3ImageProcessor.__call__`] for details ([]`Emu3Processor`] uses
            [`Emu3ImageProcessor`] for processing images).
        attention_mask (`torch.Tensor` of shape `(batch_size, sequence_length)`, *optional*):
            Mask to avoid performing attention on padding token indices. Mask values selected in `[0, 1]`:

            - 1 for tokens that are **not masked**,
            - 0 for tokens that are **masked**.

            [What are attention masks?](../glossary#attention-mask)

            Indices can be obtained using [`AutoTokenizer`]. See [`PreTrainedTokenizer.encode`] and
            [`PreTrainedTokenizer.__call__`] for details.

            If `past_key_values` is used, optionally only the last `input_ids` have to be input (see
            `past_key_values`).

            If you want to change padding behavior, you should read [`modeling_opt._prepare_decoder_attention_mask`]
            and modify to your needs. See diagram 1 in [the paper](https://arxiv.org/abs/1910.13461) for more
            information on the default strategy.

            - 1 indicates the head is **not masked**,
            - 0 indicates the head is **masked**.
        position_ids (`torch.LongTensor` of shape `(batch_size, sequence_length)`, *optional*):
            Indices of positions of each input sequence tokens in the position embeddings. Selected in the range `[0,
            config.n_positions - 1]`.

            [What are position IDs?](../glossary#position-ids)
        past_key_values (`Cache` or `tuple(tuple(torch.FloatTensor))`, *optional*):
            Pre-computed hidden-states (key and values in the self-attention blocks and in the cross-attention
            blocks) that can be used to speed up sequential decoding. This typically consists in the `past_key_values`
            returned by the model at a previous stage of decoding, when `use_cache=True` or `config.use_cache=True`.

            Has to be an instance of [`~cache_utils.Cache`] instance, see our
            [kv cache guide](https://huggingface.co/docs/transformers/en/kv_cache).

            The model will output the same cache format that is fed as input. If no `past_key_values` are passed, the
            legacy cache format will be returned.

            If `past_key_values` are used, the user can optionally input only the last `input_ids` (those that don't
            have their past key value states given to this model) of shape `(batch_size, 1)` instead of all `input_ids`
            of shape `(batch_size, sequence_length)`.
        inputs_embeds (`torch.FloatTensor` of shape `(batch_size, sequence_length, hidden_size)`, *optional*):
            Optionally, instead of passing `input_ids` you can choose to directly pass an embedded representation. This
            is useful if you want more control over how to convert `input_ids` indices into associated vectors than the
            model's internal embedding lookup matrix.
        use_cache (`bool`, *optional*):
            If set to `True`, `past_key_values` key value states are returned and can be used to speed up decoding (see
            `past_key_values`).
        output_attentions (`bool`, *optional*):
            Whether or not to return the attentions tensors of all attention layers. See `attentions` under returned
            tensors for more detail.
        output_hidden_states (`bool`, *optional*):
            Whether or not to return the hidden states of all layers. See `hidden_states` under returned tensors for
            more detail.
        return_dict (`bool`, *optional*):
            Whether or not to return a [`~utils.ModelOutput`] instead of a plain tuple.
        cache_position (`torch.LongTensor` of shape `(sequence_length)`, *optional*):
            Indices depicting the position of the input sequence tokens in the sequence. Contrarily to `position_ids`,
            this tensor is not affected by padding. It is used to update the cache in the correct position and to infer
            the complete sequence length.
"""


@add_start_docstrings(
    "The Emu3 Text Model which consists of transformer with self attention layers.",
    EMU3_START_DOCSTRING,
)
class Emu3TextModel(Emu3PreTrainedModel):
    config_class = Emu3TextConfig

    def __init__(self, config: Emu3TextConfig):
        super().__init__(config)
        self.padding_idx = config.pad_token_id
        self.vocab_size = config.vocab_size

        self.embed_tokens = nn.Embedding(config.vocab_size, config.hidden_size, self.padding_idx)
        self.layers = nn.ModuleList(
            [Emu3DecoderLayer(config, layer_idx) for layer_idx in range(config.num_hidden_layers)]
        )
        self.norm = Emu3RMSNorm(config.hidden_size, eps=config.rms_norm_eps)
        self.rotary_emb = Emu3RotaryEmbedding(config=config)
        self.gradient_checkpointing = False

        # Initialize weights and apply final processing
        self.post_init()

    def get_input_embeddings(self):
        return self.embed_tokens

    def set_input_embeddings(self, value):
        self.embed_tokens = value

    @add_start_docstrings_to_model_forward(EMU3_TEXT_INPUTS_DOCSTRING)
    def forward(
        self,
        input_ids: torch.LongTensor = None,
        attention_mask: Optional[torch.Tensor] = None,
        position_ids: Optional[torch.LongTensor] = None,
        past_key_values: Optional[Cache] = None,
        inputs_embeds: Optional[torch.FloatTensor] = None,
        use_cache: Optional[bool] = None,
        output_attentions: Optional[bool] = None,
        output_hidden_states: Optional[bool] = None,
        return_dict: Optional[bool] = None,
        cache_position: Optional[torch.LongTensor] = None,
    ) -> Union[Tuple, BaseModelOutputWithPast]:
        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )
        use_cache = use_cache if use_cache is not None else self.config.use_cache
        return_dict = return_dict if return_dict is not None else self.config.use_return_dict

        if self.gradient_checkpointing and self.training and use_cache:
            logger.warning_once(
                "`use_cache=True` is incompatible with gradient checkpointing. Setting `use_cache=False`."
            )
            use_cache = False

        if inputs_embeds is None:
            inputs_embeds = self.embed_tokens(input_ids)

        if cache_position is None:
            past_seen_tokens = past_key_values.get_seq_length() if past_key_values is not None else 0
            cache_position = torch.arange(
                past_seen_tokens, past_seen_tokens + inputs_embeds.shape[1], device=inputs_embeds.device
            )

        if position_ids is None:
            position_ids = cache_position.unsqueeze(0)

        causal_mask = self._update_causal_mask(
            attention_mask, inputs_embeds, cache_position, past_key_values, output_attentions
        )

        # embed positions
        hidden_states = inputs_embeds

        # create position embeddings to be shared across the decoder layers
        position_embeddings = self.rotary_emb(hidden_states, position_ids)

        # decoder layers
        all_hidden_states = () if output_hidden_states else None
        all_self_attns = () if output_attentions else None
        next_decoder_cache = None

        for decoder_layer in self.layers:
            if output_hidden_states:
                all_hidden_states += (hidden_states,)

            if self.gradient_checkpointing and self.training:
                layer_outputs = self._gradient_checkpointing_func(
                    decoder_layer.__call__,
                    hidden_states,
                    causal_mask,
                    position_ids,
                    past_key_values,
                    output_attentions,
                    use_cache,
                    cache_position,
                    position_embeddings,
                )
            else:
                layer_outputs = decoder_layer(
                    hidden_states,
                    attention_mask=causal_mask,
                    position_ids=position_ids,
                    past_key_value=past_key_values,
                    output_attentions=output_attentions,
                    use_cache=use_cache,
                    cache_position=cache_position,
                    position_embeddings=position_embeddings,
                )

            hidden_states = layer_outputs[0]

            if use_cache:
                next_decoder_cache = layer_outputs[2 if output_attentions else 1]

            if output_attentions:
                all_self_attns += (layer_outputs[1],)

        hidden_states = self.norm(hidden_states)

        # add hidden states from the last decoder layer
        if output_hidden_states:
            all_hidden_states += (hidden_states,)

        next_cache = None
        if use_cache:
            next_cache = next_decoder_cache

        if not return_dict:
            return tuple(v for v in [hidden_states, next_cache, all_hidden_states, all_self_attns] if v is not None)

        return BaseModelOutputWithPast(
            last_hidden_state=hidden_states,
            past_key_values=next_cache,
            hidden_states=all_hidden_states,
            attentions=all_self_attns,
        )

    def _update_causal_mask(
        self,
        attention_mask: torch.Tensor,
        input_tensor: torch.Tensor,
        cache_position: torch.Tensor,
        past_key_values: Cache,
        output_attentions: bool,
    ):
        if self.config._attn_implementation == "flash_attention_2":
            if attention_mask is not None and 0.0 in attention_mask:
                return attention_mask
            return None

        # For SDPA, when possible, we will rely on its `is_causal` argument instead of its `attn_mask` argument, in
        # order to dispatch on Flash Attention 2. This feature is not compatible with static cache, as SDPA will fail
        # to infer the attention mask.
        past_seen_tokens = past_key_values.get_seq_length() if past_key_values is not None else 0
        using_static_cache = isinstance(past_key_values, StaticCache)

        # When output attentions is True, sdpa implementation's forward method calls the eager implementation's forward
        if self.config._attn_implementation == "sdpa" and not using_static_cache and not output_attentions:
            if AttentionMaskConverter._ignore_causal_mask_sdpa(
                attention_mask,
                inputs_embeds=input_tensor,
                past_key_values_length=past_seen_tokens,
                is_training=self.training,
            ):
                return None

        dtype, device = input_tensor.dtype, input_tensor.device
        sequence_length = input_tensor.shape[1]
        if using_static_cache:
            target_length = past_key_values.get_max_cache_shape()
        else:
            target_length = (
                attention_mask.shape[-1]
                if isinstance(attention_mask, torch.Tensor)
                else past_seen_tokens + sequence_length + 1
            )

        # In case the provided `attention` mask is 2D, we generate a causal mask here (4D).
        causal_mask = self._prepare_4d_causal_attention_mask_with_cache_position(
            attention_mask,
            sequence_length=sequence_length,
            target_length=target_length,
            dtype=dtype,
            device=device,
            cache_position=cache_position,
            batch_size=input_tensor.shape[0],
        )

        if (
            self.config._attn_implementation == "sdpa"
            and attention_mask is not None
            and attention_mask.device.type == "cuda"
            and not output_attentions
        ):
            # Attend to all tokens in fully masked rows in the causal_mask, for example the relevant first rows when
            # using left padding. This is required by F.scaled_dot_product_attention memory-efficient attention path.
            # Details: https://github.com/pytorch/pytorch/issues/110213
            min_dtype = torch.finfo(dtype).min
            causal_mask = AttentionMaskConverter._unmask_unattended(causal_mask, min_dtype)

        return causal_mask

    @staticmethod
    def _prepare_4d_causal_attention_mask_with_cache_position(
        attention_mask: torch.Tensor,
        sequence_length: int,
        target_length: int,
        dtype: torch.dtype,
        device: torch.device,
        cache_position: torch.Tensor,
        batch_size: int,
        **kwargs,
    ):
        """
        Creates a causal 4D mask of shape `(batch_size, 1, query_length, key_value_length)` from a 2D mask of shape
        `(batch_size, key_value_length)`, or if the input `attention_mask` is already 4D, do nothing.

        Args:
            attention_mask (`torch.Tensor`):
                A 2D attention mask of shape `(batch_size, key_value_length)` or a 4D attention mask of shape
                `(batch_size, 1, query_length, key_value_length)`.
            sequence_length (`int`):
                The sequence length being processed.
            target_length (`int`):
                The target length: when generating with static cache, the mask should be as long as the static cache,
                to account for the 0 padding, the part of the cache that is not filled yet.
            dtype (`torch.dtype`):
                The dtype to use for the 4D attention mask.
            device (`torch.device`):
                The device to plcae the 4D attention mask on.
            cache_position (`torch.Tensor`):
                Indices depicting the position of the input sequence tokens in the sequence.
            batch_size (`torch.Tensor`):
                Batch size.
        """
        if attention_mask is not None and attention_mask.dim() == 4:
            # In this case we assume that the mask comes already in inverted form and requires no inversion or slicing.
            causal_mask = attention_mask
        else:
            min_dtype = torch.finfo(dtype).min
            causal_mask = torch.full(
                (sequence_length, target_length), fill_value=min_dtype, dtype=dtype, device=device
            )
            if sequence_length != 1:
                causal_mask = torch.triu(causal_mask, diagonal=1)
            causal_mask *= torch.arange(target_length, device=device) > cache_position.reshape(-1, 1)
            causal_mask = causal_mask[None, None, :, :].expand(batch_size, 1, -1, -1)
            if attention_mask is not None:
                causal_mask = causal_mask.clone()  # copy to contiguous memory for in-place edit
                mask_length = attention_mask.shape[-1]
                padding_mask = causal_mask[:, :, :, :mask_length] + attention_mask[:, None, None, :]
                padding_mask = padding_mask == 0
                causal_mask[:, :, :, :mask_length] = causal_mask[:, :, :, :mask_length].masked_fill(
                    padding_mask, min_dtype
                )

        return causal_mask


@add_start_docstrings(
    "Emu3 Model with a head on top used for outputting logits for next token prediction.",
    EMU3_START_DOCSTRING,
)
class Emu3ForCausalLM(Emu3PreTrainedModel, GenerationMixin):
    config_class = Emu3TextConfig

    def __init__(self, config):
        super().__init__(config)
        self.model = Emu3TextModel(config)
        self.vocab_size = config.vocab_size
        self.lm_head = nn.Linear(config.hidden_size, config.vocab_size, bias=False)

        # Initialize weights and apply final processing
        self.post_init()

    @add_start_docstrings_to_model_forward(EMU3_TEXT_INPUTS_DOCSTRING)
    def forward(
        self,
        input_ids: torch.LongTensor = None,
        attention_mask: Optional[torch.Tensor] = None,
        position_ids: Optional[torch.LongTensor] = None,
        past_key_values: Optional[Cache] = None,
        inputs_embeds: Optional[torch.FloatTensor] = None,
        labels: Optional[torch.LongTensor] = None,
        use_cache: Optional[bool] = None,
        output_attentions: Optional[bool] = None,
        output_hidden_states: Optional[bool] = None,
        return_dict: Optional[bool] = None,
        cache_position: Optional[torch.LongTensor] = None,
        num_logits_to_keep: int = 0,
    ) -> Union[Tuple, CausalLMOutputWithPast]:
        r"""
        Args:
            labels (`torch.LongTensor` of shape `(batch_size, sequence_length)`, *optional*):
                Labels for computing the masked language modeling loss. Indices should either be in `[0, ...,
                config.vocab_size]` or -100 (see `input_ids` docstring). Tokens with indices set to `-100` are ignored
                (masked), the loss is only computed for the tokens with labels in `[0, ..., config.vocab_size]`.

            num_logits_to_keep (`int`, *optional*):
                Calculate logits for the last `num_logits_to_keep` tokens. If `0`, calculate logits for all
                `input_ids` (special case). Only last token logits are needed for generation, and calculating them only for that
                token can save memory, which becomes pretty significant for long sequences or large vocabulary size.

        Returns:

        Example:

        ```python
        >>> from transformers import Emu3Processor, Emu3ForConditionalGeneration
        >>> import torch
        >>> import requests
        >>> from PIL import Image

        >>> model = Emu3ForCausalLM.from_pretrained("Emu3-community/Emu3-Chat-hf", torch_dtype=torch.bfloat16)
        >>> processor = Emu3Processor.from_pretrained("Emu3-community/Emu3-Chat-hf")

        >>> inputs = processor(text=["Can you write me a poem about winter."], return_tensors="pt").to(model.device)

        >>> generated_ids = model.generate(**inputs, max_new_tokens=100, do_sample=False)
        >>> processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        ```"""
        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )
        return_dict = return_dict if return_dict is not None else self.config.use_return_dict

        # decoder outputs consists of (dec_features, layer_state, dec_hidden, dec_attn)
        outputs = self.model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            position_ids=position_ids,
            past_key_values=past_key_values,
            inputs_embeds=inputs_embeds,
            use_cache=use_cache,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
            cache_position=cache_position,
        )

        hidden_states = outputs[0]
        if self.config.pretraining_tp > 1:
            lm_head_slices = self.lm_head.weight.split(self.vocab_size // self.config.pretraining_tp, dim=0)
            logits = [F.linear(hidden_states, lm_head_slices[i]) for i in range(self.config.pretraining_tp)]
            logits = torch.cat(logits, dim=-1)
        else:
            # Only compute necessary logits, and do not upcast them to float if we are not computing the loss
            logits = self.lm_head(hidden_states[:, -num_logits_to_keep:, :])

        loss = None
        if labels is not None:
            loss = self.loss_function(logits=logits, labels=labels, vocab_size=self.config.vocab_size)

        if not return_dict:
            output = (logits,) + outputs[1:]
            return (loss,) + output if loss is not None else output

        return CausalLMOutputWithPast(
            loss=loss,
            logits=logits,
            past_key_values=outputs.past_key_values,
            hidden_states=outputs.hidden_states,
            attentions=outputs.attentions,
        )


@add_start_docstrings(
    """The Emu3 model which consists of a VQ-VAE and a language model.""",
    EMU3_START_DOCSTRING,
)
class Emu3ForConditionalGeneration(Emu3PreTrainedModel, GenerationMixin):
    def __init__(self, config):
        super().__init__(config)
        self.text_model = Emu3ForCausalLM._from_config(config.text_config)
        self.vqmodel = Emu3VQVAE(config.vq_config)
        self.vocabulary_mapping = Emu3ImageVocabularyMapping(config.vocabulary_map)

        # Initialize weights and apply final processing
        self.post_init()

    def get_input_embeddings(self):
        return self.text_model.get_input_embeddings()

    def set_input_embeddings(self, value):
        self.text_model.set_input_embeddings(value)

    def get_image_tokens(self, pixel_values: torch.FloatTensor, image_sizes: torch.LongTensor):
        """
        Tokenizes images into discrete tokens with VQGAN module. Converts
        obtained image tokens into BPE tokens and wraps with "boi" and "eoi"
        special tokens.

        Args:
            pixel_values (`torch.FloatTensor` of shape `(batch_size, num_channels, image_size, image_size)`):
                The tensors corresponding to the input images.
            image_sizes (`torch.LongTensor` of shape `(batch_size, 2)`):
                The sizes of the images in the batch, being (height, width) for each image.
        """
        image_tokens_list = self.vqmodel.encode(pixel_values, image_sizes)
        bpe_tokens_list = [self.vocabulary_mapping.convert_img2bpe(tokens).flatten() for tokens in image_tokens_list]
        bpe_tokens = torch.cat(bpe_tokens_list)
        return bpe_tokens

    @torch.no_grad
    def decode_image_tokens(self, image_tokens: torch.LongTensor, height: int, width: int):
        """
        Decodes generated image tokens from language model to continuous pixel values
        with VQGAN module via upsampling.

        Args:
            image_tokens (`torch.LongTensor` of shape `(batch_size, num_of_tokens)`):
                The tensors corresponding to the input images.
            height (`int`):
                Height of the generated image before upsampling.
            width (`int`):
                Width of the generated image before upsampling.
        """
        sequences = image_tokens[:, :-3].view(-1, height, width + 1)
        image_tokens = self.vocabulary_mapping.convert_bpe2img(sequences)
        image = self.vqmodel.decode(image_tokens)
        return image

    @add_start_docstrings_to_model_forward(EMU3_INPUTS_DOCSTRING)
    def forward(
        self,
        input_ids: torch.LongTensor = None,
        pixel_values: torch.FloatTensor = None,
        image_sizes: torch.Tensor = None,
        attention_mask: Optional[torch.Tensor] = None,
        position_ids: Optional[torch.LongTensor] = None,
        past_key_values: Optional[Cache] = None,
        inputs_embeds: Optional[torch.FloatTensor] = None,
        labels: Optional[torch.LongTensor] = None,
        use_cache: Optional[bool] = None,
        output_attentions: Optional[bool] = None,
        output_hidden_states: Optional[bool] = None,
        return_dict: Optional[bool] = None,
        cache_position: Optional[torch.LongTensor] = None,
        num_logits_to_keep: int = 0,
    ) -> Union[Tuple, CausalLMOutputWithPast]:
        r"""
        Args:
            labels (`torch.LongTensor` of shape `(batch_size, sequence_length)`, *optional*):
                Labels for computing the masked language modeling loss. Indices should either be in `[0, ...,
                config.vocab_size]` or -100 (see `input_ids` docstring). Tokens with indices set to `-100` are ignored
                (masked), the loss is only computed for the tokens with labels in `[0, ..., config.vocab_size]`.

            num_logits_to_keep (`int`, *optional*):
                Calculate logits for the last `num_logits_to_keep` tokens. If `0`, calculate logits for all
                `input_ids` (special case). Only last token logits are needed for generation, and calculating them only for that
                token can save memory, which becomes pretty significant for long sequences or large vocabulary size.

        Returns:

        Example:

        ```python
        >>> from transformers import Emu3Processor, Emu3ForConditionalGeneration
        >>> import torch
        >>> import requests
        >>> from PIL import Image

        >>> model = Emu3ForConditionalGeneration.from_pretrained("Emu3-community/Emu3-Chat-hf", torch_dtype=torch.bfloat16)
        >>> processor = Emu3Processor.from_pretrained("Emu3-community/Emu3-Chat-hf")

        >>> conversation = [
        ...     {
        ...     "role": "system",
        ...     "content": [
        ...         {"type": "text", "text": "You are a helpful assistant."},
        ...         ],
        ...     },
        ...     {
        ...     "role": "user",
        ...     "content": [
        ...         {"type": "image"},
        ...         {"type": "text", "text": "Please describe the image."},
        ...         ],
        ...     },
        ... ]

        >>> prompt = processor.apply_chat_template(conversation, add_generation_prompt=True)
        >>> image = Image.open(requests.get("https://www.ilankelman.org/stopsigns/australia.jpg", stream=True).raw)

        >>> inputs = processor(images=[image], text=[prompt], return_tensors="pt").to(model.device, torch.bfloat16)

        >>> generated_ids = model.generate(**inputs, max_new_tokens=100, do_sample=False)
        >>> processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        ```"""
        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )
        return_dict = return_dict if return_dict is not None else self.config.use_return_dict

        if (input_ids is None) ^ (inputs_embeds is not None):
            raise ValueError(
                "You cannot specify both input_ids and inputs_embeds at the same time, and must specify either one"
            )

        if pixel_values is not None and inputs_embeds is not None:
            raise ValueError(
                "You cannot specify both pixel_values and inputs_embeds at the same time, and must specify either one"
            )

        if pixel_values is not None:
            image_tokens = self.get_image_tokens(pixel_values, image_sizes)
            special_image_mask = input_ids == self.vocabulary_mapping.image_token_id
            image_tokens = image_tokens.to(input_ids.device, input_ids.dtype)
            input_ids = input_ids.masked_scatter(special_image_mask, image_tokens)

        # decoder outputs consists of (dec_features, layer_state, dec_hidden, dec_attn)
        outputs = self.text_model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            position_ids=position_ids,
            past_key_values=past_key_values,
            inputs_embeds=inputs_embeds,
            use_cache=use_cache,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
            cache_position=cache_position,
            num_logits_to_keep=num_logits_to_keep,
        )

        return outputs

    def prepare_inputs_for_generation(
        self,
        input_ids,
        pixel_values=None,
        past_key_values=None,
        image_sizes=None,
        attention_mask=None,
        inputs_embeds=None,
        cache_position=None,
        position_ids=None,
        use_cache=True,
        **kwargs,
    ):
        # If we have cache: let's slice `input_ids` through `cache_position`, to keep only the unprocessed tokens
        # Exception 1: when passing input_embeds, input_ids may be missing entries
        # Exception 2: some generation methods do special slicing of input_ids, so we don't need to do it here
        if past_key_values is not None:
            if inputs_embeds is not None:  # Exception 1
                input_ids = input_ids[:, -cache_position.shape[0] :]
            elif input_ids.shape[1] != cache_position.shape[0]:  # Default case (the "else", a no op, is Exception 2)
                input_ids = input_ids[:, cache_position]

        if attention_mask is not None and position_ids is None:
            # create position_ids on the fly for batch generation
            position_ids = attention_mask.long().cumsum(-1) - 1
            position_ids.masked_fill_(attention_mask == 0, 1)
            if past_key_values:
                position_ids = position_ids[:, -input_ids.shape[1] :]

        # if `inputs_embeds` are passed, we only want to use them in the 1st generation step
        if inputs_embeds is not None and cache_position[0] == 0:
            model_inputs = {"inputs_embeds": inputs_embeds, "input_ids": None}
        else:
            model_inputs = {"input_ids": input_ids.clone(memory_format=torch.contiguous_format), "inputs_embeds": None}

        # 6. Create 4D attention mask is we are using a `StaticCache` (important for performant compiled forward pass)
        if isinstance(past_key_values, StaticCache) and attention_mask.ndim == 2:
            if model_inputs["inputs_embeds"] is not None:
                batch_size, sequence_length, _ = model_inputs["inputs_embeds"].shape
                device = model_inputs["inputs_embeds"].device
            else:
                batch_size, sequence_length = model_inputs["input_ids"].shape
                device = model_inputs["input_ids"].device

            attention_mask = self.text_model.model._prepare_4d_causal_attention_mask_with_cache_position(
                attention_mask,
                sequence_length=sequence_length,
                target_length=past_key_values.get_max_cache_shape(),
                dtype=self.dtype,
                device=device,
                cache_position=cache_position,
                batch_size=batch_size,
                config=self.config,
                past_key_values=past_key_values,
            )

        if cache_position[0] == 0:
            # If we're in cached decoding stage, pixel values should be `None` because input ids do not contain special image token anymore
            # Otherwise we need pixel values to be passed to model
            model_inputs["pixel_values"] = pixel_values
            model_inputs["image_sizes"] = image_sizes

        model_inputs.update(
            {
                "position_ids": position_ids,
                "cache_position": cache_position,
                "past_key_values": past_key_values,
                "use_cache": use_cache,
                "attention_mask": attention_mask,
            }
        )
        return model_inputs
