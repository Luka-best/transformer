# coding=utf-8
# Copyright 2022 Microsoft Research and The HuggingFace Inc. team. All rights reserved.
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
""" TF 2.0 Swin Transformer model."""

import collections.abc
import math
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import tensorflow as tf

from ...activations_tf import ACT2FN
from ...modeling_tf_utils import TFPreTrainedModel, TFSequenceClassificationLoss, get_initializer
from ...utils import (
    ModelOutput,
    add_code_sample_docstrings,
    add_start_docstrings,
    add_start_docstrings_to_model_forward,
    logging,
    replace_return_docstrings,
)
from .configuration_swin import SwinConfig


logger = logging.get_logger(__name__)

# General docstring
_CONFIG_FOR_DOC = "SwinConfig"
_FEAT_EXTRACTOR_FOR_DOC = "AutoFeatureExtractor"

# Base docstring
_CHECKPOINT_FOR_DOC = "microsoft/swin-tiny-patch4-window7-224"
_EXPECTED_OUTPUT_SHAPE = [1, 49, 768]

# Image classification docstring
_IMAGE_CLASS_CHECKPOINT = "microsoft/swin-tiny-patch4-window7-224"
_IMAGE_CLASS_EXPECTED_OUTPUT = "tabby, tabby cat"


DUMMY_IMAGE_INPUTS = tf.random.normal((1, 3, 224, 224), seed=42) #FIXME - introduce proper dummies

TF_SWIN_PRETRAINED_MODEL_ARCHIVE_LIST = [
    "microsoft/swin-tiny-patch4-window7-224",
    # See all Swin models at https://huggingface.co/models?filter=swin
]

# to_2tuple, drop_path, SwinPatchEmbeddings, SwinPatchMerging and SwinDropPath are from the timm library.


@dataclass
class TFSwinEncoderOutput(ModelOutput):
    """
    Swin encoder's outputs, with potential hidden states and attentions.

    Args:
        last_hidden_state (`tf.Tensor` of shape `(batch_size, sequence_length, hidden_size)`):
            Sequence of hidden-states at the output of the last layer of the model.
        hidden_states (`tuple(tf.Tensor)`, *optional*, returned when `output_hidden_states=True` is passed or when `config.output_hidden_states=True`):
            Tuple of `tf.Tensor` (one for the output of the embeddings + one for the output of each stage) of
            shape `(batch_size, sequence_length, hidden_size)`.

            Hidden-states of the model at the output of each layer plus the initial embedding outputs.
        attentions (`tuple(torch.FloatTensor)`, *optional*, returned when `output_attentions=True` is passed or when `config.output_attentions=True`):
            Tuple of `torch.FloatTensor` (one for each stage) of shape `(batch_size, num_heads, sequence_length,
            sequence_length)`.

            Attentions weights after the attention softmax, used to compute the weighted average in the self-attention
            heads.
        reshaped_hidden_states (`tuple(tf.Tensor)`, *optional*, returned when `output_hidden_states=True` is passed or when `config.output_hidden_states=True`):
            Tuple of `tf.Tensor` (one for the output of the embeddings + one for the output of each stage) of
            shape `(batch_size, hidden_size, height, width)`.

            Hidden-states of the model at the output of each layer plus the initial embedding outputs reshaped to
            include the spatial dimensions.
    """

    last_hidden_state: tf.Tensor = None
    hidden_states: Optional[Tuple[tf.Tensor]] = None
    attentions: Optional[Tuple[tf.Tensor]] = None
    reshaped_hidden_states: Optional[Tuple[tf.Tensor]] = None


@dataclass
class TFSwinModelOutput(ModelOutput):
    """
    Swin model's outputs that also contains a pooling of the last hidden states.

    Args:
        last_hidden_state (`tf.Tensor` of shape `(batch_size, sequence_length, hidden_size)`):
            Sequence of hidden-states at the output of the last layer of the model.
        pooler_output (`tf.Tensor` of shape `(batch_size, hidden_size)`):
            Average pooling of the last layer hidden-state.
        hidden_states (`tuple(tf.Tensor)`, *optional*, returned when `output_hidden_states=True` is passed or when `config.output_hidden_states=True`):
            Tuple of `tf.Tensor` (one for the output of the embeddings + one for the output of each stage) of
            shape `(batch_size, sequence_length, hidden_size)`.

            Hidden-states of the model at the output of each layer plus the initial embedding outputs.
        attentions (`tuple(tf.Tensor)`, *optional*, returned when `output_attentions=True` is passed or when `config.output_attentions=True`):
            Tuple of `tf.Tensor` (one for each stage) of shape `(batch_size, num_heads, sequence_length,
            sequence_length)`.

            Attentions weights after the attention softmax, used to compute the weighted average in the self-attention
            heads.
        reshaped_hidden_states (`tuple(tf.Tensor)`, *optional*, returned when `output_hidden_states=True` is passed or when `config.output_hidden_states=True`):
            Tuple of `tf.Tensor` (one for the output of the embeddings + one for the output of each stage) of
            shape `(batch_size, hidden_size, height, width)`.

            Hidden-states of the model at the output of each layer plus the initial embedding outputs reshaped to
            include the spatial dimensions.
    """

    last_hidden_state: tf.Tensor = None
    pooler_output: tf.Tensor = None
    hidden_states: Optional[Tuple[tf.Tensor]] = None
    attentions: Optional[Tuple[tf.Tensor]] = None
    reshaped_hidden_states: Optional[Tuple[tf.Tensor]] = None


@dataclass
class TFSwinMaskedImageModelingOutput(ModelOutput):
    """
    Swin masked image model outputs.

    Args:
        loss (`tf.Tensor` of shape `(1,)`, *optional*, returned when `bool_masked_pos` is provided):
            Masked image modeling (MLM) loss.
        logits (`tf.Tensor` of shape `(batch_size, num_channels, height, width)`):
            Reconstructed pixel values.
        hidden_states (`tuple(tf.Tensor)`, *optional*, returned when `output_hidden_states=True` is passed or when `config.output_hidden_states=True`):
            Tuple of `tf.Tensor` (one for the output of the embeddings + one for the output of each stage) of
            shape `(batch_size, sequence_length, hidden_size)`.

            Hidden-states of the model at the output of each layer plus the initial embedding outputs.
        attentions (`tuple(tf.Tensor)`, *optional*, returned when `output_attentions=True` is passed or when `config.output_attentions=True`):
            Tuple of `tf.Tensor` (one for each stage) of shape `(batch_size, num_heads, sequence_length,
            sequence_length)`.

            Attentions weights after the attention softmax, used to compute the weighted average in the self-attention
            heads.
        reshaped_hidden_states (`tuple(tf.Tensor)`, *optional*, returned when `output_hidden_states=True` is passed or when `config.output_hidden_states=True`):
            Tuple of `tf.Tensor` (one for the output of the embeddings + one for the output of each stage) of
            shape `(batch_size, hidden_size, height, width)`.

            Hidden-states of the model at the output of each layer plus the initial embedding outputs reshaped to
            include the spatial dimensions.
    """

    loss: Optional[tf.Tensor] = None
    logits: tf.Tensor = None
    hidden_states: Optional[Tuple[tf.Tensor]] = None
    attentions: Optional[Tuple[tf.Tensor]] = None
    reshaped_hidden_states: Optional[Tuple[tf.Tensor]] = None


@dataclass
class TFSwinImageClassifierOutput(ModelOutput):
    """
    Swin outputs for image classification.

    Args:
        loss (`tf.Tensor` of shape `(1,)`, *optional*, returned when `labels` is provided):
            Classification (or regression if config.num_labels==1) loss.
        logits (`tf.Tensor` of shape `(batch_size, config.num_labels)`):
            Classification (or regression if config.num_labels==1) scores (before SoftMax).
        hidden_states (`tuple(tf.Tensor)`, *optional*, returned when `output_hidden_states=True` is passed or when `config.output_hidden_states=True`):
            Tuple of `tf.Tensor` (one for the output of the embeddings + one for the output of each stage) of
            shape `(batch_size, sequence_length, hidden_size)`.

            Hidden-states of the model at the output of each layer plus the initial embedding outputs.
        attentions (`tuple(tf.Tensor)`, *optional*, returned when `output_attentions=True` is passed or when `config.output_attentions=True`):
            Tuple of `tf.Tensor` (one for each stage) of shape `(batch_size, num_heads, sequence_length,
            sequence_length)`.

            Attentions weights after the attention softmax, used to compute the weighted average in the self-attention
            heads.
        reshaped_hidden_states (`tuple(tf.Tensor)`, *optional*, returned when `output_hidden_states=True` is passed or when `config.output_hidden_states=True`):
            Tuple of `tf.Tensor` (one for the output of the embeddings + one for the output of each stage) of
            shape `(batch_size, hidden_size, height, width)`.

            Hidden-states of the model at the output of each layer plus the initial embedding outputs reshaped to
            include the spatial dimensions.
    """

    loss: Optional[tf.Tensor] = None
    logits: tf.Tensor = None
    hidden_states: Optional[Tuple[tf.Tensor]] = None
    attentions: Optional[Tuple[tf.Tensor]] = None
    reshaped_hidden_states: Optional[Tuple[tf.Tensor]] = None


# # Copied from transformers.models.vit.modeling_tf_vit.to_2tuple
def to_2tuple(x):
    if isinstance(x, collections.abc.Iterable):
        return x
    return (x, x)


def window_partition(input_feature, window_size): #FIXME AR
    """
    Partitions the given input into windows.
    """
    batch_size, height, width, num_channels = input_feature.shape
    input_feature = tf.reshape(
        input_feature,
        (batch_size, height // window_size, window_size, width // window_size, window_size, num_channels)
    )
    windows = tf.transpose(input_feature, (0, 1, 3, 2, 4, 5))
    windows = tf.reshape(windows, (-1, window_size, window_size, num_channels))
    return windows


def window_reverse(windows, window_size, height, width):
    """
    Merges windows to produce higher resolution features.
    """
    batch_size = int(windows.shape[0] / (height * width / window_size / window_size))
    windows = tf.reshape(
        windows,
        (batch_size, height // window_size, width // window_size, window_size, window_size, -1)
    )
    windows = tf.transpose(windows, (0, 1, 3, 2, 4, 5))
    windows = tf.reshape(windows, (batch_size, height, width, -1))
    return windows


def drop_path(input, drop_prob=0.0, training=False, scale_by_keep=True):
    """
    Drop paths (Stochastic Depth) per sample (when applied in main path of residual blocks).
    """
    if drop_prob == 0.0 or not training:
        return input
    keep_prob = 1 - drop_prob
    shape = (input.shape[0],) + (1,) * (input.ndim - 1)  # work with diff dim tensors, not just 2D ConvNets
    random_tensor = input.new_empty(shape).bernoulli_(keep_prob)
    if keep_prob > 0.0 and scale_by_keep:
        random_tensor.div_(keep_prob)
    return input * random_tensor


class TFSwinEmbeddings(tf.keras.layers.Layer):
    """
    Construct the patch and position embeddings. Optionally, also the mask token.
    """

    def __init__(self, config, use_mask_token=False):
        super().__init__()
        self.patch_embeddings = TFSwinPatchEmbeddings(
            image_size=config.image_size,
            patch_size=config.patch_size,
            num_channels=config.num_channels,
            embed_dim=config.embed_dim,
        )
        self.num_patches = self.patch_embeddings.num_patches
        self.patch_grid = self.patch_embeddings.grid_size
        self.embed_dim = config.embed_dim
        self.use_mask_token = use_mask_token
        self.use_absolute_embeddings = config.use_absolute_embeddings

        self.norm = tf.keras.layers.LayerNormalization() #FIXME
        self.dropout = tf.keras.layers.Dropout(config.hidden_dropout_prob) #FIXME

    def build(self, input_shape):
        if self.use_mask_token:
            self.mask_token = self.add_weight(shape=(1, 1, self.embed_dim), initializer="zeros") # FIXME - trainable?
        else:
            self.mask_token = None

        if self.use_absolute_embeddings:
            self.position_embeddings = self.add_weight((1, self.num_patches + 1, self.embed_dim), initializer="zeros")
        else:
            self.position_embeddings = None
        super().build(input_shape)

    def call(self, pixel_values, bool_masked_pos=None, training=False):
        embeddings, output_dimensions = self.patch_embeddings(pixel_values) #FIXME - take dict values?
        embeddings = self.norm(embeddings)
        batch_size, seq_len, _ = embeddings.shape

        if bool_masked_pos is not None:
            mask_tokens = self.mask_token.expand(batch_size, seq_len, -1)
            # replace the masked visual tokens by mask_tokens
            mask = tf.expand_dims(bool, -1)
            mask = tf.cast(mask, mask_tokens.dtype)
            mask = bool_masked_pos

            embeddings = embeddings * (1.0 - mask) + mask_tokens * mask

        if self.position_embeddings is not None:
            embeddings = embeddings + self.position_embeddings

        embeddings = self.dropout(embeddings, training=training)

        return embeddings, output_dimensions


class TFSwinPatchEmbeddings(tf.keras.layers.Layer):
    """
    Image to Patch Embedding.
    """

    def __init__(self, image_size=224, patch_size=16, num_channels=3, embed_dim=768):
        super().__init__()
        image_size = to_2tuple(image_size)
        patch_size = to_2tuple(patch_size)
        num_patches = (image_size[1] // patch_size[1]) * (image_size[0] // patch_size[0])
        self.image_size = image_size
        self.patch_size = patch_size
        self.num_patches = num_patches
        self.grid_size = (image_size[0] // patch_size[0], image_size[1] // patch_size[1])

        self.projection = tf.keras.layers.Conv2D(
            filters=embed_dim,
            kernel_size=self.patch_size,
            strides=self.patch_size,
            padding='valid',
        ) #FIXME

    def maybe_pad(self, pixel_values, height, width):
        if width % self.patch_size[1] != 0:
            pad_values = (0, self.patch_size[1] - width % self.patch_size[1])
            pixel_values = tf.pad(pixel_values, pad_values) #FIXME
        if height % self.patch_size[0] != 0:
            pad_values = (0, 0, 0, self.patch_size[0] - height % self.patch_size[0])
            pixel_values = tf.pad(pixel_values, pad_values) #FIXME
        return pixel_values

    def call(self, pixel_values):
        _, _, height, width = pixel_values.shape
        # pad the input to be divisible by self.patch_size, if needed
        pixel_values = self.maybe_pad(pixel_values, height, width)

        # FIXME - how to handle different channel orders?
        pixel_values = tf.transpose(pixel_values, (0, 2, 3, 1))

        embeddings = self.projection(pixel_values)

        # FIXME - reorder channel again?
        embeddings = tf.transpose(embeddings, (0, 3, 1, 2))

        _, _, height, width = embeddings.shape
        output_dimensions = (height, width)

        embeddings = tf.reshape(embeddings, (embeddings.shape[0], embeddings.shape[1], -1))
        embeddings = tf.transpose(embeddings, (0, 2, 1))
        return embeddings, output_dimensions


class TFSwinPatchMerging(tf.keras.layers.Layer):
    """
    Patch Merging Layer.

    Args:
        input_resolution (`Tuple[int]`):
            Resolution of input feature.
        dim (`int`):
            Number of input channels.
        norm_layer (`tf.keras.layer.Layer`, *optional*, defaults to `tf.keras.layers.LayerNormalization`):
            Normalization layer class.
    """

    def __init__(self, input_resolution, dim, norm_layer=None): #FIXME
        super().__init__()
        self.input_resolution = input_resolution
        self.dim = dim
        #FIXME
        self.reduction = tf.keras.layers.Dense(2 * dim, use_bias=False)
        self.norm = norm_layer()

    def maybe_pad(self, input_feature, height, width):
        should_pad = (height % 2 == 1) or (width % 2 == 1)
        if should_pad:
            pad_values = (0, 0, 0, width % 2, 0, height % 2)
            input_feature = tf.pad(input_feature, pad_values) #FIXME

        return input_feature

    def call(self, input_feature, input_dimensions):
        height, width = input_dimensions
        # `dim` is height * width
        batch_size, dim, num_channels = input_feature.shape

        input_feature = tf.reshape(input_feature, (batch_size, height, width, num_channels))
        # pad input to be disible by width and height, if needed
        input_feature = self.maybe_pad(input_feature, height, width)
        # [batch_size, height/2, width/2, num_channels]
        input_feature_0 = input_feature[:, 0::2, 0::2, :]
        # [batch_size, height/2, width/2, num_channels]
        input_feature_1 = input_feature[:, 1::2, 0::2, :]
        # [batch_size, height/2, width/2, num_channels]
        input_feature_2 = input_feature[:, 0::2, 1::2, :]
        # [batch_size, height/2, width/2, num_channels]
        input_feature_3 = input_feature[:, 1::2, 1::2, :]
        # batch_size height/2 width/2 4*num_channels
        input_feature = tf.concat([input_feature_0, input_feature_1, input_feature_2, input_feature_3], -1) #FIXME
        input_feature = tf.reshape(input_feature, (batch_size, -1, 4 * num_channels)) # batch_size height/2*width/2 4*C

        input_feature = self.norm(input_feature)
        input_feature = self.reduction(input_feature)

        return input_feature


class TFSwinDropPath(tf.keras.layers.Layer):
    """Drop paths (Stochastic Depth) per sample (when applied in main path of residual blocks)."""

    def __init__(self, drop_prob=None, scale_by_keep=True):
        super(TFSwinDropPath, self).__init__()
        self.drop_prob = drop_prob
        self.scale_by_keep = scale_by_keep

    def call(self, input, training=False):
        return drop_path(input, self.drop_prob, training, self.scale_by_keep)


class TFSwinSelfAttention(tf.keras.layers.Layer):
    def __init__(
        self,
        config: SwinConfig,
        dim: int,
        num_heads: int,
    ):
        super().__init__()
        if dim % num_heads != 0:
            raise ValueError(
                f"The hidden size ({dim}) is not a multiple of the number of attention " f"heads ({num_heads})"
            )

        self.num_attention_heads = num_heads
        self.attention_head_size = int(dim / num_heads)
        self.all_head_size = self.num_attention_heads * self.attention_head_size
        self.window_size = to_2tuple(config.window_size)

        # get pair-wise relative position index for each token inside the window
        #FIXME
        coords_h = tf.range(self.window_size[0])
        coords_w = tf.range(self.window_size[1])
        coords = tf.stack(tf.meshgrid(coords_h, coords_w, indexing='ij'))
        coords_flatten = tf.reshape(coords, (coords.shape[0], -1))
        relative_coords = coords_flatten[:, :, None] - coords_flatten[:, None, :]
        relative_coords = tf.transpose(relative_coords, (1, 2, 0)) #FIXME
        #FIXME - better names and computation
        stack_0, stack_1 = tf.unstack(relative_coords, axis=2)
        stack_0 += self.window_size[0] - 1
        stack_0 *= 2 * self.window_size[1] - 1
        stack_1 += self.window_size[1] - 1
        relative_coords = tf.stack([stack_0, stack_1], axis=2)
        self.relative_position_index = tf.reduce_sum(relative_coords, axis=-1)
        # self.register_buffer("relative_position_index", relative_position_index) #FIXME !!!!

        self.query = tf.keras.layers.Dense(
            self.all_head_size,
            kernel_initializer=get_initializer(config.initializer_range),
            use_bias=config.qkv_bias)
        self.key = tf.keras.layers.Dense(
            self.all_head_size,
            kernel_initializer=get_initializer(config.initializer_range),
            use_bias=config.qkv_bias)
        self.value = tf.keras.layers.Dense(
            self.all_head_size,
            kernel_initializer=get_initializer(config.initializer_range),
            use_bias=config.qkv_bias)

        self.dropout = tf.keras.layers.Dropout(config.attention_probs_dropout_prob)

    def build(self, input_shape):
        self.relative_position_bias_table = self.add_weight(
            shape=(((2 * self.window_size[0] - 1) * (2 * self.window_size[1] - 1)), self.num_attention_heads),
            initializer="zeros"
        ) #FIXME
        super().build(input_shape)

    def transpose_for_scores(self, x):
        new_x_shape = x.shape[:-1] + (self.num_attention_heads, self.attention_head_size)
        x = tf.reshape(x, new_x_shape)
        return tf.transpose(x, (0, 2, 1, 3))

    def call(
        self,
        hidden_states,
        attention_mask=None,
        head_mask=None,
        output_attentions=False,
        training=False
    ):
        batch_size, dim, num_channels = hidden_states.shape
        mixed_query_layer = self.query(hidden_states)

        key_layer = self.transpose_for_scores(self.key(hidden_states))
        value_layer = self.transpose_for_scores(self.value(hidden_states))
        query_layer = self.transpose_for_scores(mixed_query_layer)

        # Take the dot product between "query" and "key" to get the raw attention scores.
        attention_scores = tf.matmul(
            query_layer,
            tf.transpose(key_layer, (0, 1, 3, 2)) #FIXME - make more general?
        )

        attention_scores = attention_scores / math.sqrt(self.attention_head_size)
        relative_position_bias = tf.gather(self.relative_position_bias_table, tf.reshape(self.relative_position_index, -1)) # FIXME - double check dimensions
        relative_position_bias = tf.reshape(
            relative_position_bias,
            (self.window_size[0] * self.window_size[1], self.window_size[0] * self.window_size[1], -1)
        )

        relative_position_bias = tf.transpose(relative_position_bias, (2, 0, 1)) #FIXME
        attention_scores = attention_scores + tf.expand_dims(relative_position_bias, 0)

        if attention_mask is not None:
            # Apply the attention mask is (precomputed for all layers in SwinModel forward() function)
            mask_shape = attention_mask.shape[0]
            attention_scores = tf.reshape(
                attention_scores,
                (batch_size // mask_shape, mask_shape, self.num_attention_heads, dim, dim)
            )
            attention_mask = tf.expand_dims(attention_mask, 1)
            attention_mask = tf.expand_dims(attention_mask, 0)
            attention_scores = attention_scores + attention_mask
            attention_scores = tf.reshape(attention_scores, (-1, self.num_attention_heads, dim, dim))

        # Normalize the attention scores to probabilities.
        attention_probs = tf.nn.softmax(attention_scores, axis=-1) #FIXME - double check calculation is same

        # This is actually dropping out entire tokens to attend to, which might
        # seem a bit unusual, but is taken from the original Transformer paper.
        attention_probs = self.dropout(attention_probs, training=training)

        # Mask heads if we want to
        if head_mask is not None:
            attention_probs = attention_probs * head_mask

        context_layer = tf.matmul(attention_probs, value_layer)
        context_layer = tf.transpose(context_layer, (0, 2, 1, 3)) #FIXME
        new_context_layer_shape = context_layer.shape[:-2] + (self.all_head_size,)
        context_layer = tf.reshape(context_layer, new_context_layer_shape)

        outputs = (context_layer, attention_probs) if output_attentions else (context_layer,)

        return outputs


class TFSwinSelfOutput(tf.keras.layers.Layer):
    def __init__(self, config: SwinConfig, dim: int):
        super().__init__()
        self.dense = tf.keras.layers.Dense(dim)
        self.dropout = tf.keras.layers.Dropout(config.attention_probs_dropout_prob)

    def call(self, hidden_states, input_tensor, training=False):
        hidden_states = self.dense(hidden_states)
        hidden_states = self.dropout(hidden_states, training=training)
        return hidden_states


class TFSwinAttention(tf.keras.layers.Layer):
    pass
    def __init__(self, config, dim, num_heads):
        super().__init__()
        self.self = TFSwinSelfAttention(config, dim, num_heads)
        self.self_output = TFSwinSelfOutput(config, dim)
        self.pruned_heads = set()

    def prune_heads(self, heads):
        """
        Prunes heads of the model. See base class PreTrainedModel
        heads: dict of {layer_num: list of heads to prune in this layer}
        """
        raise NotImplementedError

    def call(self, hidden_states, attention_mask=None, head_mask=None, output_attentions=False, training=False):
        self_outputs = self.self(hidden_states, attention_mask, head_mask, output_attentions, training=training)
        attention_output = self.self_output(self_outputs[0], hidden_states, training=training)
        outputs = (attention_output,) + self_outputs[1:]  # add attentions if we output them
        return outputs

class TFSwinIntermediate(tf.keras.layers.Layer):
    def __init__(self, config, dim):
        super().__init__()
        self.dense = tf.keras.layers.Dense(int(config.mlp_ratio * dim))
        if isinstance(config.hidden_act, str):
            self.intermediate_act_fn = ACT2FN[config.hidden_act]
        else:
            self.intermediate_act_fn = config.hidden_act

    def call(self, hidden_states):
        hidden_states = self.dense(hidden_states)
        hidden_states = self.intermediate_act_fn(hidden_states)
        return hidden_states


class TFSwinOutput(tf.keras.layers.Layer):
    def __init__(self, config: SwinConfig, dim: int):
        super().__init__()
        self.dense = tf.keras.layers.Dense(dim)
        self.dropout = tf.keras.layers.Dropout(config.hidden_dropout_prob)

    def call(self, hidden_states, training=False):
        hidden_states = self.dense(hidden_states)
        hidden_states = self.dropout(hidden_states, training=training)
        return hidden_states


class TFSwinLayer(tf.keras.layers.Layer):
    def __init__(self, config, dim, input_resolution, num_heads, shift_size=0):
        super().__init__()
        self.chunk_size_feed_forward = config.chunk_size_feed_forward
        self.shift_size = shift_size
        self.window_size = config.window_size
        self.input_resolution = input_resolution
        self.set_shift_and_window_size(input_resolution)

        self.layernorm_before = tf.keras.layers.LayerNormalization(epsilon=config.layer_norm_eps) #FIXME
        self.attention = TFSwinAttention(config, dim, num_heads)
        self.drop_path = TFSwinDropPath(config.drop_path_rate) if config.drop_path_rate > 0.0 else tf.identity()
        self.layernorm_after = tf.keras.layers.LayerNormalization(epsilon=config.layer_norm_eps)
        self.intermediate = TFSwinIntermediate(config, dim)
        self.swin_output = TFSwinOutput(config, dim)

    def set_shift_and_window_size(self, input_resolution):
        if min(input_resolution) <= self.window_size:
            # if window size is larger than input resolution, we don't partition windows
            self.shift_size = 0
            self.window_size = min(input_resolution)

    def get_attn_mask(self, height, width):
        if self.shift_size > 0:
            # calculate attention mask for SW-MSA
            # img_mask = tf.zeros((1, height, width, 1)) #FIXME - add back in these dimenstions
            img_mask = tf.zeros((height, width))
            height_slices = (
                (0, -self.window_size),
                (-self.window_size, -self.shift_size),
                (-self.shift_size, -1), #FIXME - double check -1 versus None
            )
            width_slices = (
                (0, -self.window_size),
                (-self.window_size, -self.shift_size),
                (-self.shift_size, -1), #FIXME - double check -1 versus None
            )

            count = 0
            for height_slice in height_slices:
                for width_slice in width_slices:
                    indices = [
                        [i, j]
                        for i in range(height_slice[0] % height, height_slice[1] % height)
                        for j in range(width_slice[0] % width, width_slice[1] % width)
                    ] #FIXME - find indices in a better way
                    updates = tf.ones((len(indices),), dtype=img_mask.dtype) * count
                    img_mask = tf.tensor_scatter_nd_update(img_mask, indices, updates)
                    # img_mask[:, height_slice, width_slice, :] = count
                    count += 1

            img_mask = tf.expand_dims(img_mask, -1) #FIXME - have dimensions at the start
            img_mask = tf.expand_dims(img_mask, 0)

            mask_windows = window_partition(img_mask, self.window_size)
            mask_windows = tf.reshape(mask_windows, (-1, self.window_size * self.window_size))
            attn_mask = tf.expand_dims(mask_windows, 1) - tf.expand_dims(mask_windows, 2)
            attn_mask = tf.where(attn_mask != 0, attn_mask, float(-100.0))
            attn_mask = tf.where(attn_mask == 0, attn_mask, float(0.0))
        else:
            attn_mask = None
        return attn_mask

    def maybe_pad(self, hidden_states, height, width):
        pad_right = (self.window_size - width % self.window_size) % self.window_size
        pad_bottom = (self.window_size - height % self.window_size) % self.window_size
        pad_values = tf.constant([
            [0, 0],
            [0, pad_bottom],
            [0, pad_right],
            [0, 0],
        ]) #FIXME - double check dimensions and padding
        hidden_states = tf.pad(hidden_states, pad_values)
        pad_values = tf.reshape(pad_values, -1)
        return hidden_states, pad_values

    def call(self, hidden_states, input_dimensions, head_mask=None, output_attentions=False, training=False):
        self.set_shift_and_window_size(input_dimensions)
        height, width = input_dimensions
        batch_size, _, channels = hidden_states.shape
        shortcut = hidden_states

        hidden_states = self.layernorm_before(hidden_states)
        hidden_states = tf.reshape(hidden_states, (batch_size, height, width, channels))
        # pad hidden_states to multiples of window size
        hidden_states, pad_values = self.maybe_pad(hidden_states, height, width)

        _, height_pad, width_pad, _ = hidden_states.shape
        # cyclic shift
        if self.shift_size > 0:
            shifted_hidden_states = tf.roll(hidden_states, shift=(-self.shift_size, -self.shift_size), axis=(1, 2))
        else:
            shifted_hidden_states = hidden_states

        # partition windows
        hidden_states_windows = window_partition(shifted_hidden_states, self.window_size)
        hidden_states_windows = tf.reshape(hidden_states_windows, (-1, self.window_size * self.window_size, channels))
        attn_mask = self.get_attn_mask(height_pad, width_pad)


        attention_outputs = self.attention(
            hidden_states_windows, attn_mask, head_mask, output_attentions=output_attentions, training=training
        )

        attention_output = attention_outputs[0]

        attention_windows = tf.reshape(attention_output, (-1, self.window_size, self.window_size, channels))
        shifted_windows = window_reverse(attention_windows, self.window_size, height_pad, width_pad)

#         # reverse cyclic shift
        if self.shift_size > 0:
            attention_windows = tf.roll(shifted_windows, shift=(self.shift_size, self.shift_size), axis=(1, 2))
        else:
            attention_windows = shifted_windows

        was_padded = pad_values[3] > 0 or pad_values[5] > 0 #FIXME - double check indexing
        if was_padded:
            attention_windows = attention_windows[:, :height, :width, :] #FIXME

        attention_windows = tf.reshape(attention_windows, (batch_size, height * width, channels))

        hidden_states = shortcut + self.drop_path(attention_windows)

        layer_output = self.layernorm_after(hidden_states, training=training)
        layer_output = self.intermediate(layer_output, training=training)
        layer_output = hidden_states + self.swin_output(layer_output, training=training)

        layer_outputs = (layer_output, attention_outputs[1]) if output_attentions else (layer_output,)
        return layer_outputs


class TFSwinStage(tf.keras.layers.Layer):
    def __init__(self, config, dim, input_resolution, depth, num_heads, drop_path, downsample):
        super().__init__()
        self.config = config
        self.dim = dim
        self.blocks = [
            TFSwinLayer(
                config=config,
                dim=dim,
                input_resolution=input_resolution,
                num_heads=num_heads,
                shift_size=0 if (i % 2 == 0) else config.window_size // 2,
            )
            for i in range(depth)
        ]

        # patch merging layer
        if downsample is not None:
            self.downsample = downsample(input_resolution, dim=dim, norm_layer=tf.keras.layers.LayerNormalization)
        else:
            self.downsample = None

        self.pointing = False

    def call(self, hidden_states, input_dimensions, head_mask=None, output_attentions=False, training=False):
        height, width = input_dimensions
        for i, layer_module in enumerate(self.blocks):
            layer_head_mask = head_mask[i] if head_mask is not None else None

            layer_outputs = layer_module(hidden_states, input_dimensions, layer_head_mask, output_attentions, training=training)

            hidden_states = layer_outputs[0]

        if self.downsample is not None:
            height_downsampled, width_downsampled = (height + 1) // 2, (width + 1) // 2
            output_dimensions = (height, width, height_downsampled, width_downsampled)
            hidden_states = self.downsample(layer_outputs[0], input_dimensions)
        else:
            output_dimensions = (height, width, height, width)

        stage_outputs = (hidden_states, output_dimensions)

        if output_attentions:
            stage_outputs += layer_outputs[1:]
        return stage_outputs


class TFSwinEncoder(tf.keras.layers.Layer):
    def __init__(self, config, grid_size):
        super().__init__()
        self.num_layers = len(config.depths)
        self.config = config
        dpr = list((tf.linspace(0, 1, sum(config.depths)) * config.drop_path_rate).numpy()) #FIXME
        self.layers = [
            TFSwinStage(
                config=config,
                dim=int(config.embed_dim * 2**i_layer),
                input_resolution=(grid_size[0] // (2**i_layer), grid_size[1] // (2**i_layer)),
                depth=config.depths[i_layer],
                num_heads=config.num_heads[i_layer],
                drop_path=dpr[sum(config.depths[:i_layer]) : sum(config.depths[: i_layer + 1])],
                downsample=TFSwinPatchMerging if (i_layer < self.num_layers - 1) else None,
            )
            for i_layer in range(self.num_layers)
        ]

        self.gradient_checkpointing = False

    def call(
        self,
        hidden_states,
        input_dimensions,
        head_mask=None,
        output_attentions=False,
        output_hidden_states=False,
        return_dict=True,
    ):
        all_input_dimensions = ()
        all_hidden_states = () if output_hidden_states else None
        all_reshaped_hidden_states = () if output_hidden_states else None
        all_self_attentions = () if output_attentions else None

        if output_hidden_states:
            batch_size, _, hidden_size = hidden_states.shape
            # rearrange b (h w) c -> b c h w
            reshaped_hidden_state = tf.reshape(hidden_states, (batch_size, *input_dimensions, hidden_size))
            reshaped_hidden_state = tf.transpose(reshaped_hidden_state, (0, 3, 1, 2)) #FIXME
            all_hidden_states += (hidden_states,)
            all_reshaped_hidden_states += (reshaped_hidden_state,)

        for i, layer_module in enumerate(self.layers):
            layer_head_mask = head_mask[i] if head_mask is not None else None

#             if self.gradient_checkpointing and self.training:

#                 def create_custom_forward(module):
#                     def custom_forward(*inputs):
#                         return module(*inputs, output_attentions)

#                     return custom_forward

# #                 layer_outputs = torch.utils.checkpoint.checkpoint(
# #                     create_custom_forward(layer_module), hidden_states, input_dimensions, layer_head_mask
# #                 )
# #             else:
            #FIXME
            layer_outputs = layer_module(hidden_states, input_dimensions, layer_head_mask, output_attentions)

            hidden_states = layer_outputs[0]
            output_dimensions = layer_outputs[1]

            input_dimensions = (output_dimensions[-2], output_dimensions[-1])
            all_input_dimensions += (input_dimensions,)

            if output_hidden_states:
                batch_size, _, hidden_size = hidden_states.shape
                # rearrange b (h w) c -> b c h w
                reshaped_hidden_state = tf.reshape(batch_size, (*input_dimensions, hidden_size))
                reshaped_hidden_state = tf.transpose(reshaped_hidden_state, (0, 3, 1, 2)) #FIXME
                all_hidden_states += (hidden_states,)
                all_reshaped_hidden_states += (reshaped_hidden_state,)

            if output_attentions:
                all_self_attentions += layer_outputs[2:]

        if not return_dict:
            return tuple(v for v in [hidden_states, all_hidden_states, all_self_attentions] if v is not None)

        return TFSwinEncoderOutput(
            last_hidden_state=hidden_states,
            hidden_states=all_hidden_states,
            attentions=all_self_attentions,
            reshaped_hidden_states=all_reshaped_hidden_states,
        )


class TFSwinPreTrainedModel(TFPreTrainedModel):
    """
    An abstract class to handle weights initialization and a simple interface for downloading and loading pretrained
    models.
    """

    config_class = SwinConfig
    base_model_prefix = "swin"
    main_input_name = "pixel_values"
    supports_gradient_checkpointing = True

#     def _init_weights(self, module): #FIXME - add in TF initialisation of weights
#         """Initialize the weights"""
#         if isinstance(module, (tf.keras.layers.Dense, tf.keras.layers.Conv2D)):
# #             # Slightly different from the TF version which uses truncated_normal for initialization
# #             # cf https://github.com/pytorch/pytorch/pull/5617 #FIXME
#             module.weight.data.normal_(mean=0.0, std=self.config.initializer_range)
# #             if module.bias is not None:
# #                 module.bias.data.zero_()
# #         elif isinstance(module, nn.LayerNorm):
# #             module.bias.data.zero_()
# #             module.weight.data.fill_(1.0)

    def _set_gradient_checkpointing(self, module, value=False):
        if isinstance(module, TFSwinEncoder):
            module.gradient_checkpointing = value


class TFSwinModel(TFSwinPreTrainedModel):
    def __init__(
        self, config,
        add_pooling_layer=False, # True, #FIXME !!!!!!! - add in the pooling layer
        use_mask_token=False
    ):
        super().__init__(config)
        self.config = config
        self.num_layers = len(config.depths)
        self.num_features = int(config.embed_dim * 2 ** (self.num_layers - 1))

        self.embeddings = TFSwinEmbeddings(config, use_mask_token=use_mask_token)
        self.encoder = TFSwinEncoder(config, self.embeddings.patch_grid)

        self.layernorm = tf.keras.layers.LayerNormalization(epsilon=config.layer_norm_eps)
        self.pooler = None #nn.AdaptiveAvgPool1d(1) if add_pooling_layer else None

#         # Initialize weights and apply final processing
#         self.post_init() #FIXME

    def get_input_embeddings(self):
        return self.embeddings.patch_embeddings

    def _prune_heads(self, heads_to_prune):
        """
        Prunes heads of the model. heads_to_prune: dict of {layer_num: list of heads to prune in this layer} See base
        class PreTrainedModel
        """
        for layer, heads in heads_to_prune.items():
            self.encoder.layer[layer].attention.prune_heads(heads)

    def call(
        self,
        pixel_values=None,
        bool_masked_pos=None,
        head_mask=None,
        output_attentions=None,
        output_hidden_states=None,
        return_dict=None,
        training=False
    ):
        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )
        return_dict = return_dict if return_dict is not None else self.config.use_return_dict

        if pixel_values is None:
            raise ValueError("You have to specify pixel_values")

        # Prepare head mask if needed
        # 1.0 in head_mask indicate we keep the head
        # attention_probs has shape bsz x n_heads x N x N
        # input head_mask has shape [num_heads] or [num_hidden_layers x num_heads]
        # and head_mask is converted to shape [num_hidden_layers x batch x num_heads x seq_length x seq_length]
        if head_mask is not None:
            raise NotImplementedError
        else:
            head_mask = [None] * len(self.config.depths)
        # head_mask = self.get_head_mask(head_mask, len(self.config.depths)) #FIXME
        embedding_output, input_dimensions = self.embeddings(pixel_values, bool_masked_pos=bool_masked_pos, training=training)

        encoder_outputs = self.encoder(
            embedding_output,
            input_dimensions,
            head_mask=head_mask,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
            training=training
        )

        sequence_output = encoder_outputs[0]
        sequence_output = self.layernorm(sequence_output)

        pooled_output = None
        if self.pooler is not None:
            pooled_output = self.pooler(sequence_output.transpose(1, 2), training=training)
            pooled_output = tf.reshape(pooled_output, (-1, 1))

        if not return_dict:
            output = (sequence_output, pooled_output) + encoder_outputs[1:]

            return output

        return TFSwinModelOutput(
            last_hidden_state=sequence_output,
            pooler_output=pooled_output,
            hidden_states=encoder_outputs.hidden_states,
            attentions=encoder_outputs.attentions,
            reshaped_hidden_states=encoder_outputs.reshaped_hidden_states,
        )


# FIXME
class PixelShuffle(tf.keras.layers.Layer):
    """TF layer implementation of torch.nn.PixelShuffle"""
    def __init__(
        self,
        upscale_factor,
        data_format="NHWC", #FIXME -set up order of channels
        trainable=True,
        name=None,
        dtype=None,
        dynamic=False,
        **kwargs
    ):
        super().__init__(trainable, name, dtype, dynamic, **kwargs)
        if upscale_factor < 2:
            raise ValueError("upscale_factor must be an integer value >= 2")
        self.upscale_factor = upscale_factor
        self.data_format = data_format

    def call(self, x):
        return tf.nn.depth_to_space(x, block_size=self.upscale_factor, data_format=self.data_format)


class TFSwinForMaskedImageModeling(TFSwinPreTrainedModel):
    def __init__(self, config):
        super().__init__(config)

        self.swin = TFSwinModel(config, add_pooling_layer=False, use_mask_token=True)

        num_features = int(config.embed_dim * 2 ** (config.num_layers - 1))
        self.decoder = tf.keras.Sequential([
            tf.keras.layers.Conv2D(
                filters=config.encoder_stride**2 * 3,
                kernel_size=1,
                strides=1
            ),
            PixelShuffle(config.encoder_stride) #FIXME
        ])

        # Initialize weights and apply final processing
        # self.post_init() #FIXME

    @property
    def dummy_inputs(self) -> Dict[str, tf.Tensor]: #FIXME - change defaul the dummy inputs
        return DUMMY_IMAGE_INPUTS

    def call(
        self,
        pixel_values=None,
        bool_masked_pos=None,
        head_mask=None,
        output_attentions=None,
        output_hidden_states=None,
        return_dict=None,
        training=False
    ):
        return_dict = return_dict if return_dict is not None else self.config.use_return_dict

        outputs = self.swin(
            pixel_values,
            bool_masked_pos=bool_masked_pos,
            head_mask=head_mask,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
            training=training
        )

        sequence_output = outputs[0]
        # Reshape to (batch_size, num_channels, height, width)
        sequence_output = tf.transpose(sequence_output, (0, 2, 1)) #FIXME - double check dimensions
        batch_size, num_channels, sequence_length = sequence_output.shape
        height = width = int(sequence_length**0.5)
        sequence_output = tf.reshape(sequence_output, (batch_size, num_channels, height, width))

        # Reconstruct pixel values
        #FIXME - check channel order and output dimensions
        sequence_output = tf.transpose(sequence_output, (0, 2, 3, 1))
        reconstructed_pixel_values = self.decoder(sequence_output)
        reconstructed_pixel_values = tf.transpose(reconstructed_pixel_values, (0, 3, 1, 2))

        masked_im_loss = None
        if bool_masked_pos is not None:
            size = self.config.image_size // self.config.patch_size
            bool_masked_pos = bool_masked_pos.reshape(-1, size, size)
            mask = tf.repeat(bool_masked_pos, self.config.patch_size, 1)
            mask = tf.repeat(mask, self.config.patch_size, 2)
            mask = tf.expand_dims(mask, 1)
            #FIXME - make sure reduction isn't happening
            reconstruction_loss = tf.keras.losses.mean_absolute_error(pixel_values, reconstructed_pixel_values)
            masked_im_loss = (reconstruction_loss * mask).sum() / (mask.sum() + 1e-5) / self.config.num_channels

        if not return_dict:
            output = (reconstructed_pixel_values,) + outputs[2:]
            return ((masked_im_loss,) + output) if masked_im_loss is not None else output

        return TFSwinMaskedImageModelingOutput(
            loss=masked_im_loss,
            logits=reconstructed_pixel_values,
            hidden_states=outputs.hidden_states,
            attentions=outputs.attentions,
            reshaped_hidden_states=outputs.reshaped_hidden_states,
        )


class TFSwinForImageClassification(TFSwinPreTrainedModel, TFSequenceClassificationLoss):
    def __init__(self, config):
        super().__init__(config)

        self.num_labels = config.num_labels
        self.swin = TFSwinModel(config)

        # Classifier head
        self.classifier = (
            tf.keras.layers.Dense(config.num_labels) if config.num_labels > 0 else tf.identity()
        )

        # Initialize weights and apply final processing
        # self.post_init() #FIXME

    @property
    def dummy_inputs(self) -> Dict[str, tf.Tensor]: #FIXME - change default dummy inputs
        return DUMMY_IMAGE_INPUTS

    def call(
        self,
        pixel_values=None,
        head_mask=None,
        labels=None,
        output_attentions=None,
        output_hidden_states=None,
        return_dict=None,
        training=False
    ):
        return_dict = return_dict if return_dict is not None else self.config.use_return_dict

        outputs = self.swin(
            pixel_values,
            head_mask=head_mask,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
            training=training,
        )

        pooled_output = outputs[1]

        logits = self.classifier(pooled_output)

        loss = None if labels is None else self.hf_compute_loss(labels, logits) #FIXME

        if not return_dict:
            output = (logits,) + outputs[2:]
            return ((loss,) + output) if loss is not None else output

        return TFSwinImageClassifierOutput(
            loss=loss,
            logits=logits,
            hidden_states=outputs.hidden_states,
            attentions=outputs.attentions,
            reshaped_hidden_states=outputs.reshaped_hidden_states,
        )
