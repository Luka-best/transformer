# coding=utf-8
# Copyright 2021 The Eleuther AI and The Google Flax Team Authors and The HuggingFace Inc. team.
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

from functools import partial
from typing import Optional, Tuple

import flax.linen as nn
import jax
import jax.numpy as jnp
import numpy as np
from flax.core.frozen_dict import FrozenDict, freeze, unfreeze
from flax.linen import combine_masks, make_causal_mask
from flax.linen.attention import dot_product_attention_weights
from flax.traverse_util import flatten_dict, unflatten_dict
from jax import lax

from ...modeling_flax_utils import ACT2FN, FlaxPreTrainedModel
from ...utils import add_start_docstrings, add_start_docstrings_to_model_forward, logging
from .configuration_llama import LlamaConfig


logger = logging.get_logger(__name__)

_CONFIG_FOR_DOC = "LlamaConfig"


LLAMA_START_DOCSTRING = r"""

    This model inherits from [`FlaxPreTrainedModel`]. Check the superclass documentation for the generic methods the
    library implements for all its model (such as downloading or saving, resizing the input embeddings, pruning heads
    etc.)

    This model is also a Flax Linen
    [flax.nn.Module](https://flax.readthedocs.io/en/latest/_autosummary/flax.nn.module.html) subclass. Use it as a
    regular Flax Module and refer to the Flax documentation for all matter related to general usage and behavior.

    Finally, this model supports inherent JAX features such as:

    - [Just-In-Time (JIT) compilation](https://jax.readthedocs.io/en/latest/jax.html#just-in-time-compilation-jit)
    - [Automatic Differentiation](https://jax.readthedocs.io/en/latest/jax.html#automatic-differentiation)
    - [Vectorization](https://jax.readthedocs.io/en/latest/jax.html#vectorization-vmap)
    - [Parallelization](https://jax.readthedocs.io/en/latest/jax.html#parallelization-pmap)

    Parameters:
        config ([`LlamaConfig`]): Model configuration class with all the parameters of the model.
            Initializing with a config file does not load the weights associated with the model, only the
            configuration. Check out the [`~FlaxPreTrainedModel.from_pretrained`] method to load the model weights.
"""

LLAMA_INPUTS_DOCSTRING = r"""
    Args:
        input_ids (`numpy.ndarray` of shape `(batch_size, input_ids_length)`):
            Indices of input sequence tokens in the vocabulary. Padding will be ignored by default should you provide
            it.

            Indices can be obtained using [`AutoTokenizer`]. See [`PreTrainedTokenizer.encode`] and
            [`PreTrainedTokenizer.__call__`] for details.

            [What are input IDs?](../glossary#input-ids)
        attention_mask (`numpy.ndarray` of shape `(batch_size, sequence_length)`, *optional*):
            Mask to avoid performing attention on padding token indices. Mask values selected in `[0, 1]`:

            - 1 for tokens that are **not masked**,
            - 0 for tokens that are **masked**.

            [What are attention masks?](../glossary#attention-mask)

            Indices can be obtained using [`AutoTokenizer`]. See [`PreTrainedTokenizer.encode`] and
            [`PreTrainedTokenizer.__call__`] for details.

            If `past_key_values` is used, optionally only the last `decoder_input_ids` have to be input (see
            `past_key_values`).

            If you want to change padding behavior, you should read [`modeling_opt._prepare_decoder_attention_mask`]
            and modify to your needs. See diagram 1 in [the paper](https://arxiv.org/abs/1910.13461) for more
            information on the default strategy.

            - 1 indicates the head is **not masked**,
            - 0 indicates the head is **masked**.
        position_ids (`numpy.ndarray` of shape `(batch_size, sequence_length)`, *optional*):
            Indices of positions of each input sequence tokens in the position embeddings. Selected in the range `[0,
            config.n_positions - 1]`.

            [What are position IDs?](../glossary#position-ids)
        past_key_values (`Dict[str, np.ndarray]`, *optional*, returned by `init_cache` or when passing previous `past_key_values`):
            Dictionary of pre-computed hidden-states (key and values in the attention blocks) that can be used for fast
            auto-regressive decoding. Pre-computed key and value hidden-states are of shape *[batch_size, max_length]*.
        inputs_embeds (`np.array` of shape `(batch_size, sequence_length, hidden_size)`, *optional*):
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
"""


def create_sinusoidal_positions(num_pos, dim):
    inv_freq = 1.0 / (10000 ** (np.arange(0, dim, 2) / dim))
    freqs = np.einsum("i , j -> i j", np.arange(num_pos), inv_freq).astype("float32")

    emb = np.concatenate((freqs, freqs), axis=-1)
    out = np.concatenate((np.sin(emb)[:, None, :], np.cos(emb)[:, None, :]), axis=-1)
    return jnp.array(out[:, :, :num_pos])  # TODO: don't think slice is needed


def rotate_half(x):
    """Rotates half the hidden dims of the input."""
    rotate_half_tensor = jnp.concatenate((-x[..., x.shape[-1] // 2 :], x[..., : x.shape[-1] // 2]), axis=-1)
    return rotate_half_tensor


def apply_rotary_pos_emb(tensor, sincos):
    sin_pos, cos_pos = sincos
    return (tensor * cos_pos) + (rotate_half(tensor) * sin_pos)


class FlaxLlamaRMSNorm(nn.Module):
    eps: float = 1e-6

    @nn.compact
    def __call__(self, hidden_states):
        input_dtype = hidden_states.dtype
        variance = jnp.asarray(hidden_states, dtype=jnp.float32)
        variance = jnp.square(variance)
        variance = variance.mean(-1, keepdims=True)
        hidden_states = hidden_states * jax.lax.rsqrt(variance + self.eps)

        weight = self.param("weight", lambda _, shape: jnp.ones(shape), hidden_states.shape[-1])

        return jnp.asarray(weight * hidden_states, dtype=input_dtype)


class FlaxLlamaAttention(nn.Module):
    config: LlamaConfig
    dtype: jnp.dtype = jnp.float32
    causal: bool = True
    is_cross_attention: bool = False

    def setup(self):
        config = self.config
        self.embed_dim = config.hidden_size
        self.num_heads = config.num_attention_heads
        self.head_dim = self.embed_dim // self.num_heads

        dense = partial(
            nn.Dense,
            self.embed_dim,
            use_bias=False,
            dtype=self.dtype,
            kernel_init=jax.nn.initializers.normal(self.config.initializer_range),
        )

        self.q_proj, self.k_proj, self.v_proj = dense(), dense(), dense()
        self.o_proj = dense()

        self.causal_mask = make_causal_mask(jnp.ones((1, config.max_position_embeddings), dtype="bool"), dtype="bool")
        self.embed_positions = create_sinusoidal_positions(config.max_position_embeddings, self.head_dim)

    def _split_heads(self, hidden_states):
        return hidden_states.reshape(hidden_states.shape[:2] + (self.num_heads, self.head_dim))

    def _merge_heads(self, hidden_states):
        return hidden_states.reshape(hidden_states.shape[:2] + (self.embed_dim,))

    @nn.compact
    def _concatenate_to_cache(self, key, value, query, attention_mask):
        """
        This function takes projected key, value states from a single input token and concatenates the states to cached
        states from previous steps. This function is slighly adapted from the official Flax repository:
        https://github.com/google/flax/blob/491ce18759622506588784b4fca0e4bf05f8c8cd/flax/linen/attention.py#L252
        """
        # detect if we're initializing by absence of existing cache data.
        is_initialized = self.has_variable("cache", "cached_key")
        cached_key = self.variable("cache", "cached_key", jnp.zeros, key.shape, key.dtype)
        cached_value = self.variable("cache", "cached_value", jnp.zeros, value.shape, value.dtype)
        cache_index = self.variable("cache", "cache_index", lambda: jnp.array(0, dtype=jnp.int32))

        if is_initialized:
            *batch_dims, max_length, num_heads, depth_per_head = cached_key.value.shape
            # update key, value caches with our new 1d spatial slices
            cur_index = cache_index.value
            indices = (0,) * len(batch_dims) + (cur_index, 0, 0)
            key = lax.dynamic_update_slice(cached_key.value, key, indices)
            value = lax.dynamic_update_slice(cached_value.value, value, indices)
            cached_key.value = key
            cached_value.value = value
            num_updated_cache_vectors = query.shape[1]
            cache_index.value = cache_index.value + num_updated_cache_vectors
            # causal mask for cached decoder self-attention: our single query position should only attend to those key positions that have already been generated and cached, not the remaining zero elements.
            pad_mask = jnp.broadcast_to(
                jnp.arange(max_length) < cur_index + num_updated_cache_vectors,
                tuple(batch_dims) + (1, num_updated_cache_vectors, max_length),
            )
            attention_mask = combine_masks(pad_mask, attention_mask)
        return key, value, attention_mask

    def __call__(
        self,
        hidden_states,
        attention_mask,
        position_ids,
        deterministic: bool = True,
        init_cache: bool = False,
        output_attentions: bool = False,
    ):
        query = self.q_proj(hidden_states)
        key = self.k_proj(hidden_states)
        value = self.v_proj(hidden_states)

        query = self._split_heads(query)
        key = self._split_heads(key)
        value = self._split_heads(value)

        sincos = self.embed_positions[position_ids]
        sincos = jnp.split(sincos, 2, axis=-1)

        key = apply_rotary_pos_emb(key, sincos)
        query = apply_rotary_pos_emb(query, sincos)

        query_length, key_length = query.shape[1], key.shape[1]

        if self.has_variable("cache", "cached_key"):
            mask_shift = self.variables["cache"]["cache_index"]
            max_decoder_length = self.variables["cache"]["cached_key"].shape[1]
            causal_mask = lax.dynamic_slice(
                self.causal_mask, (0, 0, mask_shift, 0), (1, 1, query_length, max_decoder_length)
            )
        else:
            causal_mask = self.causal_mask[:, :, :query_length, :key_length]

        batch_size = hidden_states.shape[0]
        causal_mask = jnp.broadcast_to(causal_mask, (batch_size,) + causal_mask.shape[1:])

        attention_mask = jnp.broadcast_to(jnp.expand_dims(attention_mask, axis=(-3, -2)), causal_mask.shape)
        attention_mask = combine_masks(attention_mask, causal_mask)

        # During fast autoregressive decoding, we feed one position at a time,
        # and cache the keys and values step by step.
        if self.has_variable("cache", "cached_key") or init_cache:
            key, value, attention_mask = self._concatenate_to_cache(key, value, query, attention_mask)

        # transform boolean mask into float mask
        attention_bias = lax.select(
            attention_mask > 0,
            jnp.full(attention_mask.shape, 0.0).astype(self.dtype),
            jnp.full(attention_mask.shape, jnp.finfo(self.dtype).min).astype(self.dtype),
        )

        # usual dot product attention
        attn_weights = dot_product_attention_weights(
            query,
            key,
            bias=attention_bias,
            deterministic=deterministic,
            dtype=self.dtype,
        )

        attn_output = jnp.einsum("...hqk,...khd->...qhd", attn_weights, value)
        attn_output = self._merge_heads(attn_output)
        attn_output = self.o_proj(attn_output)

        outputs = (attn_output, attn_weights) if output_attentions else (attn_output,)
        return outputs


class FlaxLlamaMLP(nn.Module):
    config: LlamaConfig
    intermediate_size: int
    dtype: jnp.dtype = jnp.float32

    def setup(self):
        embed_dim = self.config.hidden_size
        jax.nn.initializers.normal(self.config.initializer_range)
        self.act = ACT2FN[self.config.hidden_act]

        self.gate_proj = nn.Dense(self.intermediate_size, use_bias=False)
        self.down_proj = nn.Dense(embed_dim, use_bias=False)
        self.up_proj = nn.Dense(self.intermediate_size, use_bias=False)

    def __call__(self, hidden_states):
        hidden_states = self.up_proj(hidden_states) * self.act(self.gate_proj(hidden_states))
        hidden_states = self.down_proj(hidden_states)
        return hidden_states


class FlaxLlamaDecoderLayer(nn.Module):
    config: LlamaConfig
    dtype: jnp.dtype = jnp.float32

    def setup(self):
        hidden_size = self.config.hidden_size
        inner_dim = self.config.intermediate_size if self.config.intermediate_size is not None else 4 * hidden_size

        self.input_layernorm = FlaxLlamaRMSNorm(eps=self.config.rms_norm_eps)
        self.self_attn = FlaxLlamaAttention(self.config, dtype=self.dtype)
        self.post_attention_layernorm = FlaxLlamaRMSNorm(eps=self.config.rms_norm_eps)
        self.mlp = FlaxLlamaMLP(self.config, inner_dim, dtype=self.dtype)

    def __call__(
        self,
        hidden_states,
        position_ids=None,
        attention_mask=None,
        deterministic: bool = True,
        init_cache: bool = False,
        output_attentions: bool = False,
    ):
        residual = hidden_states
        hidden_states = self.input_layernorm(hidden_states)
        outputs = self.self_attn(
            hidden_states,
            position_ids=position_ids,
            attention_mask=attention_mask,
            deterministic=deterministic,
            init_cache=init_cache,
            output_attentions=output_attentions,
        )
        # residual connection
        attn_output = outputs[0]
        hidden_states = residual + attn_output

        residual = hidden_states
        hidden_states = self.post_attention_layernorm(hidden_states)
        hidden_states = self.mlp(hidden_states)
        # residual connection
        hidden_states = residual + hidden_states

        return (hidden_states,) + outputs[1:]


# TODO: check this is ported
class FlaxLlamaPreTrainedModel(FlaxPreTrainedModel):
    """
    An abstract class to handle weights initialization and a simple interface for downloading and loading pretrained
    models.
    """

    config_class = LlamaConfig
    base_model_prefix = "transformer"
    module_class: nn.Module = None

    def __init__(
        self,
        config: LlamaConfig,
        input_shape: Tuple = (1, 1),
        seed: int = 0,
        dtype: jnp.dtype = jnp.float32,
        _do_init: bool = True,
        **kwargs,
    ):
        module = self.module_class(config=config, dtype=dtype, **kwargs)
        super().__init__(config, module, input_shape=input_shape, seed=seed, dtype=dtype, _do_init=_do_init)

    def init_weights(self, rng: jax.random.PRNGKey, input_shape: Tuple, params: FrozenDict = None) -> FrozenDict:
        # init input tensors
        input_ids = jnp.zeros(input_shape, dtype="i4")
        attention_mask = jnp.ones_like(input_ids)
        position_ids = jnp.broadcast_to(jnp.arange(jnp.atleast_2d(input_ids).shape[-1]), input_shape)
        params_rng, dropout_rng = jax.random.split(rng)
        rngs = {"params": params_rng, "dropout": dropout_rng}

        # TODO: add return_dict
        # random_params = self.module.init(rngs, input_ids, position_ids=position_ids, attention_mask=attention_mask, return_dict=False)["params"]
        random_params = self.module.init(rngs, input_ids, position_ids=position_ids, attention_mask=attention_mask)[
            "params"
        ]

        if params is not None:
            random_params = flatten_dict(unfreeze(random_params))
            params = flatten_dict(unfreeze(params))
            for missing_key in self._missing_keys:
                params[missing_key] = random_params[missing_key]
            self._missing_keys = set()
            return freeze(unflatten_dict(params))
        else:
            return random_params

    def init_cache(self, batch_size, max_length):
        r"""
        Args:
            batch_size (`int`):
                batch_size used for fast auto-regressive decoding. Defines the batch size of the initialized cache.
            max_length (`int`):
                maximum possible length for auto-regressive decoding. Defines the sequence length of the initialized
                cache.
        """
        # init input variables to retrieve cache
        input_ids = jnp.ones((batch_size, max_length))
        attention_mask = jnp.ones_like(input_ids)
        position_ids = jnp.broadcast_to(jnp.arange(jnp.atleast_2d(input_ids).shape[-1]), input_ids.shape)

        # init_variables = self.module.init(
        # jax.random.PRNGKey(0), input_ids, position_ids=position_ids, attention_mask=attention_mask, return_dict=False, init_cache=True
        # )
        init_variables = self.module.init(
            jax.random.PRNGKey(0), input_ids, position_ids=position_ids, attention_mask=attention_mask, init_cache=True
        )
        return unfreeze(init_variables["cache"])

    @add_start_docstrings_to_model_forward(LLAMA_INPUTS_DOCSTRING)
    def __call__(
        self,
        input_ids,
        position_ids=None,
        attention_mask=None,
        params: dict = None,
        past_key_values: dict = None,
        dropout_rng: jax.random.PRNGKey = None,
        train: bool = False,
        output_attentions: Optional[bool] = None,
        output_hidden_states: Optional[bool] = None,
        return_dict: Optional[bool] = None,
    ):
        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )
        return_dict = return_dict if return_dict is not None else self.config.return_dict

        batch_size, sequence_length = input_ids.shape

        if position_ids is None:
            if past_key_values is not None:
                raise ValueError("Make sure to provide `position_ids` when passing `past_key_values`.")

            position_ids = jnp.broadcast_to(jnp.arange(sequence_length)[None, :], (batch_size, sequence_length))

        if attention_mask is None:
            attention_mask = jnp.ones((batch_size, sequence_length))

        # Handle any PRNG if needed
        rngs = {}
        if dropout_rng is not None:
            rngs["dropout"] = dropout_rng

        inputs = {"params": params or self.params}

        # if past_key_values are passed then cache is already initialized a private flag init_cache has to be passed down to ensure cache is used. It has to be made sure that cache is marked as mutable so that it can be changed by FlaxLlamaNeoAttention module
        if past_key_values:
            inputs["cache"] = past_key_values
            mutable = ["cache"]
        else:
            mutable = False

        outputs = self.module.apply(
            inputs,
            jnp.array(input_ids, dtype="i4"),
            jnp.array(position_ids, dtype="i4"),
            jnp.array(attention_mask, dtype="i4"),
            not train,
            False,
            output_attentions,
            output_hidden_states,
            return_dict,
            rngs=rngs,
            mutable=mutable,
        )

        # add updated cache to model output
        if past_key_values is not None and return_dict:
            outputs, past_key_values = outputs
            outputs["past_key_values"] = unfreeze(past_key_values["cache"])
            return outputs
        elif past_key_values is not None and not return_dict:
            outputs, past_key_values = outputs
            outputs = outputs[:1] + (unfreeze(past_key_values["cache"]),) + outputs[1:]

        return outputs


class FlaxLlamaBlockCollection(nn.Module):
    config: LlamaConfig
    dtype: jnp.dtype = jnp.float32

    def setup(self):
        self.blocks = [
            FlaxLlamaDecoderLayer(self.config, dtype=self.dtype, name=str(i))
            for i in range(self.config.num_hidden_layers)
        ]

    def __call__(
        self,
        hidden_states,
        position_ids=None,
        attention_mask=None,
        deterministic: bool = True,
        init_cache: bool = False,
        output_attentions: bool = False,
    ):
        all_attentions = () if output_attentions else None

        for block in self.blocks:
            layer_outputs = block(
                hidden_states,
                attention_mask=attention_mask,
                position_ids=position_ids,
                deterministic=deterministic,
                init_cache=init_cache,
                output_attentions=output_attentions,
            )
            hidden_states = layer_outputs[0]

            if output_attentions:
                all_attentions += (layer_outputs[1],)

        # this contains possible `None` values - `FlaxLlamaModule` will filter them out
        outputs = (hidden_states, all_attentions)

        return outputs


class FlaxLlamaModule(nn.Module):
    config: LlamaConfig
    dtype: jnp.dtype = jnp.float32

    def setup(self):
        self.hidden_size = self.config.hidden_size
        embedding_init = jax.nn.initializers.normal(stddev=self.config.initializer_range)
        self.embed_tokens = nn.Embed(
            self.config.vocab_size,
            self.hidden_size,
            embedding_init=embedding_init,
        )
        self.layers = FlaxLlamaBlockCollection(self.config, dtype=self.dtype)
        self.norm = FlaxLlamaRMSNorm(self.config.rms_norm_eps)

    def __call__(
        self,
        input_ids,
        position_ids=None,
        attention_mask=None,
        deterministic=True,
        init_cache: bool = False,
        output_attentions: bool = False,
        # TODO: implement these args
        # output_hidden_states: bool = False,
        # return_dict: bool = True,
    ):
        input_embeds = self.embed_tokens(input_ids.astype("i4"))

        outputs = self.layers(
            input_embeds,
            position_ids=position_ids,
            attention_mask=attention_mask,
            deterministic=deterministic,
            init_cache=init_cache,
            output_attentions=output_attentions,
            # output_hidden_states=output_hidden_states,
            # return_dict=return_dict,
        )

        hidden_states = outputs[0]
        hidden_states = self.norm(hidden_states)

        # TODO: implement this
        # if output_hidden_states:
        # all_hidden_states = outputs[1] + (hidden_states,)
        # outputs = (hidden_states, all_hidden_states) + outputs[2:]
        # else:
        # outputs = (hidden_states,) + outputs[1:]

        # if not return_dict:
        # return tuple(v for v in outputs if v is not None)

        # return FlaxBaseModelOutput(
        # last_hidden_state=hidden_states,
        # hidden_states=outputs[1],
        # attentions=outputs[-1],
        # )

        return hidden_states


@add_start_docstrings(
    "The bare Llama Model transformer outputting raw hidden-states without any specific head on top.",
    LLAMA_START_DOCSTRING,
)
class FlaxLlamaModel(FlaxLlamaPreTrainedModel):
    module_class = FlaxLlamaModule


# append_call_sample_docstring(FlaxLlamaModel, _CHECKPOINT_FOR_DOC, FlaxBaseModelOutput, _CONFIG_FOR_DOC)


class FlaxLlamaForCausalLMModule(nn.Module):
    config: LlamaConfig
    dtype: jnp.dtype = jnp.float32

    def setup(self):
        self.model = FlaxLlamaModule(self.config, dtype=self.dtype)
        self.lm_head = nn.Dense(
            self.config.vocab_size,
            use_bias=False,
            dtype=self.dtype,
            kernel_init=jax.nn.initializers.normal(stddev=self.config.initializer_range),
        )

    def __call__(
        self,
        input_ids,
        position_ids=None,
        attention_mask=None,
        deterministic: bool = True,
        init_cache: bool = False,
        output_attentions: bool = False,
        # output_hidden_states: bool = False,
        # return_dict: bool = True,
    ):
        outputs = self.model(
            input_ids,
            position_ids=position_ids,
            attention_mask=attention_mask,
            deterministic=deterministic,
            init_cache=init_cache,
            output_attentions=output_attentions,
            # output_hidden_states=output_hidden_states,
            # return_dict=return_dict,
        )

        # TODO: add this back when we return `FlaxBaseModelOutput`
        # hidden_states = outputs[0]
        hidden_states = outputs
        lm_logits = self.lm_head(hidden_states)

        # if not return_dict:
        # return (lm_logits,) + outputs[1:]

        # TODO: return FlaxCausalLMOutput
        # return FlaxCausalLMOutput(logits=lm_logits, hidden_states=outputs.hidden_states, attentions=outputs.attentions)
        return lm_logits


@add_start_docstrings(
    """
    The Llama Model transformer with a language modeling head on top (linear layer with weights tied to the input
    embeddings).
    """,
    LLAMA_START_DOCSTRING,
)
class FlaxLlamaForCausalLM(FlaxLlamaPreTrainedModel):
    module_class = FlaxLlamaForCausalLMModule

    def prepare_inputs_for_generation(self, input_ids, max_length, attention_mask: Optional[jnp.DeviceArray] = None):
        # initializing the cache
        batch_size, seq_length = input_ids.shape

        past_key_values = self.init_cache(batch_size, max_length)
        # Note that usually one would have to put 0's in the attention_mask for x > input_ids.shape[-1] and x < cache_length.
        # But since Llama uses a causal mask, those positions are masked anyways.
        # Thus we can create a single static attention_mask here, which is more efficient for compilation
        extended_attention_mask = jnp.ones((batch_size, max_length), dtype="i4")
        if attention_mask is not None:
            position_ids = attention_mask.cumsum(axis=-1) - 1
            extended_attention_mask = lax.dynamic_update_slice(extended_attention_mask, attention_mask, (0, 0))
        else:
            position_ids = jnp.broadcast_to(jnp.arange(seq_length, dtype="i4")[None, :], (batch_size, seq_length))

        return {
            "past_key_values": past_key_values,
            "attention_mask": extended_attention_mask,
            "position_ids": position_ids,
        }

    def update_inputs_for_generation(self, model_outputs, model_kwargs):
        model_kwargs["past_key_values"] = model_outputs.past_key_values
        model_kwargs["position_ids"] = model_kwargs["position_ids"][:, -1:] + 1
        return model_kwargs


# append_call_sample_docstring(FlaxLlamaForCausalLM, _CHECKPOINT_FOR_DOC, FlaxCausalLMOutput, _CONFIG_FOR_DOC)

if __name__ == "__main__":
    import torch

    from .configuration_llama import LlamaConfig
    from .modeling_llama import LlamaForCausalLM

    key = jax.random.PRNGKey(0)
    torch.manual_seed(0)
    config = LlamaConfig(num_hidden_layers=2, vocab_size=16)
    print(config)

    model = FlaxLlamaForCausalLMModule(config)
    pt_model = LlamaForCausalLM(config)

    key, subkey = jax.random.split(key)
    x = jax.random.randint(subkey, (4, 128), 0, 16)
    mask = jnp.ones((4, 128), dtype=bool)
    position_ids = jnp.arange(128)[jnp.newaxis, :].repeat(4, axis=0)

    key, model_key = jax.random.split(key)
    y, params = model.init_with_output(model_key, x, attention_mask=mask, position_ids=position_ids)

    params = flatten_dict(params["params"], sep=".")

    for i, l in enumerate(pt_model.model.layers):
        pt_state = l.state_dict()
        l.load_state_dict(
            {
                "self_attn.q_proj.weight": torch.from_numpy(
                    np.asarray(params[f"model.layers.{i}.self_attn.q_proj.kernel"])
                ).T,
                "self_attn.k_proj.weight": torch.from_numpy(
                    np.asarray(params[f"model.layers.{i}.self_attn.k_proj.kernel"])
                ).T,
                "self_attn.v_proj.weight": torch.from_numpy(
                    np.asarray(params[f"model.layers.{i}.self_attn.v_proj.kernel"])
                ).T,
                "self_attn.o_proj.weight": torch.from_numpy(
                    np.asarray(params[f"model.layers.{i}.self_attn.o_proj.kernel"])
                ).T,
                "self_attn.rotary_emb.inv_freq": pt_state["self_attn.rotary_emb.inv_freq"],
                "input_layernorm.weight": torch.from_numpy(
                    np.asarray(params[f"model.layers.{i}.input_layernorm.weight"])
                ),
                "post_attention_layernorm.weight": torch.from_numpy(
                    np.asarray(params[f"model.layers.{i}.post_attention_layernorm.weight"])
                ),
                "mlp.down_proj.weight": torch.from_numpy(
                    np.asarray(params[f"model.layers.{i}.mlp.down_proj.kernel"])
                ).T,
                "mlp.up_proj.weight": torch.from_numpy(np.asarray(params[f"model.layers.{i}.mlp.up_proj.kernel"])).T,
                "mlp.gate_proj.weight": torch.from_numpy(
                    np.asarray(params[f"model.layers.{i}.mlp.gate_proj.kernel"])
                ).T,
            }
        )

    pt_model.model.embed_tokens.weight = torch.nn.Parameter(
        torch.from_numpy(np.asarray(params["model.embed_tokens.embedding"]))
    )
    pt_model.model.norm.weight = torch.nn.Parameter(torch.from_numpy(np.asarray(params["model.norm.weight"])))
    pt_model.lm_head.weight = torch.nn.Parameter(torch.from_numpy(np.asarray(params["lm_head.kernel"].T)))

    x_pt = torch.tensor(np.asarray(x))
    pt_y = pt_model(
        x_pt,
        attention_mask=torch.from_numpy(np.asarray(mask)),
        position_ids=torch.from_numpy(np.asarray(position_ids)),
    )[0]

    pt_y = pt_y.detach().numpy()

    try:
        np.testing.assert_allclose(y, pt_y, atol=1e-2, rtol=1e-2)
    except AssertionError as e:
        print(e)
        import ipdb

        ipdb.set_trace()

    print("done")
