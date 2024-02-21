from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import torch

from .configuration_utils import PretrainedConfig


class ModelCache:
    """
    A standalone class that holds multiple `Cache` instances, behaving exactly like the legacy cache format.
    Designed mostly for backwards compatibility purposes, it is used to set up the cache for models, or as an output
    type for the `forward` method of models that use caches.
    Parameters:
        caches (`List[Cache]`):
            A list of `Cache` instances.
    """

    def __init__(self, caches: List["Cache"]) -> None:
        self.caches = caches
        self.cache_cls = caches[0].__class__
        if not all(isinstance(cache, self.cache_cls) for cache in caches):
            raise ValueError(
                f"All caches in `caches` must be of the same type. Got: {[cache.__class__ for cache in caches]}"
            )

    def __len__(self) -> int:
        """
        Support for backwards-compatible `past_key_value` length, e.g. `len(past_key_value)`. This value corresponds
        to the number of layers in the model.
        """
        return len(self.caches)

    def __getitem__(self, layer_idx: int) -> List[Tuple[torch.Tensor]]:
        """
        Support for backwards-compatible `past_key_value` indexing, e.g. `past_key_value[0][0].shape[2]` to get the
        sequence length.
        """
        if layer_idx < len(self):
            return (self.caches[layer_idx].key_cache, self.caches[layer_idx].value_cache)
        else:
            raise KeyError(f"Cache only has {len(self)} layers, attempted to access layer with index {layer_idx}")

    def __iter__(self):
        """
        Support for backwards-compatible `past_key_value` iteration, e.g. `for x in past_key_value:` to iterate over
        keys and values
        """
        for layer_idx in range(len(self)):
            yield (self.caches[layer_idx].key_cache, self.caches[layer_idx].value_cache)

    @property
    def seen_tokens(self) -> int:
        """Returns the total number of tokens seen by the cache."""
        return self.caches[0].seen_tokens

    def get_seq_length(self) -> int:
        """Returns the sequence length of the cached states."""
        return self.caches[0].get_seq_length()

    def get_max_length(self) -> Optional[int]:
        """Returns the maximum sequence length of the cached states."""
        return self.caches[0].get_max_length()

    def get_usable_length(self, new_seq_length: int) -> int:
        """Given the sequence length of the new inputs, returns the usable length of the cache."""
        return self.caches[0].get_usable_length(new_seq_length)

    def reorder_cache(self, beam_idx: torch.LongTensor):
        """Reorders the cache for beam search, given the selected beam indices."""
        for cache in self.caches:
            cache.reorder_cache(beam_idx)

    def to_legacy_cache(self) -> Tuple[Tuple[torch.Tensor], Tuple[torch.Tensor]]:
        """Converts the `ModelCache` instance into the its equivalent in the legacy cache format."""
        legacy_cache = ()
        for layer_idx in range(len(self)):
            legacy_cache += ((self.caches[layer_idx].key_cache, self.caches[layer_idx].value_cache),)
        return legacy_cache

    @classmethod
    def from_legacy_cache(cls, past_key_values: Optional[Tuple[Tuple[torch.FloatTensor]]] = None) -> "DynamicCache":
        """Converts a cache in the legacy cache format into an equivalent `ModelCache`."""
        caches = []
        if past_key_values is not None:
            for layer_idx in range(len(past_key_values)):
                key_states, value_states = past_key_values[layer_idx]
                layer_cache = DynamicCache()
                layer_cache.update(key_states, value_states)
                caches.append(layer_cache)
        return cls(caches)


@dataclass
class Cache:
    """
    Base, abstract class for all caches. The actual data structure is specific to each subclass.
    """

    def update(
        self,
        key_states: torch.Tensor,
        value_states: torch.Tensor,
        cache_kwargs: Optional[Dict[str, Any]] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Updates the cache with the new `key_states` and `value_states` for a given layer.

        Parameters:
            key_states (`torch.Tensor`):
                The new key states to cache.
            value_states (`torch.Tensor`):
                The new value states to cache.
            cache_kwargs (`Dict[str, Any]`, `optional`):
                Additional arguments for the cache subclass. These are specific to each subclass and allow new types of
                cache to be created.

        Return:
            A tuple containing the updated key and value states.
        """
        raise NotImplementedError("Make sure to implement `update` in a subclass.")

    def get_seq_length(self) -> int:
        """Returns the sequence length of the cached states."""
        raise NotImplementedError("Make sure to implement `get_seq_length` in a subclass.")

    def get_max_length(self) -> Optional[int]:
        """Returns the maximum sequence length of the cached states, if there is any."""
        raise NotImplementedError("Make sure to implement `get_max_length` in a subclass.")

    def get_usable_length(self, new_seq_length: int) -> int:
        """Given the sequence length of the new inputs, returns the usable length of the cache."""
        # Cache without size limit -> all cache is usable
        # Cache with size limit -> if the length cache plus the length of the new inputs is larger the maximum cache
        #   length, we will need to evict part of the cache (and thus not all cache is usable)
        max_length = self.get_max_length()
        previous_seq_length = self.get_seq_length()
        if max_length is not None and previous_seq_length + new_seq_length > max_length:
            return max_length - new_seq_length
        return previous_seq_length

    def reorder_cache(self, beam_idx: torch.LongTensor):
        """Reorders the cache for beam search, given the selected beam indices."""
        raise NotImplementedError("Make sure to implement `reorder_cache` in a subclass.")


class DynamicCache(Cache):
    """
    A cache that grows dynamically as more tokens are generated. This is the default for generative models. The
    expected shape for each cached tensor is `[batch_size, num_heads, seq_len, head_dim]`.
    """

    def __init__(self, **unused_kwargs) -> None:
        self.key_cache: Optional[torch.Tensor] = None
        self.value_cache: Optional[torch.Tensor] = None
        self.seen_tokens = 0  # Used in `generate` to keep tally of how many tokens the cache has seen

    def update(
        self,
        key_states: torch.Tensor,
        value_states: torch.Tensor,
        layer_idx: int,
        cache_kwargs: Optional[Dict[str, Any]] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Updates the cache with the new `key_states` and `value_states` for a given layer.

        Parameters:
            key_states (`torch.Tensor`):
                The new key states to cache.
            value_states (`torch.Tensor`):
                The new value states to cache.
            cache_kwargs (`Dict[str, Any]`, `optional`):
                Additional arguments for the cache subclass. No additional arguments are used in `DynamicCache`.

        Return:
            A tuple containing the updated key and value states.
        """
        # Update the number of seen tokens
        self.seen_tokens += key_states.shape[-2]

        # Update the cache
        if self.key_cache is None:
            self.key_cache = key_states
            self.value_cache = value_states
        else:
            self.key_cache = torch.cat([self.key_cache, key_states], dim=-2)
            self.value_cache = torch.cat([self.value_cache, value_states], dim=-2)

        return self.key_cache, self.value_cache

    def get_seq_length(self) -> int:
        """Returns the sequence length of the cached states. A layer index can be optionally passed."""
        if self.key_cache is None:
            return 0
        return self.key_cache.shape[-2]

    def get_max_length(self) -> Optional[int]:
        """Returns the maximum sequence length of the cached states. DynamicCache does not have a maximum length."""
        return None

    def reorder_cache(self, beam_idx: torch.LongTensor):
        """Reorders the cache for beam search, given the selected beam indices."""
        device = self.key_cache.device
        self.key_cache = self.key_cache.index_select(0, beam_idx.to(device))
        device = self.value_cache.device
        self.value_cache = self.value_cache.index_select(0, beam_idx.to(device))


class SinkCache(Cache):
    """
    A cache that as described in the [Attention Sinks paper](https://arxiv.org/abs/2309.17453). It allows the model to
    generate beyond the length of its context window, without losing fluency in the conversation. As it discards past
    tokens, the model will lose the ability to generate tokens that depend on the context that was discarded.

    It stores the Key and Value states as a list of tensors, one for each layer. The expected shape for each tensor is
    `[batch_size, num_heads, seq_len, head_dim]`.

    Parameters:
        window_length (`int`):
            The length of the context window.
        num_sink_tokens (`int`):
            The number of sink tokens. See the original paper for more information.
    """

    def __init__(self, window_length: int, num_sink_tokens: int, **unused_kwargs) -> None:
        self.key_cache: Optional[torch.Tensor] = None
        self.value_cache: Optional[torch.Tensor] = None
        self.window_length = window_length
        self.num_sink_tokens = num_sink_tokens
        self.cos_sin_cache = {}
        self.seen_tokens = 0  # Used in `generate` to keep tally of how many tokens the cache has seen

    @staticmethod
    def _rotate_half(x):
        x1 = x[..., : x.shape[-1] // 2]
        x2 = x[..., x.shape[-1] // 2 :]
        return torch.cat((-x2, x1), dim=-1)

    def _apply_key_rotary_pos_emb(
        self, key_states: torch.Tensor, cos: torch.Tensor, sin: torch.Tensor
    ) -> torch.Tensor:
        rotated_key_states = (key_states * cos) + (self._rotate_half(key_states) * sin)
        return rotated_key_states

    def _get_rerotation_cos_sin(
        self, key_states: torch.Tensor, cos: torch.Tensor, sin: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        if key_states.shape[-2] not in self.cos_sin_cache:
            # Upcast to float32 temporarily for better accuracy
            cos = cos.to(torch.float32)
            sin = sin.to(torch.float32)

            # Compute the cos and sin required for back- and forward-rotating to one position earlier in the sequence
            original_cos = cos[self.num_sink_tokens + key_states.shape[-2] :]
            shifted_cos = cos[self.num_sink_tokens : -key_states.shape[-2]]
            original_sin = sin[self.num_sink_tokens + key_states.shape[-2] :]
            shifted_sin = sin[self.num_sink_tokens : -key_states.shape[-2]]
            rerotation_cos = original_cos * shifted_cos + original_sin * shifted_sin
            rerotation_sin = -original_sin * shifted_cos + original_cos * shifted_sin

            self.cos_sin_cache[key_states.shape[-2]] = (
                rerotation_cos.to(key_states.dtype).unsqueeze(0),
                rerotation_sin.to(key_states.dtype).unsqueeze(0),
            )
        return self.cos_sin_cache[key_states.shape[-2]]

    # Copied from transformers.cache_utils.DynamicCache.get_seq_length
    def get_seq_length(self) -> int:
        """Returns the sequence length of the cached states. A layer index can be optionally passed."""
        if self.key_cache is None:
            return 0
        return self.key_cache.shape[-2]

    def get_max_length(self) -> Optional[int]:
        """Returns the maximum sequence length of the cached states."""
        return self.window_length

    def update(
        self,
        key_states: torch.Tensor,
        value_states: torch.Tensor,
        cache_kwargs: Optional[Dict[str, Any]] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Updates the cache with the new `key_states` and `value_states` for a given layer.

        Parameters:
            key_states (`torch.Tensor`):
                The new key states to cache.
            value_states (`torch.Tensor`):
                The new value states to cache.
            cache_kwargs (`Dict[str, Any]`, `optional`):
                Additional arguments for the cache subclass. The following arguments can be used in `SinkCache`: `sin`,
                `cos` and `partial_rotation_size`. These arguments are used with models using RoPE, to recompute the
                rotation as the tokens are shifted.

        Return:
            A tuple containing the updated key and value states.
        """
        # Optional kwargs for `SinkCache` -- needed on models using RoPE. `partial_rotation_size` is used on models
        # with partially rotated position embeddings, like Phi or Persimmon.
        sin = cache_kwargs.get("sin")
        cos = cache_kwargs.get("cos")
        partial_rotation_size = cache_kwargs.get("partial_rotation_size")
        using_rope = cos is not None and sin is not None

        # Update the number of seen tokens
        self.seen_tokens += key_states.shape[-2]

        # [bsz, num_heads, seq_len, head_dim]
        if self.key_cache is None:
            # Empty cache
            self.key_cache = key_states
            self.value_cache = value_states

        elif key_states.shape[-2] + self.get_seq_length() < self.window_length:
            # Growing cache
            self.key_cache = torch.cat([self.key_cache, key_states], dim=-2)
            self.value_cache = torch.cat([self.value_cache, value_states], dim=-2)

        else:
            # Shifting cache
            keys_to_keep = self.key_cache[:, :, -self.window_length + self.num_sink_tokens + key_states.shape[-2] :]

            # On RoPE models, we need to recompute the Key rotation as the tokens are shifted
            if using_rope:
                rerotation_cos, rerotation_sin = self._get_rerotation_cos_sin(
                    key_states, cos[: self.window_length], sin[: self.window_length]
                )
                if partial_rotation_size is not None:
                    keys_to_keep, keys_pass = (
                        keys_to_keep[..., :partial_rotation_size],
                        keys_to_keep[..., partial_rotation_size:],
                    )
                keys_to_keep = self._apply_key_rotary_pos_emb(keys_to_keep, rerotation_cos, rerotation_sin)
                if partial_rotation_size is not None:
                    keys_to_keep = torch.cat((keys_to_keep, keys_pass), dim=-1)

            # Concatenate sink tokens, shifted & rotated tokens (if needed), and new tokens
            sink_keys = self.key_cache[:, :, : self.num_sink_tokens]
            self.key_cache = torch.cat([sink_keys, keys_to_keep, key_states], dim=-2)

            sink_values = self.value_cache[:, :, : self.num_sink_tokens]
            values_to_keep = self.value_cache[
                :, :, -self.window_length + self.num_sink_tokens + value_states.shape[-2] :
            ]
            self.value_cache = torch.cat([sink_values, values_to_keep, value_states], dim=-2)

        return self.key_cache, self.value_cache

    # Copied from transformers.cache_utils.DynamicCache.reorder_cache
    def reorder_cache(self, beam_idx: torch.LongTensor):
        """Reorders the cache for beam search, given the selected beam indices."""
        device = self.key_cache.device
        self.key_cache = self.key_cache.index_select(0, beam_idx.to(device))
        device = self.value_cache.device
        self.value_cache = self.value_cache.index_select(0, beam_idx.to(device))


class StaticCache(Cache):
    """
    Static cache class to be used with `torch.compile(model)`.

    Parameters:
        config (`PretrainedConfig):
            The configuration file defining the `max_position_embeddings`, `hidden_size` and `num_attention_heads`
            required to initialize the static cache.
        max_batch_size (`int`):
            The maximum batch size with which the model will be used.
        max_cache_len (`int`):
            The maximum sequence length with which the model will be used.
        device (`torch.device`):
            The device on which the cache should be initialized. Should be the same as the layer.
        dtype (*optional*, defaults to `torch.float32`):
            The default `dtype` to use when initializing the layer.
    """

    def __init__(
        self,
        config: PretrainedConfig,
        max_batch_size: int,
        max_cache_len: int,
        device,
        dtype=torch.float32,
        **unused_kwargs,
    ) -> None:
        super().__init__()
        self.max_batch_size = max_batch_size
        self.max_cache_len = config.max_position_embeddings if max_cache_len is None else max_cache_len
        self.head_dim = config.hidden_size // config.num_attention_heads
        if hasattr(config, "num_key_value_heads") and config.num_key_value_heads is not None:
            self.num_key_value_heads = config.num_key_value_heads
        else:
            self.num_key_value_heads = config.num_attention_heads
        self.dtype = config.torch_dtype if config.torch_dtype is not None else dtype

        cache_shape = (max_batch_size, self.num_key_value_heads, self.max_cache_len, self.head_dim)
        self.key_cache: torch.Tensor = torch.zeros(cache_shape, dtype=self.dtype, device=device)
        self.value_cache: torch.Tensor = torch.zeros(cache_shape, dtype=self.dtype, device=device)

    def update(
        self,
        key_states: torch.Tensor,
        value_states: torch.Tensor,
        cache_kwargs: Optional[Dict[str, Any]] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Updates the cache with the new `key_states` and `value_states` for a given layer..
        It is VERY important to index using a tensor, otherwise you introduce a copy to the device.

        Parameters:
            key_states (`torch.Tensor`):
                The new key states to cache.
            value_states (`torch.Tensor`):
                The new value states to cache.
            cache_kwargs (`Dict[str, Any]`, `optional`):
                Additional arguments for the cache subclass. The `StaticCache` just needs the `q_len`
                to know how much of the cache it should overwrite.

        Return:
            A tuple containing the updated key and value states.
        """
        new_cache_positions = cache_kwargs.get("cache_position")
        k_out = self.key_cache
        v_out = self.value_cache

        k_out[:, :, new_cache_positions] = key_states
        v_out[:, :, new_cache_positions] = value_states

        return k_out, v_out

    def get_seq_length(self) -> int:
        """Returns the sequence length of the cached states that were seen by the model. `layer_idx` kept for BC"""
        # TODO: Fix once the stateful `int` bug in PyTorch is fixed.
        raise ValueError(
            "get_seq_length is not implemented for StaticCache. Please refer to https://github.com/huggingface/transformers/pull/29114."
        )

    def get_usable_length(self, new_sequence_length=None) -> int:
        # TODO: Fix once the stateful `int` bug in PyTorch is fixed.
        raise ValueError(
            "get_seq_length is not implemented for StaticCache. Please refer to https://github.com/huggingface/transformers/pull/29114."
        )

    def get_max_length(self) -> Optional[int]:
        """Returns the maximum sequence length of the cached states. DynamicCache does not have a maximum length."""
        return self.max_cache_len

    def reorder_cache(self, beam_idx: torch.LongTensor):
        """Reorders the cache for beam search, given the selected beam indices."""
        device = self.key_cache.device
        self.key_cache = self.key_cache.index_select(0, beam_idx.to(device))
        device = self.value_cache.device
        self.value_cache = self.value_cache.index_select(0, beam_idx.to(device))
