# coding=utf-8
# Copyright 2020 The Facebook AI Research Team Authors and The HuggingFace Inc. team.
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
"""TF BART model, ported from the fairseq repo."""
import logging
import math
import random
from typing import Dict, List, Optional, Tuple

import numpy as np
import tensorflow as tf
from tensorflow import Tensor
from tensorflow.keras.layers import Dense, Dropout, LayerNormalization

from .configuration_bart import BartConfig
from .file_utils import add_start_docstrings, add_start_docstrings_to_callable
from .modeling_tf_utils import DUMMY_INPUTS, TFPreTrainedModel, TFSharedEmbeddings, keras_serializable, shape_list


# from .modeling_utils import PreTrainedModel, create_position_ids_from_input_ids


def create_position_ids_from_input_ids(input_ids, padding_idx):
    """ Replace non-padding symbols with their position numbers. Position numbers begin at
    padding_idx+1. Padding symbols are ignored. This is modified from fairseq's
    `utils.make_positions`.

    :param torch.Tensor x:
    :return tf.Tensor:
    """
    # The series of casts and type-conversions here are carefully balanced to both work with ONNX export and XLA.
    mask = input_ids.ne(padding_idx).int()
    incremental_indicies = tf.cumsum(mask, axis=1).type_as(mask) * mask
    return incremental_indicies.long() + padding_idx


logger = logging.getLogger(__name__)


TF_BART_PRETRAINED_MODEL_ARCHIVE_MAP = {
    "bart-large": "https://s3.amazonaws.com/models.huggingface.co/bert/facebook/bart-large/pytorch_model.bin",
    "bart-large-mnli": "https://s3.amazonaws.com/models.huggingface.co/bert/facebook/bart-large-mnli/pytorch_model.bin",
    "bart-large-cnn": "https://s3.amazonaws.com/models.huggingface.co/bert/facebook/bart-large-cnn/pytorch_model.bin",
}

BART_START_DOCSTRING = r"""

    Parameters:
        config (:class:`~transformers.BartConfig`): Model configuration class with all the parameters of the model.
            Initializing with a config file does not load the weights associated with the model, only the configuration.
            Check out the :meth:`~transformers.PreTrainedModel.from_pretrained` method to load the model weights.

"""

BART_INPUTS_DOCSTRING = r"""
    Args:
        input_ids (:obj:`tf.LongTensor` of shape :obj:`(batch_size, sequence_length)`):
               Indices of input sequence tokens in the vocabulary. Use BartTokenizer.encode to produce them.
            Padding will be ignored by default should you provide it.
            Indices can be obtained using :class:`transformers.BartTokenizer.encode(text)`.
        attention_mask (:obj:`tf.Tensor` of shape :obj:`(batch_size, sequence_length)`, `optional`, defaults to :obj:`None`):
            Mask to avoid performing attention on padding token indices in input_ids.
            Mask values selected in ``[0, 1]``:
            ``1`` for tokens that are NOT MASKED, ``0`` for MASKED tokens.
        decoder_input_ids (:obj:`tf.LongTensor` of shape :obj:`(batch_size, target_sequence_length)`, `optional`, defaults to :obj:`None`):
            Provide for translation and summarization training. By default, the model will create this tensor by shifting the input_ids right, following the paper.
        decoder_attention_mask (:obj:`tf.Tensor` of shape :obj:`(batch_size, 1, tgt_seq_len, tgt_seq_len)`, `optional`, defaults to :obj:`None`):
            Default behavior: generate a tensor that ignores pad tokens and future tokens, as in the paper.
            If you want to change padding behavior, you should read :func:`~transformers.modeling_bart._prepare_decoder_inputs` and modify.
            See diagram 1 in the paper for more info on the default strategy
"""
LARGE_NEGATIVE = -1e8
T = tf.Tensor


def causal_attention_mask(nd, ns, dtype):
    """1's in the lower triangle, counting from the lower right corner.
    Same as tf.matrix_band_part(tf.ones([nd, ns]), -1, ns-nd), but doesn't produce garbage on TPUs.
    """
    i = tf.range(nd)[:, None]
    j = tf.range(ns)
    m = i < j - ns + nd
    return tf.cast(m, dtype) * LARGE_NEGATIVE


def invert_mask(attention_mask: T):
    """Turns 1->0, 0->1, False->True, True-> False"""
    assert attention_mask._rank() == 2
    attention_mask = tf.cast(attention_mask, tf.bool)
    ret = tf.math.logical_not(attention_mask)
    assert ret.dtype == tf.bool
    return ret


def _prepare_bart_decoder_inputs(
    config, input_ids: T, decoder_input_ids=None, decoder_attn_mask=None, mask_dtype=None,
):
    """Prepare masks that ignore padding tokens  decoder and a causal lm mask for the decoder if
    none are provided. This mimics the default behavior in fairseq. To override it pass in masks.
    """
    pad_token_id = config.pad_token_id
    if decoder_input_ids is None:
        decoder_input_ids = shift_tokens_right(input_ids, pad_token_id)
    bsz, tgt_len = decoder_input_ids.shape[:2]
    if decoder_attn_mask is None:
        decoder_padding_mask = make_padding_mask(decoder_input_ids, pad_token_id)
    else:
        decoder_padding_mask = invert_mask(T)

    causal_lm_mask = causal_attention_mask(tgt_len, tgt_len, mask_dtype)
    return decoder_input_ids, decoder_padding_mask, causal_lm_mask


class TFPretrainedBartModel(TFPreTrainedModel):
    config_class = BartConfig
    base_model_prefix = "model"
    pretrained_model_archive_map = TF_BART_PRETRAINED_MODEL_ARCHIVE_MAP

    @property
    def dummy_inputs(self):
        pad_token = 1
        input_ids = tf.cast(tf.constant(DUMMY_INPUTS), tf.int32)
        decoder_input_ids = tf.cast(tf.constant(DUMMY_INPUTS), tf.int32)
        dummy_inputs = {
            "decoder_input_ids": decoder_input_ids,
            "attention_mask": tf.math.not_equal(input_ids, pad_token),
            "input_ids": input_ids,
        }
        return dummy_inputs


# Helper Functions, mostly for making masks
def _check_shapes(shape_1, shape2):
    if shape_1 != shape2:
        raise AssertionError("shape mismatch: {} != {}".format(shape_1, shape2))


def shift_tokens_right(input_ids, pad_token_id):
    """Shift input ids one token to the right, and wrap the last non pad token (usually <eos>)."""
    raise NotImplementedError("Doesnt work at all.")
    prev_output_tokens = tf.identity(input_ids)
    index_of_eos = tf.reduce_sum(tf.cast(tf.math.not_equal(input_ids, pad_token_id), tf.int8), axis=1) - 1
    index_of_eos = tf.cast(tf.expand_dims(index_of_eos, -1), input_ids.dtype)
    import ipdb

    ipdb.set_trace()
    gathered = tf.gather(input_ids, index_of_eos, axis=1)
    return tf.concat([gathered, input_ids[:, :-1]], axis=1)
    #    prev_output_tokens[:, 1:] = input_ids[:, :-1]
    #    return prev_output_tokens
    # index_of_eos = (input_ids.ne(pad_token_id).sum(axis=1) - 1).unsqueeze(-1)


def make_padding_mask(input_ids, padding_idx=1):
    """True for pad tokens"""
    padding_mask = tf.math.equal(input_ids, padding_idx)  # bool tensor
    if not tf.math.reduce_any(padding_mask):
        padding_mask = None
    return padding_mask


# Helper Modules
def TFDropout(x, **kwargs):  # FIXME
    return x


class EncoderLayer(tf.keras.layers.Layer):
    def __init__(self, config: BartConfig):
        super().__init__()
        self.embed_dim = config.d_model
        self.self_attn = SelfAttention(
            self.embed_dim, config.encoder_attention_heads, dropout=config.attention_dropout,
        )
        assert not config.normalize_before, "MBART Not Supported"
        self.self_attn_layer_norm = LayerNorm(self.embed_dim)
        self.dropout_wt = tf.keras.layers.Dropout(config.dropout)
        self.activation_fn = gelu
        self.activation_dropout = tf.keras.layers.Dropout(config.activation_dropout)
        self.fc1 = Dense(config.encoder_ffn_dim)
        self.fc2 = Dense(self.embed_dim)
        self.final_layer_norm = LayerNormalization(epsilon=1e-5)
        # TODO(SS): could use sequential

    def call(self, x, encoder_padding_mask, output_attentions=False, training=False):
        """
        Args:
            x (Tensor): input to the layer of shape `(seq_len, batch, embed_dim)`
            encoder_padding_mask (ByteTensor): binary ByteTensor of shape
                `(batch, src_len)` where padding elements are indicated by ``1``.
            for t_tgt, t_src is excluded (or masked out), =0 means it is
            included in attention

        Returns:
            encoded output of shape `(seq_len, batch, embed_dim)`
        """
        residual = x
        x, attn_weights = self.self_attn(query=x, key=x, value=x, key_padding_mask=encoder_padding_mask)
        assert x.shape == residual.shape
        x = self.dropout_wt(x, training=training)
        x = residual + x
        x = self.self_attn_layer_norm(x)

        residual = x
        x = self.activation_fn(self.fc1(x))
        x = self.activation_dropout(x, training=training)
        x = self.fc2(x)
        x = self.dropout_wt(x, training=training)
        x = residual + x
        x = self.final_layer_norm(x)

        return x, attn_weights


class TFBartEncoder(tf.keras.layers.Layer):
    """
    Transformer encoder consisting of *config.encoder_layers* self attention layers. Each layer
    is a :class:`EncoderLayer`.

    Args:
        config: BartConfig
    """

    def __init__(self, config: BartConfig, embed_tokens: TFSharedEmbeddings):
        super().__init__()

        self.dropout = config.dropout
        self.layerdrop = config.encoder_layerdrop

        embed_dim = embed_tokens.vocab_size
        self.embed_scale = math.sqrt(embed_dim) if config.scale_embedding else 1.0
        self.padding_idx = config.pad_token_id
        self.max_source_positions = config.max_position_embeddings

        self.embed_tokens = embed_tokens
        self.embed_positions = LearnedPositionalEmbedding(
            config.max_position_embeddings, embed_tokens.hidden_size, self.padding_idx, config.extra_pos_embeddings,
        )
        self.layers = [EncoderLayer(config) for _ in range(config.encoder_layers)]
        self.layernorm_embedding = LayerNorm(embed_dim)

    def call(
        self, input_ids=None, attention_mask=None, output_attentions=False, output_hidden_states=False, training=False,
    ):
        """
        Args:
            input_ids (LongTensor): tokens in the source language of shape
                `(batch, src_len)`
            attention_mask (torch.LongTensor): indicating which indices are padding tokens.
        Returns:
            namedtuple:
                - **x** (Tensor): the last encoder layer's output of
                  shape `(src_len, batch, embed_dim)`

                - **encoder_states** (List[Tensor]): all intermediate
                  hidden states of shape `(src_len, batch, embed_dim)`.
                  Only populated if *return_all_hiddens* is True.
                - **all_attentions** (List[Tensor]): Attention weights for each layer.
                During training might not be of length n_layers because of layer dropout.
        """
        # check attention mask and invert
        if attention_mask is not None:
            assert attention_mask._rank() == 2

            attention_mask = tf.cast(attention_mask, dtype=tf.float32)
            attention_mask = (1.0 - attention_mask) * -1e9
            # assert attention_mask.max() <= 0
        inputs_embeds = self.embed_tokens(input_ids)
        embed_pos = self.embed_positions(input_ids)
        x = inputs_embeds + embed_pos
        x = self.layernorm_embedding(x)
        x = TFDropout(x, p=self.dropout, training=training)

        # B x T x C -> T x B x C
        x = tf.transpose(x, perm=[1, 0, 2])

        encoder_states, all_attentions = [], []

        # encoder layers
        for encoder_layer in self.layers:

            if output_hidden_states:
                encoder_states.append(x)
            # add LayerDrop (see https://arxiv.org/abs/1909.11556 for description)
            dropout_probability = random.uniform(0, 1)
            if training and (dropout_probability < self.layerdrop):  # skip the layer
                attn = None
            else:
                x, attn = encoder_layer(x, attention_mask)

            if output_attentions:
                all_attentions.append(attn)

        if output_hidden_states:
            encoder_states.append(x)

        encoder_states = [tf.transpose(hidden_state, perm=(1, 0, 2)) for hidden_state in encoder_states]
        x = tf.transpose(x, perm=(1, 0, 2))
        return x, encoder_states, all_attentions  # Always return three things, for now


class TFDecoderLayer(tf.keras.layers.Layer):
    def __init__(self, config: BartConfig):
        super().__init__()
        self.embed_dim = config.d_model
        self.self_attn = SelfAttention(
            embed_dim=self.embed_dim, num_heads=config.decoder_attention_heads, dropout=config.attention_dropout,
        )
        self.dropout = config.dropout
        self.activation_fn = gelu
        self.activation_dropout = config.activation_dropout

        self.self_attn_layer_norm = LayerNorm(self.embed_dim)
        self.encoder_attn = SelfAttention(
            self.embed_dim,
            config.decoder_attention_heads,
            dropout=config.attention_dropout,
            encoder_decoder_attention=True,
        )
        self.encoder_attn_layer_norm = LayerNorm(self.embed_dim)
        self.fc1 = Dense(config.decoder_ffn_dim)
        self.fc2 = Dense(self.embed_dim)
        self.final_layer_norm = LayerNorm(self.embed_dim)

    def call(
        self,
        x,
        encoder_hidden_states,
        encoder_attn_mask=None,
        layer_state=None,
        causal_mask=None,
        decoder_padding_mask=None,
        training=False,
    ):
        """
        Args:
            x (Tensor): input to the layer of shape `(seq_len, batch, embed_dim)`
            encoder_attn_mask (ByteTensor, optional): binary
                ByteTensor of shape `(batch, src_len)` where padding
                elements are indicated by ``1``.
            need_attn_weights (bool, optional): return attention weights
                for each head (default: return average over heads).

        Returns:
            encoded output of shape `(seq_len, batch, embed_dim)`
        """

        residual = x
        y = x  # TODO(SS): figure out why fairseq did this, then hopefully delete it

        if layer_state is None:
            layer_state = {}
        # next line mutates layer state
        x, self_attn_weights = self.self_attn(
            query=x,
            key=y,
            value=y,
            layer_state=layer_state,
            attn_mask=causal_mask,
            key_padding_mask=decoder_padding_mask,
        )
        x = TFDropout(x, p=self.dropout, training=training)
        x = residual + x
        x = self.self_attn_layer_norm(x)
        residual = x
        assert self.encoder_attn.cache_key != self.self_attn.cache_key

        x, encoder_attn_weights = self.encoder_attn(
            query=x,
            key=encoder_hidden_states,  # could be None
            value=encoder_hidden_states,
            key_padding_mask=encoder_attn_mask,
            layer_state=layer_state,  # mutates layer state
            static_kv=True,
        )
        x = TFDropout(x, p=self.dropout, training=training)
        x = residual + x

        x = self.encoder_attn_layer_norm(x)

        residual = x
        x = self.activation_fn(self.fc1(x))
        x = TFDropout(x, p=self.activation_dropout, training=training)
        x = self.fc2(x)
        x = TFDropout(x, p=self.dropout, training=training)
        x = residual + x
        x = self.final_layer_norm(x)
        return (
            x,
            self_attn_weights,
            layer_state,
        )  # just self_attn weights for now, following t5, layer_state = cache for decoding


class BartDecoder(tf.keras.layers.Layer):
    """
    Transformer decoder consisting of *config.decoder_layers* layers. Each layer
    is a :class:`TFDecoderLayer`.
    Args:
        config: BartConfig
        embed_tokens: output embedding
    """

    def __init__(self, config: BartConfig, embed_tokens):
        super().__init__()
        self.layerdrop = config.decoder_layerdrop
        self.padding_idx = config.pad_token_id
        self.max_target_positions = config.max_position_embeddings
        self.embed_tokens = embed_tokens
        self.embed_scale = math.sqrt(config.d_model) if config.scale_embedding else 1.0
        self.embed_positions = LearnedPositionalEmbedding(
            config.max_position_embeddings, config.d_model, self.padding_idx, config.extra_pos_embeddings
        )
        self.layers = [TFDecoderLayer(config) for _ in range(config.decoder_layers)]
        self.layernorm_embedding = LayerNorm(config.d_model)
        self.dropout = tf.keras.layers.Dropout(config.dropout)
        self.layer_norm = None  # fix later for mbart

    def call(
        self,
        input_ids,
        encoder_hidden_states,
        encoder_padding_mask,
        decoder_padding_mask,
        decoder_causal_mask,
        decoder_cached_states=None,
        use_cache=False,
        output_attentions=False,
        output_hidden_states=False,
        training=False,
        **unused,
    ):
        if unused:
            raise TypeError(f"Ignoring kwargs {unused}")
        # check attention mask and invert
        if encoder_padding_mask is not None:
            encoder_padding_mask = invert_mask(encoder_padding_mask)

        # embed positions
        positions = self.embed_positions(input_ids, use_cache=use_cache)

        if use_cache:
            input_ids = input_ids[:, -1:]
            positions = positions[:, -1:]  # happens after we embed them
            # assert input_ids.ne(self.padding_idx).any()

        x = self.embed_tokens(input_ids) * self.embed_scale
        x += positions
        x = self.layernorm_embedding(x)
        x = self.dropout(x)

        # Convert to Bart output format: (seq_len, BS, model_dim) -> (BS, seq_len, model_dim)
        x = tf.transpose(x, perm=(1, 0, 2))
        encoder_hidden_states = tf.transpose(encoder_hidden_states, perm=(1, 0, 2))

        # decoder layers
        all_hidden_states = ()
        all_self_attns = ()
        next_decoder_cache = []
        for idx, decoder_layer in enumerate(self.layers):
            # add LayerDrop (see https://arxiv.org/abs/1909.11556 for description)
            if output_hidden_states:
                all_hidden_states += (x,)
            dropout_probability = random.uniform(0, 1)
            if training and (dropout_probability < self.layerdrop):
                continue

            layer_state = decoder_cached_states[idx] if decoder_cached_states is not None else None

            x, layer_self_attn, layer_past = decoder_layer(
                x,
                encoder_hidden_states,
                encoder_attn_mask=encoder_padding_mask,
                decoder_padding_mask=decoder_padding_mask,
                layer_state=layer_state,
                causal_mask=decoder_causal_mask,
            )

            if use_cache:
                next_decoder_cache.append(layer_past.copy())

            if self.layer_norm and (idx == len(self.layers) - 1):  # last layer of mbart
                x = self.layer_norm(x)
            if output_attentions:
                all_self_attns += (layer_self_attn,)

        # Convert to standard output format: (seq_len, BS, model_dim) -> (BS, seq_len, model_dim)
        all_hidden_states = [tf.transpose(hidden_state, perm=(1, 0, 2)) for hidden_state in all_hidden_states]
        x = tf.transpose(x, perm=(1, 0, 2))
        encoder_hidden_states = tf.transpose(encoder_hidden_states, perm=(1, 0, 2))

        if use_cache:
            next_cache = ((encoder_hidden_states, encoder_padding_mask), next_decoder_cache)
        else:
            next_cache = None
        return x, next_cache, all_hidden_states, list(all_self_attns)


def _reorder_buffer(attn_cache, new_order):
    for k, input_buffer_k in attn_cache.items():
        if input_buffer_k is not None:
            attn_cache[k] = tf.gather(input_buffer_k, new_order, axis=0)
    return attn_cache


class SelfAttention(tf.keras.layers.Layer):
    """Multi-headed attention from "Attention Is All You Need"""

    def __init__(
        self,
        embed_dim,
        num_heads,
        dropout=0.0,
        bias=True,
        encoder_decoder_attention=False,  # otherwise self_attention
    ):
        super().__init__()
        self.embed_dim = embed_dim

        self.num_heads = num_heads
        self.dropout = dropout
        self.head_dim = embed_dim // num_heads
        assert self.head_dim * num_heads == self.embed_dim, "embed_dim must be divisible by num_heads"
        self.scaling = self.head_dim ** -0.5

        self.encoder_decoder_attention = encoder_decoder_attention

        self.k_proj = Dense(embed_dim, use_bias=bias, name="k_proj")
        self.q_proj = Dense(embed_dim, use_bias=bias, name="k_proj")
        self.v_proj = Dense(embed_dim, use_bias=bias, name="k_proj")
        self.out_proj = Dense(embed_dim, use_bias=bias, name="out_proj")

        self.cache_key = "encoder_decoder" if self.encoder_decoder_attention else "self"

    def _shape(self, tensor: T, dim_0, bsz) -> T:
        reshaped_T_B_D = tf.reshape(tensor, (dim_0, bsz * self.num_heads, self.head_dim))
        return tf.transpose(reshaped_T_B_D, perm=(1, 0, 2))

    def call(
        self,
        query,
        key: Optional[Tensor],
        value: Optional[Tensor],
        key_padding_mask: Optional[Tensor] = None,
        layer_state: Optional[Dict[str, Dict[str, Optional[Tensor]]]] = None,
        static_kv: bool = False,
        attn_mask: Optional[Tensor] = None,
        training=False,
    ) -> Tuple[Tensor, Optional[Tensor]]:
        """Input shape: Time(SeqLen) x Batch x Channel

        Args:

            key_padding_mask (ByteTensor, optional): mask to exclude
                keys that are pads, of shape `(batch, src_len)`, where
                padding elements are indicated by 1s.
            attn_mask (ByteTensor, optional): typically used to
                implement causal attention, where the mask prevents the
                attention from looking forward in time (default: None).
        """
        tgt_len, bsz, embed_dim = query.shape
        assert embed_dim == self.embed_dim
        # assert list(query.shape) == [tgt_len, bsz, embed_dim]
        # get here for encoder decoder cause of static_kv
        if layer_state is not None:  # get the last k,v and mask for reuse
            saved_state = layer_state.get(self.cache_key, {})
            if "prev_key" in saved_state:
                # previous time steps are cached - no need to recompute key and value if they are static
                if static_kv:
                    assert self.encoder_decoder_attention
                    key = value = None
        else:
            saved_state = None
            layer_state = {}

        q = self.q_proj(query) * self.scaling
        if self.encoder_decoder_attention:
            if key is None:
                assert value is None
                k = v = None
            else:
                k = self.k_proj(key)
                v = self.v_proj(key)
        else:
            k = self.k_proj(query)
            v = self.v_proj(query)

        q = self._shape(q, tgt_len, bsz)
        if k is not None:
            k = self._shape(k, -1, bsz)
        if v is not None:
            v = self._shape(v, -1, bsz)

        if saved_state is not None:
            k, v, key_padding_mask = self._use_saved_state(k, v, saved_state, key_padding_mask, static_kv, bsz)
        # assert self.cache_key != 'encoder_decoder' or key_padding_mask is None

        # Update cache
        layer_state[self.cache_key] = {
            "prev_key": tf.reshape(k, (bsz, self.num_heads, -1, self.head_dim)),
            "prev_value": tf.reshape(v, (bsz, self.num_heads, -1, self.head_dim)),
            "prev_key_padding_mask": key_padding_mask if not static_kv else None,
        }

        assert k is not None
        src_len = k.shape[1]
        attn_weights = tf.matmul(q, k, transpose_b=True)

        assert attn_weights.shape == (bsz * self.num_heads, tgt_len, src_len)

        if attn_mask is not None:
            attn_weights = tf.reshape(attn_weights, (bsz, self.num_heads, tgt_len, src_len)) + attn_mask
            attn_weights = tf.reshape(attn_weights, (bsz * self.num_heads, tgt_len, src_len))

        if key_padding_mask is not None and key_padding_mask._rank() == 0:
            key_padding_mask = None
        assert key_padding_mask is None or key_padding_mask.shape[:2] == (bsz, src_len,)
        if key_padding_mask is not None:  # don't attend to padding symbols
            attn_weights: T = tf.reshape(attn_weights, (bsz, self.num_heads, tgt_len, src_len))
            neg_mask = tf.cast(key_padding_mask, attn_weights.dtype) * -1e9
            extended_mask = tf.expand_dims(tf.expand_dims(neg_mask, 1), 2)
            attn_weights = attn_weights + extended_mask
            attn_weights = tf.reshape(attn_weights, (bsz * self.num_heads, tgt_len, src_len))

        attn_weights = tf.nn.softmax(attn_weights, axis=-1)
        attn_probs = TFDropout(attn_weights, training=training)

        assert v is not None
        attn_output = tf.matmul(attn_probs, v)
        assert attn_output.shape == (bsz * self.num_heads, tgt_len, self.head_dim)
        attn_output = tf.transpose(attn_output, perm=(1, 0, 2))
        attn_output = tf.reshape(attn_output, (tgt_len, bsz, embed_dim))
        attn_output = self.out_proj(attn_output)
        attn_weights: T = tf.reshape(attn_weights, (bsz, self.num_heads, tgt_len, src_len))
        return attn_output, attn_weights

    def _use_saved_state(self, k, v, saved_state, key_padding_mask, static_kv, bsz):
        # saved states are stored with shape (bsz, num_heads, seq_len, head_dim)
        if "prev_key" in saved_state:
            _prev_key = saved_state["prev_key"]
            assert _prev_key is not None
            prev_key = tf.reshape(_prev_key, (bsz * self.num_heads, -1, self.head_dim))
            if static_kv:
                k = prev_key
            else:
                assert k is not None
                k = tf.concat([prev_key, k], axis=1)
        if "prev_value" in saved_state:
            _prev_value = saved_state["prev_value"]
            assert _prev_value is not None
            prev_value = tf.reshape(_prev_value, (bsz * self.num_heads, -1, self.head_dim))
            if static_kv:
                v = prev_value
            else:
                assert v is not None
                v = tf.concat([prev_value, v], axis=1)
        assert k is not None and v is not None
        prev_key_padding_mask = saved_state.get("prev_key_padding_mask", None)  # type: Optional[Tensor]
        key_padding_mask = self._cat_prev_key_padding_mask(
            key_padding_mask, prev_key_padding_mask, bsz, k.shape[1], static_kv
        )
        return k, v, key_padding_mask

    @staticmethod
    def _cat_prev_key_padding_mask(
        key_padding_mask: Optional[Tensor],
        prev_key_padding_mask: Optional[Tensor],
        batch_size: int,
        src_len: int,
        static_kv: bool,
    ) -> Optional[Tensor]:
        # saved key padding masks have shape (bsz, seq_len)
        if prev_key_padding_mask is not None and static_kv:
            new_key_padding_mask = prev_key_padding_mask
        elif prev_key_padding_mask is not None and key_padding_mask is not None:
            new_key_padding_mask = tf.concat([prev_key_padding_mask, key_padding_mask], axis=1)
        # During incremental decoding, as the padding token enters and
        # leaves the frame, there will be a time when prev or current is None
        elif prev_key_padding_mask is not None:
            filler = tf.zeros(
                (batch_size, src_len - prev_key_padding_mask.shape[1]), dtype=prev_key_padding_mask.dtype
            )
            new_key_padding_mask = tf.concat([prev_key_padding_mask, filler], axis=1)
        elif key_padding_mask is not None:
            filler = tf.zeros((batch_size, src_len - key_padding_mask.shape[1]), dtype=key_padding_mask.dtype)
            new_key_padding_mask = tf.concat([filler, key_padding_mask], axis=1)
        else:
            new_key_padding_mask = prev_key_padding_mask
        return new_key_padding_mask


def gelu(x):
    """ Gaussian Error Linear Unit.
    Original Implementation of the gelu activation function in Google Bert repo when initially created.
        For information: OpenAI GPT's gelu is slightly different (and gives slightly different results):
        0.5 * x * (1 + torch.tanh(math.sqrt(2 / math.pi) * (x + 0.044715 * torch.pow(x, 3))))
        Also see https://arxiv.org/abs/1606.08415
    """
    cdf = 0.5 * (1.0 + tf.math.erf(x / tf.math.sqrt(2.0)))
    return x * cdf


class BartClassificationHead(tf.keras.layers.Layer):
    """Head for sentence-level classification tasks."""

    # This can trivially be shared with RobertaClassificationHead

    def __init__(
        self, input_dim, inner_dim, num_classes, pooler_dropout,
    ):
        super().__init__()

        self.dense = Dense(inner_dim)
        self.dropout = Dropout(pooler_dropout)
        self.out_proj = Dense(num_classes)

    def call(self, x):
        x = self.dropout(x)
        x = self.dense(x)
        x = tf.tanh(x)
        x = self.dropout(x)
        x = self.out_proj(x)
        return x


class LearnedPositionalEmbedding(TFSharedEmbeddings):
    """
    This module learns positional embeddings up to a fixed maximum size.
    Padding ids are ignored by either offsetting based on padding_idx
    or by setting padding_idx to None and ensuring that the appropriate
    position ids are passed to the forward function.
    """

    def __init__(self, num_embeddings: int, embedding_dim: int, padding_idx: int, offset):
        # Bart is set up so that if padding_idx is specified then offset the embedding ids by 2
        # and adjust num_embeddings appropriately. Other models dont have this hack
        self.offset = offset
        assert padding_idx is not None
        num_embeddings += offset
        super().__init__(num_embeddings, embedding_dim)

    def call(self, input_ids: T, use_cache=False):
        """Input is expected to be of size [bsz x seqlen]."""
        bsz, seq_len = input_ids.shape[:2]

        if use_cache:
            positions = tf.fill((1, 1), seq_len - 1)
        else:
            # starts at 0, ends at 1-seq_len
            positions = tf.range(0, seq_len, delta=1, dtype=tf.int32, name="range")
        return super().call(positions + self.offset)  # super object is not callable for some reason


def LayerNorm(normalized_shape, eps=1e-5, elementwise_affine=True):
    return tf.keras.layers.LayerNormalization(epsilon=eps)


def fill_with_neg_inf(t):
    """FP16-compatible function that fills a input_ids with -inf."""
    return t.float().fill_(float("-inf")).type_as(t)


def _filter_out_falsey_values(tup) -> Tuple:
    """Remove entries that are None or [] from an iterable."""
    return tuple(x for x in tup if isinstance(x, tf.Tensor) or x)


# Public API


@add_start_docstrings(
    "The bare BART Model outputting raw hidden-states without any specific head on top.", BART_START_DOCSTRING,
)
class TFBartModel(TFPretrainedBartModel):
    def __init__(self, config: BartConfig):
        super().__init__(config)

        padding_idx, vocab_size = config.pad_token_id, config.vocab_size
        self.shared = TFSharedEmbeddings(vocab_size, config.d_model, padding_idx)

        self.encoder = TFBartEncoder(config, self.shared)
        self.decoder = BartDecoder(config, self.shared)

    @add_start_docstrings_to_callable(BART_INPUTS_DOCSTRING)
    def call(
        self,
        input_ids,
        attention_mask=None,
        decoder_input_ids=None,
        encoder_outputs: Optional[Tuple] = None,
        decoder_attention_mask=None,
        decoder_cached_states=None,
        use_cache=None,
        output_attentions=None,
        output_hidden_states=None,
    ):
        # make masks if user doesn't supply
        assert decoder_input_ids is not None
        if decoder_input_ids is None:
            use_cache = False
        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )
        use_cache = use_cache if use_cache is not None else self.config.use_cache
        if not use_cache:
            decoder_input_ids, decoder_padding_mask, causal_mask = _prepare_bart_decoder_inputs(
                self.config,
                input_ids,
                decoder_input_ids=decoder_input_ids,
                decoder_attn_mask=decoder_attention_mask,
                mask_dtype=self.shared.dtype,
            )
        else:
            decoder_padding_mask, causal_mask = None, None

        assert decoder_input_ids is not None
        if encoder_outputs is None:
            encoder_outputs = self.encoder(
                input_ids=input_ids,
                attention_mask=attention_mask,
                output_attentions=output_attentions,
                output_hidden_states=output_hidden_states,
            )
        # if isinstance(encoder_outputs, T):
        #     encoder_outputs = (encoder_outputs,)

        assert isinstance(encoder_outputs, tuple), f"expected encoder_outputs to be a tuple, got {encoder_outputs}"
        # decoder outputs consists of (dec_features, layer_state, dec_hidden, dec_attn)
        decoder_outputs = self.decoder(
            decoder_input_ids,
            encoder_outputs[0],
            attention_mask,
            decoder_padding_mask,
            decoder_causal_mask=causal_mask,
            decoder_cached_states=decoder_cached_states,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            use_cache=use_cache,
        )
        # Attention and hidden_states will be [] or None if they aren't needed
        # decoder_outputs: Tuple = _filter_out_falsey_values(decoder_outputs)
        assert isinstance(decoder_outputs[0], T)
        # encoder_outputs: Tuple = _filter_out_falsey_values(encoder_outputs)
        return decoder_outputs + encoder_outputs

    def get_input_embeddings(self):
        return self.shared

    def set_input_embeddings(self, value):
        self.shared = value

    def get_output_embeddings(self):
        return self.shared


@add_start_docstrings(
    "The BART Model with a language modeling head. Can be used for summarization.", BART_START_DOCSTRING,
)
class TFBartForConditionalGeneration(TFPretrainedBartModel):
    base_model_prefix = "model"

    def __init__(self, config: BartConfig):
        super().__init__(config)
        self.model = TFBartModel(config)

    def tie_weights(self):
        pass  # hack to prevent changing lm_head.out_features. The input and output embeddings are still the same.

    @add_start_docstrings_to_callable(BART_INPUTS_DOCSTRING)
    def call(self, inputs: dict, **kwargs):
        r"""
        masked_lm_labels (:obj:`torch.LongTensor` of shape :obj:`(batch_size, sequence_length)`, `optional`, defaults to :obj:`None`):
            Labels for computing the masked language modeling loss.
            Indices should either be in ``[0, ..., config.vocab_size]`` or -100 (see ``input_ids`` docstring).
            Tokens with indices set to ``-100`` are ignored (masked), the loss is only computed for the tokens
            with labels
            in ``[0, ..., config.vocab_size]``.

    Returns:
        :obj:`tuple(torch.FloatTensor)` comprising various elements depending on the configuration (:class:`~transformers.RobertaConfig`) and inputs:
        masked_lm_loss (`optional`, returned when ``masked_lm_labels`` is provided) ``torch.FloatTensor`` of shape ``(1,)``:
            Masked language modeling loss.
        prediction_scores (:obj:`torch.FloatTensor` of shape :obj:`(batch_size, sequence_length, config.vocab_size)`)
            Prediction scores of the language modeling head (scores for each vocabulary token before SoftMax).
        hidden_states (:obj:`tuple(torch.FloatTensor)`, `optional`, returned when ``config.output_hidden_states=True``):
            Tuple of :obj:`torch.FloatTensor` (one for the output of the embeddings + one for the output of each layer)
            of shape :obj:`(batch_size, sequence_length, hidden_size)`.

            Hidden-states of the model at the output of each layer plus the initial embedding outputs.
        attentions (:obj:`tuple(torch.FloatTensor)`, `optional`, returned when ``config.output_attentions=True``):
            Tuple of :obj:`torch.FloatTensor` (one for each layer) of shape
            :obj:`(batch_size, num_heads, sequence_length, sequence_length)`.

            Attentions weights after the attention softmax, used to compute the weighted average in the self-attention
            heads.

    Examples::

            # Mask filling only works for bart-large
            from transformers import BartTokenizer, BartForConditionalGeneration
            tokenizer = BartTokenizer.from_pretrained('bart-large')
            TXT = "My friends are <mask> but they eat too many carbs."
            model = BartForConditionalGeneration.from_pretrained('bart-large')
            input_ids = tokenizer.batch_encode_plus([TXT], return_tensors='pt')['input_ids']
            logits = model(input_ids)[0]
            masked_index = (input_ids[0] == tokenizer.mask_token_id).nonzero().item()
            probs = logits[0, masked_index].softmax(dim=0)
            values, predictions = probs.topk(5)
            tokenizer.decode(predictions).split()
            # ['good', 'great', 'all', 'really', 'very']
        """

        if isinstance(inputs, T):
            input_ids = inputs
        else:
            if isinstance(inputs, dict):
                kwargs.update(**inputs)

            input_ids = kwargs.pop("input_ids", None)  # KeyError possible

        # attention_mask = kwargs.get("attention_mask", None)
        # encoder_outputs = kwargs.get("encoder_outputs", None)
        # decoder_input_ids = kwargs.get("decoder_input_ids", None)
        # decoder_attention_mask = kwargs.get("decoder_attention_mask", None)
        # decoder_cached_states = kwargs.get('decoder_cached_states', None)

        outputs = self.model(input_ids, **kwargs)
        lm_logits = self.model.shared(outputs[0], mode="linear")  # BORKED need linear
        outputs = (lm_logits,) + outputs[1:]  # Add hidden states and attention if they are here
        return outputs

    def prepare_inputs_for_generation(self, decoder_input_ids, past, attention_mask, use_cache=True):
        assert past is not None, "past has to be defined"
        if len(past) == 3:  # first step
            encoder_outputs = past
            decoder_cached_states = None
        elif len(past) == 2:
            encoder_outputs, decoder_cached_states = past
        else:
            raise ValueError(f"past must be of len 2 or 3, got len {len(past)} full past: {past}")

        # # first step
        # if len(past) < 2:
        #     encoder_outputs, decoder_cached_states = past, None
        # else:
        #     encoder_outputs, decoder_cached_states = past[0], past[1]
        assert (
            decoder_cached_states is None or decoder_cached_states
        ), f"decoder cached states must be None or a truthy list. got {decoder_cached_states}"

        return {
            "inputs": None,  # encoder_outputs is defined. input_ids not needed
            "encoder_outputs": encoder_outputs,
            "decoder_cached_states": decoder_cached_states,
            "decoder_input_ids": decoder_input_ids,
            "attention_mask": attention_mask,
            "use_cache": use_cache,  # change this to avoid caching (presumably for debugging)
        }

    def prepare_scores_for_generation(self, scores, cur_len, max_length):
        if cur_len == 1:
            self._force_token_ids_generation(scores, self.config.bos_token_id)
        if cur_len == max_length - 1 and self.config.eos_token_ids[0] is not None:
            self._force_token_ids_generation(scores, self.config.eos_token_ids[0])
        return scores

    @staticmethod
    def _reorder_cache(past, beam_idx):
        # return tuple(tf.gather(layer_past, beam_idx, axis=1) for layer_past in past)1
        # raise ValueError('hit _reorder_cache')
        ((enc_out, enc_mask, *trash), decoder_cached_states) = past

        reordered_past = []
        for layer_past in decoder_cached_states:
            # get the correct batch idx from decoder layer's batch dim for cross and self-attn
            layer_past_new = {
                attn_key: _reorder_buffer(attn_cache, beam_idx) for attn_key, attn_cache in layer_past.items()
            }
            reordered_past.append(layer_past_new)
        new_enc_out = enc_out if enc_out is None else tf.gather(enc_out, beam_idx, axis=0)
        new_enc_mask = enc_mask if enc_mask is None else tf.gather(enc_mask, beam_idx, axis=0)

        past = ((new_enc_out, new_enc_mask), reordered_past)
        return past

    def get_output_embeddings(self):
        return self.model.shared

    def get_encoder(self):
        return self.model.encoder


@add_start_docstrings(
    """Bart model with a sequence classification/head on top (a linear layer on top of the pooled output) e.g. for GLUE tasks. """,
    BART_START_DOCSTRING,
)
class TFBartForSequenceClassification(TFPretrainedBartModel):
    def __init__(self, config: BartConfig, **kwargs):
        super().__init__(config, **kwargs)
        self.model = TFBartModel(config)
        self.classification_head = BartClassificationHead(
            config.d_model, config.d_model, config.num_labels, config.classif_dropout,
        )

    @add_start_docstrings_to_callable(BART_INPUTS_DOCSTRING)
    def call(self, inputs: dict, **kwargs):
        r"""
        labels (:obj:`torch.LongTensor` of shape :obj:`(batch_size,)`, `optional`, defaults to :obj:`None`):
            Labels for computing the sequence classification/regression loss.
            Indices should be in :obj:`[0, ..., config.num_labels - 1]`.
            If :obj:`config.num_labels > 1` a classification loss is computed (Cross-Entropy).

    Returns:
        :obj:`tuple(torch.FloatTensor)` comprising various elements depending on the configuration (:class:`~transformers.BartConfig`) and inputs:
            logits (:obj:`torch.FloatTensor` of shape :obj:`(batch_size, config.num_labels)`):
                Classification (or regression if config.num_labels==1) scores (before SoftMax).
            hidden_states (:obj:`tuple(torch.FloatTensor)`, `optional`, returned when ``config.output_hidden_states=True``):
                Tuple of :obj:`torch.FloatTensor` (one for the output of the embeddings + one for the output of each layer)
                of shape :obj:`(batch_size, sequence_length, hidden_size)`.
                Hidden-states of the model at the output of each layer plus the initial embedding outputs.
            attentions (:obj:`tuple(torch.FloatTensor)`, `optional`, returned when ``config.output_attentions=True``):
                Tuple of :obj:`torch.FloatTensor` (one for each layer) of shape :obj:`(batch_size, num_heads, sequence_length, sequence_length)`.
                Attentions weights after the attention softmax, used to compute the weighted average in the
                self-attention
                heads.

    Examples::

        from transformers import BartTokenizer, BartForSequenceClassification
        import torch

        tokenizer = BartTokenizer.from_pretrained('bart-large')
        model = BartForSequenceClassification.from_pretrained('bart-large')
        input_ids = tf.Tensor(tokenizer.encode("Hello, my dog is cute",
        add_special_tokens=True)).unsqueeze(0)  # Batch size 1
        labels = tf.Tensor([1]).unsqueeze(0)  # Batch size 1
        outputs = model(input_ids, labels=labels)
        loss, logits = outputs[:2]

        """
        if isinstance(inputs, dict):
            kwargs.update(**inputs)
            input_ids = kwargs.pop("input_ids")  # KeyError possible
        else:
            assert isinstance(inputs, T)
            input_ids = inputs

        # attention_mask = kwargs.get("attention_mask", None)
        # encoder_outputs = kwargs.get("encoder_outputs", None)
        # decoder_input_ids = kwargs.get("decoder_input_ids", None)
        # decoder_attention_mask = kwargs.get("decoder_attention_mask", None)
        # decoder_cached_states = kwargs.get('decoder_cached_states', None)
        x, *other_outputs = self.model(input_ids, **kwargs)
        eos_mask = tf.math.equal(input_ids, self.config.eos_token_ids[0])
        if len(tf.unique(eos_mask.sum(1))) > 1:
            raise ValueError("All examples must have the same number of <eos> tokens.")
        sentence_representation = tf.reshape(x[eos_mask, :], (x.shape[0], -1, x.shape[-1]))[:, -1, :]
        logits = self.classification_head(sentence_representation)
        # Prepend logits
        outputs = (logits,) + other_outputs  # Add hidden states and attention if they are here
        return outputs
