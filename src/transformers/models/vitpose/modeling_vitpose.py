# coding=utf-8
# Copyright 2021 Google AI, Ross Wightman, The HuggingFace Inc. team. All rights reserved.
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
""" PyTorch ViTPose model."""


import collections.abc
import math
from typing import Dict, List, Optional, Set, Tuple, Union

import torch
import torch.utils.checkpoint
from torch import nn
from torch.nn import BCEWithLogitsLoss, CrossEntropyLoss, MSELoss

from ...activations import ACT2FN
from ...modeling_outputs import (
    BaseModelOutput,
    BaseModelOutputWithPooling,
    ImageClassifierOutput,
    MaskedImageModelingOutput,
)
from ...modeling_utils import PreTrainedModel
from ...pytorch_utils import find_pruneable_heads_and_indices, prune_linear_layer
from ...utils import (
    add_code_sample_docstrings,
    add_start_docstrings,
    add_start_docstrings_to_model_forward,
    logging,
    replace_return_docstrings,
)

from .configuration_vitpose import ViTPoseConfig


logger = logging.get_logger(__name__)

# General docstring
_CONFIG_FOR_DOC = "ViTPoseConfig"

# Base docstring ## to be changed
_CHECKPOINT_FOR_DOC = "shauray/ViTPose"
_EXPECTED_OUTPUT_SHAPE = [1, 197, 768]

# Image classification docstring
_IMAGE_CLASS_CHECKPOINT = "shauray/vitpose"
_IMAGE_CLASS_EXPECTED_OUTPUT = "Egyptian cat"


VIT_PRETRAINED_MODEL_ARCHIVE_LIST = [
    "shauray/vitpose",
    # See all ViTPose models at https://huggingface.co/models?filter=vitpose
]

## GREEN
class ViTPosePatchEmbed(nn.Module):
    """
    This class turns `pixel_values` of shape `(batch_size, num_channels, height, width)` into the initial
    `hidden_states` (patch embeddings) of shape `(batch_size, seq_length, hidden_size)` to be consumed by a
    Transformer.
    """

    def __init__(self, config: ViTPoseConfig):
        super().__init__()
        self.num_channels = 3
        self.embed_dim = config.embed_dim
        self.patch_size = config.patch_size
        self.image_size = config.img_size
       # self.image_size = self.image_size if isinstance(self.image_size, collections.abc.Iterable) else (self.image_size, self.image_size)
        self.patch_size = self.patch_size if isinstance(self.patch_size, collections.abc.Iterable) else (self.patch_size, self.patch_size)
        self.num_patches = (self.image_size[1] // self.patch_size[1]) * (self.image_size[0] // self.patch_size[0])

        self.projection = nn.Conv2d(self.num_channels, self.embed_dim, kernel_size=self.patch_size, stride=self.patch_size, padding = (2,2))

    def forward(self, pixel_values: torch.Tensor, interpolate_pos_encoding: Optional[bool]=False) -> torch.Tensor:
        batch_size, num_channels, height, width = pixel_values.shape
        if num_channels != self.num_channels:
            raise ValueError(
                "Make sure that the channel dimension of the pixel values match with the one set in the configuration."
                f" Expected {self.num_channels} but got {num_channels}."
            )
        if not interpolate_pos_encoding:
            if height != self.image_size[0] or width != self.image_size[1]:
                raise ValueError(
                    f"Input image size ({height}*{width}) doesn't match model"
                    f" ({self.image_size[0]}*{self.image_size[1]})."
                )
        embeddings = self.projection(pixel_values).flatten(2).transpose(1, 2)
        return embeddings

## GREEN
class ViTPoseAttention(nn.Module):
    def __init__(self, config: ViTPoseConfig) -> None:
        super().__init__()
        if config.embed_dim % config.num_attention_heads != 0 and not hasattr(config, "embedding_size"):
            raise ValueError(
                f"The hidden size {config.embed_dim,} is not a multiple of the number of attention "
                f"heads {config.num_attention_heads}."
            )

        self.num_attention_heads = config.num_attention_heads
        self.attention_head_size = int(config.embed_dim / config.num_attention_heads)
        self.all_head_size = self.attention_head_size * config.num_attention_heads

        #self.query = nn.Linear(config.hidden_size, self.all_head_size, bias=config.qkv_bias)
        #self.key = nn.Linear(config.hidden_size, self.all_head_size, bias=config.qkv_bias)
        #self.value = nn.Linear(config.hidden_size, self.all_head_size, bias=config.qkv_bias)

        self.qkv = nn.Linear(config.embed_dim, self.all_head_size*3, bias=config.qkv_bias)
        self.attn_drop = nn.Dropout(config.dropout_p)
        self.proj = nn.Linear(self.all_head_size, config.embed_dim, bias=config.qkv_bias)
        self.proj_drop = nn.Dropout(config.dropout_p)

    def transpose_for_scores(self, x: torch.Tensor) -> torch.Tensor:
        new_x_shape = x.size()[:-1] + (self.num_attention_heads, self.attention_head_size)
        x = x.view(*new_x_shape)
        return x.permute(0, 2, 1, 3)

    def forward(
        self, hidden_states, head_mask: Optional[torch.Tensor] = None, output_attentions: bool = False
    ) -> Union[Tuple[torch.Tensor, torch.Tensor], Tuple[torch.Tensor]]:
        qkv_layer = self.qkv(hidden_states)

        query_layer, key_layer, value_layer = torch.chunk(qkv_layer, 3, dim=-1)

        value_layer = self.transpose_for_scores(value_layer)
        key_layer = self.transpose_for_scores(key_layer)
        query_layer = self.transpose_for_scores(query_layer)


        # Take the dot product between "query" and "key" to get the raw attention scores.
        attention_scores = torch.matmul(query_layer, key_layer.transpose(-1, -2))

        attention_scores = attention_scores / math.sqrt(self.attention_head_size)

        # Normalize the attention scores to probabilities.
        attention_probs = nn.functional.softmax(attention_scores, dim=-1)

        # This is actually dropping out entire tokens to attend to, which might
        # seem a bit unusual, but is taken from the original Transformer paper.
        attention_probs = self.attn_drop(attention_probs)

        # Mask heads if we want to
        if head_mask is not None:
            attention_probs = attention_probs * head_mask

        context_layer = torch.matmul(attention_probs, value_layer)

        context_layer = context_layer.permute(0, 2, 1, 3).contiguous()
        new_context_layer_shape = context_layer.size()[:-2] + (self.all_head_size,)
        context_layer = context_layer.view(*new_context_layer_shape)

        attention_output = self.proj(context_layer)
        attention_output = self.proj_drop(attention_output)

        return attention_output

class ViTPoseMLP(nn.Module):
    def __init__(self, config: ViTPoseConfig):
        super().__init__()

        self.fc1 = nn.Linear(in_features=config.embed_dim, out_features=config.embed_dim*config.mlp_ratio,bias=True)
        self.act = nn.GELU()
        self.fc2 = nn.Linear(in_features=config.embed_dim*config.mlp_ratio, out_features=config.embed_dim)
        self.dropout = nn.Dropout(config.dropout_p, inplace=True)

    def forward(self,x):
        x = self.fc1(x)
        x = self.act(x)
        x = self.dropout(x)
        x = self.fc2(x)
        return x

    pass

class ViTPoseBlock(nn.Module):
    def __init__(self, config: ViTPoseConfig):
        super().__init__()
        self.norm1 = nn.LayerNorm(config.embed_dim, eps=1e-06, elementwise_affine=True)
        self.attn = ViTPoseAttention(config)
        self.drop_path = DropPath(p = config.drop_path_rate)
        self.norm2 = nn.LayerNorm(config.embed_dim, eps=1e-06, elementwise_affine=True)
        self.mlp = ViTPoseMLP(config)

    def forward(self, x):
        x = x + self.drop_path(self.attn(self.norm1(x)))
        x = x + self.drop_path(self.mlp(self.norm2(x)))
        return x
    pass

class DropPath(nn.Module):
    def __init__(self, p=0.0):
        super(DropPath, self).__init__()
        self.p = p

    def forward(self, x):
        if not self.training or self.p == 0.0:
            return x
        keep_prob = 1 - self.p
        shape = (x.shape[0],) + (1,) * (x.ndim - 1)
        random_tensor = keep_prob + torch.rand(shape, dtype=x.dtype, device=x.device)
        random_tensor.floor_()  # binarize
        output = x.div(keep_prob) * random_tensor
        return output

## LOOKS GREEN
class ViTPoseBackbone(nn.Module):
    """
    Construct the CLS token, position and patch embeddings. Optionally, also the mask token.
    """

    def __init__(self, config: ViTPoseConfig, use_mask_token: bool = False) -> None:
        super().__init__()

        self.cls_token = nn.Parameter(torch.randn(1, 1, config.embed_dim))
        self.mask_token = nn.Parameter(torch.zeros(1, 1, config.embed_dim)) if use_mask_token else None
        self.patch_embeddings = ViTPosePatchEmbed(config)
        num_patches = self.patch_embeddings.num_patches
        self.position_embeddings = nn.Parameter(torch.randn(1, num_patches + 1, config.embed_dim))
        self.blocks = nn.ModuleList([ViTPoseBlock(config) for i in range(config.depth)])
        self.last_norm = nn.LayerNorm(config.embed_dim, eps=1e-06, elementwise_affine=True)
        self.config = config

    def interpolate_pos_encoding(self, embeddings: torch.Tensor, height: int, width: int) -> torch.Tensor:
        """
        This method allows to interpolate the pre-trained position encodings, to be able to use the model on higher
        resolution images.

        Source:
        https://github.com/facebookresearch/dino/blob/de9ee3df6cf39fac952ab558447af1fa1365362a/vision_transformer.py#L174
        """

        num_patches = embeddings.shape[1] - 1
        num_positions = self.position_embeddings.shape[1] - 1
        if num_patches == num_positions and height == width:
            return self.position_embeddings
        class_pos_embed = self.position_embeddings[:, 0]
        patch_pos_embed = self.position_embeddings[:, 1:]
        dim = embeddings.shape[-1]
        h0 = height // self.config.patch_size
        w0 = width // self.config.patch_size
        # we add a small number to avoid floating point error in the interpolation
        # see discussion at https://github.com/facebookresearch/dino/issues/8
        h0, w0 = h0 + 0.1, w0 + 0.1
        patch_pos_embed = patch_pos_embed.reshape(1, int(math.sqrt(num_positions)), int(math.sqrt(num_positions)), dim)
        patch_pos_embed = patch_pos_embed.permute(0, 3, 1, 2)
        patch_pos_embed = nn.functional.interpolate(
            patch_pos_embed,
            scale_factor=(h0 / math.sqrt(num_positions), w0 / math.sqrt(num_positions)),
            mode="bicubic",
            align_corners=False,
        )
        assert int(h0) == patch_pos_embed.shape[-2] and int(w0) == patch_pos_embed.shape[-1]
        patch_pos_embed = patch_pos_embed.permute(0, 2, 3, 1).view(1, -1, dim)
        return torch.cat((class_pos_embed.unsqueeze(0), patch_pos_embed), dim=1)

    def forward(
        self,
        pixel_values: torch.Tensor,
        bool_masked_pos: Optional[torch.BoolTensor] = None,
        interpolate_pos_encoding: bool = False,
    ) -> torch.Tensor:
        batch_size, num_channels, height, width = pixel_values.shape
        embeddings = self.patch_embeddings(pixel_values, interpolate_pos_encoding=interpolate_pos_encoding)

        if bool_masked_pos is not None:
            seq_length = embeddings.shape[1]
            mask_tokens = self.mask_token.expand(batch_size, seq_length, -1)
            # replace the masked visual tokens by mask_tokens
            mask = bool_masked_pos.unsqueeze(-1).type_as(mask_tokens)
            embeddings = embeddings * (1.0 - mask) + mask_tokens * mask

        # add the [CLS] token to the embedded patch tokens
        cls_tokens = self.cls_token.expand(batch_size, -1, -1)
        embeddings = torch.cat((cls_tokens, embeddings), dim=1)

        # add positional encoding to each token
        if interpolate_pos_encoding:
            embeddings = embeddings + self.interpolate_pos_encoding(embeddings, height, width)
        else:
            embeddings = embeddings + self.position_embeddings

        for i,layer in enumerate(self.blocks):
            embeddings = self.blocks[i//2](embeddings) + layer(embeddings)

        return self.last_norm(embeddings)

class ViTPoseTopDownHeatMap(nn.Module):
    # keypoint head - mse loss]
    ## deconv layers and all the other remaining things with the final layer
    def __init__(self, config: ViTPoseConfig):
        super().__init__()
        self.deconv_layers = []
        for i in range(config.keypoint_num_deconv_layer):
            in_channels = config.embed_dim if i == 0 else config.keypoint_num_deconv_filters[i - 1]
            out_channels = config.keypoint_num_deconv_filters[i]
            kernel_size = config.keypoint_num_deconv_kernels[i]
            self.deconv_layers.append(nn.ConvTranspose2d(in_channels, out_channels, kernel_size, stride=2, padding=1, bias=False))
            self.deconv_layers.append(nn.BatchNorm2d(out_channels))
            self.deconv_layers.append(nn.ReLU(inplace=True))
        self.deconv_layers = nn.Sequential(*self.deconv_layers)
        self.final_layer = nn.Conv2d(config.keypoint_num_deconv_filters[-1], config.num_output_channels, kernel_size=1, stride=1)

    def forward(self, x):
        x = self.deconv_layers(x)
        keypoints = self.final_layer(x)
        return keypoints


## to be changed
class ViTPosePreTrainedModel(PreTrainedModel):
    """
    An abstract class to handle weights initialization and a simple interface for downloading and loading pretrained
    models.
    """

    config_class = ViTPoseConfig
    base_model_prefix = "vitpose"
    main_input_name = "pixel_values"
    supports_gradient_checkpointing = True
    _no_split_modules = []

    def _init_weights(self, module: Union[nn.Linear, nn.Conv2d, nn.LayerNorm]) -> None:
        """Initialize the weights"""
        if isinstance(module, (nn.Linear, nn.Conv2d)):
            # Upcast the input in `fp32` and cast it back to desired `dtype` to avoid
            # `trunc_normal_cpu` not implemented in `half` issues
            module.weight.data = nn.init.trunc_normal_(
                module.weight.data.to(torch.float32), mean=0.0, std=self.config.initializer_range
            ).to(module.weight.dtype)
            if module.bias is not None:
                module.bias.data.zero_()
        elif isinstance(module, nn.LayerNorm):
            module.bias.data.zero_()
            module.weight.data.fill_(1.0)
        elif isinstance(module, ViTPosePatchEmbed):
            pass
        #    module.position_embeddings.data = nn.init.trunc_normal_(
        #        module.position_embeddings.data.to(torch.float32),
        #        mean=0.0,
        #        std=self.config.initializer_range,
        #    ).to(module.position_embeddings.dtype)

        #    module.cls_token.data = nn.init.trunc_normal_(
        #        module.cls_token.data.to(torch.float32),
        #        mean=0.0,
        #        std=self.config.initializer_range,
        #    ).to(module.cls_token.dtype)

   # def _set_gradient_checkpointing(self, module: ViTEncoder, value: bool = False) -> None:
   #     if isinstance(module, ViTEncoder):
   #         module.gradient_checkpointing = value


VIT_START_DOCSTRING = r"""
    This model is a PyTorch [torch.nn.Module](https://pytorch.org/docs/stable/nn.html#torch.nn.Module) subclass. Use it
    as a regular PyTorch Module and refer to the PyTorch documentation for all matter related to general usage and
    behavior.

    Parameters:
        config ([`ViTConfig`]): Model configuration class with all the parameters of the model.
            Initializing with a config file does not load the weights associated with the model, only the
            configuration. Check out the [`~PreTrainedModel.from_pretrained`] method to load the model weights.
"""

VIT_INPUTS_DOCSTRING = r"""
    Args:
        pixel_values (`torch.FloatTensor` of shape `(batch_size, num_channels, height, width)`):
            Pixel values. Pixel values can be obtained using [`AutoImageProcessor`]. See [`ViTImageProcessor.__call__`]
            for details.

        head_mask (`torch.FloatTensor` of shape `(num_heads,)` or `(num_layers, num_heads)`, *optional*):
            Mask to nullify selected heads of the self-attention modules. Mask values selected in `[0, 1]`:

            - 1 indicates the head is **not masked**,
            - 0 indicates the head is **masked**.

        output_attentions (`bool`, *optional*):
            Whether or not to return the attentions tensors of all attention layers. See `attentions` under returned
            tensors for more detail.
        output_hidden_states (`bool`, *optional*):
            Whether or not to return the hidden states of all layers. See `hidden_states` under returned tensors for
            more detail.
        interpolate_pos_encoding (`bool`, *optional*):
            Whether to interpolate the pre-trained position encodings.
        return_dict (`bool`, *optional*):
            Whether or not to return a [`~utils.ModelOutput`] instead of a plain tuple.
"""


@add_start_docstrings(
    "The bare ViT Model transformer outputting raw hidden-states without any specific head on top.",
    VIT_START_DOCSTRING,
)



class ViTPoseModel(ViTPosePreTrainedModel):
    def __init__(self, config: ViTPoseConfig, add_pooling_layer: bool = True, use_mask_token: bool = False):
        super().__init__(config)
        self.config = config

        self.backbone = ViTPoseBackbone(config)
        self.keypoint_head = ViTPoseTopDownHeatMap(config)

        # Initialize weights and apply final processing
        self.post_init()

    def get_input_embeddings(self) -> ViTPosePatchEmbed:
        return self.backbone.patch_embeddings

    #def _prune_heads(self, heads_to_prune: Dict[int, List[int]]) -> None:
    #    """
    #    Prunes heads of the model. heads_to_prune: dict of {layer_num: list of heads to prune in this layer} See base
    #    class PreTrainedModel
    #    """
    #    for layer, heads in heads_to_prune.items():
    #        self.encoder.layer[layer].attention.prune_heads(heads)

    #@add_start_docstrings_to_model_forward(VIT_INPUTS_DOCSTRING)
    #@add_code_sample_docstrings(
    #    checkpoint=_CHECKPOINT_FOR_DOC,
    #    output_type=BaseModelOutputWithPooling,
    #    config_class=_CONFIG_FOR_DOC,
    #    modality="vision",
    #    expected_output=_EXPECTED_OUTPUT_SHAPE,
    #)
    def forward(
        self,
        pixel_values: Optional[torch.Tensor] = None,
        bool_masked_pos: Optional[torch.BoolTensor] = None,
        head_mask: Optional[torch.Tensor] = None,
        output_attentions: Optional[bool] = None,
        output_hidden_states: Optional[bool] = None,
        interpolate_pos_encoding: Optional[bool] = None,
        return_dict: Optional[bool] = None,
    ) -> Union[Tuple, BaseModelOutputWithPooling]:
        r"""
        bool_masked_pos (`torch.BoolTensor` of shape `(batch_size, num_patches)`, *optional*):
            Boolean masked positions. Indicates which patches are masked (1) and which aren't (0).
        """
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
        head_mask = self.get_head_mask(head_mask, self.config.depth)

        # TODO: maybe have a cleaner way to cast the input (from `ImageProcessor` side?)
        expected_dtype = self.backbone.patch_embeddings.projection.weight.dtype
        pixel_values = pixel_values.to(expected_dtype) if type(pixel_values) != expected_dtype else pixel_values

        backbone_output = self.backbone(
            pixel_values, bool_masked_pos=bool_masked_pos, interpolate_pos_encoding=interpolate_pos_encoding
        )

        keypoint_outputs = self.keypoint_head(
            backbone_output,
        )

        if not return_dict:
            head_outputs = (sequence_output, pooled_output) if pooled_output is not None else (sequence_output,)
            return head_outputs + encoder_outputs[1:]

        return keypoint_outputs

#class ViTForImageClassification(ViTPosePreTrainedModel):
#    def __init__(self, config: ViTConfig) -> None:
#        super().__init__(config)
#
#        self.num_labels = config.num_labels
#        self.vitpose = ViTPoseModel(config, add_pooling_layer=False)
#
#        # Classifier head
#        self.classifier = nn.Linear(config.hidden_size, config.num_labels) if config.num_labels > 0 else nn.Identity()
#
#        # Initialize weights and apply final processing
#        self.post_init()
#
#    @add_start_docstrings_to_model_forward(VIT_INPUTS_DOCSTRING)
#    @add_code_sample_docstrings(
#        checkpoint=_IMAGE_CLASS_CHECKPOINT,
#        output_type=ImageClassifierOutput,
#        config_class=_CONFIG_FOR_DOC,
#        expected_output=_IMAGE_CLASS_EXPECTED_OUTPUT,
#    )
#    def forward(
#        self,
#        pixel_values: Optional[torch.Tensor] = None,
#        head_mask: Optional[torch.Tensor] = None,
#        labels: Optional[torch.Tensor] = None,
#        output_attentions: Optional[bool] = None,
#        output_hidden_states: Optional[bool] = None,
#        interpolate_pos_encoding: Optional[bool] = None,
#        return_dict: Optional[bool] = None,
#    ) -> Union[tuple, ImageClassifierOutput]:
#        r"""
#        labels (`torch.LongTensor` of shape `(batch_size,)`, *optional*):
#            Labels for computing the image classification/regression loss. Indices should be in `[0, ...,
#            config.num_labels - 1]`. If `config.num_labels == 1` a regression loss is computed (Mean-Square loss), If
#            `config.num_labels > 1` a classification loss is computed (Cross-Entropy).
#        """
#        return_dict = return_dict if return_dict is not None else self.config.use_return_dict
#
#        outputs = self.vit(
#            pixel_values,
#            head_mask=head_mask,
#            output_attentions=output_attentions,
#            output_hidden_states=output_hidden_states,
#            interpolate_pos_encoding=interpolate_pos_encoding,
#            return_dict=return_dict,
#        )
#
#        sequence_output = outputs[0]
#
#        logits = self.classifier(sequence_output[:, 0, :])
#
#        loss = None
#        if labels is not None:
#            # move labels to correct device to enable model parallelism
#            labels = labels.to(logits.device)
#            if self.config.problem_type is None:
#                if self.num_labels == 1:
#                    self.config.problem_type = "regression"
#                elif self.num_labels > 1 and (labels.dtype == torch.long or labels.dtype == torch.int):
#                    self.config.problem_type = "single_label_classification"
#                else:
#                    self.config.problem_type = "multi_label_classification"
#
#            if self.config.problem_type == "regression":
#                loss_fct = MSELoss()
#                if self.num_labels == 1:
#                    loss = loss_fct(logits.squeeze(), labels.squeeze())
#                else:
#                    loss = loss_fct(logits, labels)
#            elif self.config.problem_type == "single_label_classification":
#                loss_fct = CrossEntropyLoss()
#                loss = loss_fct(logits.view(-1, self.num_labels), labels.view(-1))
#            elif self.config.problem_type == "multi_label_classification":
#                loss_fct = BCEWithLogitsLoss()
#                loss = loss_fct(logits, labels)
#
#        if not return_dict:
#            output = (logits,) + outputs[1:]
#            return ((loss,) + output) if loss is not None else output
#
#        return ImageClassifierOutput(
#            loss=loss,
#            logits=logits,
#            hidden_states=outputs.hidden_states,
#            attentions=outputs.attentions,
#        )
#]
#
#class ViTLayer(nn.Module):
#    """This corresponds to the Block class in the timm implementation."""
#
#    def __init__(self, config: ViTConfig) -> None:
#        super().__init__()
#        self.chunk_size_feed_forward = config.chunk_size_feed_forward
#        self.seq_len_dim = 1
#        self.attention = ViTAttention(config)
#        self.intermediate = ViTIntermediate(config)
#        self.output = ViTOutput(config)
#        self.layernorm_before = nn.LayerNorm(config.hidden_size, eps=config.layer_norm_eps)
#        self.layernorm_after = nn.LayerNorm(config.hidden_size, eps=config.layer_norm_eps)
#
#    def forward(
#        self,
#        hidden_states: torch.Tensor,
#        head_mask: Optional[torch.Tensor] = None,
#        output_attentions: bool = False,
#    ) -> Union[Tuple[torch.Tensor, torch.Tensor], Tuple[torch.Tensor]]:
#        self_attention_outputs = self.attention(
#            self.layernorm_before(hidden_states),  # in ViT, layernorm is applied before self-attention
#            head_mask,
#            output_attentions=output_attentions,
#        )
#        attention_output = self_attention_outputs[0]
#        outputs = self_attention_outputs[1:]  # add self attentions if we output attention weights
#
#        # first residual connection
#        hidden_states = attention_output + hidden_states
#
#        # in ViT, layernorm is also applied after self-attention
#        layer_output = self.layernorm_after(hidden_states)
#        layer_output = self.intermediate(layer_output)
#
#        # second residual connection is done here
#        layer_output = self.output(layer_output, hidden_states)
#
#        outputs = (layer_output,) + outputs
#
#        return outputs
#
#
#class ViTEncoder(nn.Module):
#    def __init__(self, config: ViTConfig) -> None:
#        super().__init__()
#        self.config = config
#        self.layer = nn.ModuleList([ViTLayer(config) for _ in range(config.num_hidden_layers)])
#        self.gradient_checkpointing = False
#
#    def forward(
#        self,
#        hidden_states: torch.Tensor,
#        head_mask: Optional[torch.Tensor] = None,
#        output_attentions: bool = False,
#        output_hidden_states: bool = False,
#        return_dict: bool = True,
#    ) -> Union[tuple, BaseModelOutput]:
#        all_hidden_states = () if output_hidden_states else None
#        all_self_attentions = () if output_attentions else None
#
#        for i, layer_module in enumerate(self.layer):
#            if output_hidden_states:
#                all_hidden_states = all_hidden_states + (hidden_states,)
#
#            layer_head_mask = head_mask[i] if head_mask is not None else None
#
#            if self.gradient_checkpointing and self.training:
#
#                def create_custom_forward(module):
#                    def custom_forward(*inputs):
#                        return module(*inputs, output_attentions)
#
#                    return custom_forward
#
#                layer_outputs = torch.utils.checkpoint.checkpoint(
#                    create_custom_forward(layer_module),
#                    hidden_states,
#                    layer_head_mask,
#                )
#            else:
#                layer_outputs = layer_module(hidden_states, layer_head_mask, output_attentions)
#
#            hidden_states = layer_outputs[0]
#
#            if output_attentions:
#                all_self_attentions = all_self_attentions + (layer_outputs[1],)
#
#        if output_hidden_states:
#            all_hidden_states = all_hidden_states + (hidden_states,)
#
#        if not return_dict:
#            return tuple(v for v in [hidden_states, all_hidden_states, all_self_attentions] if v is not None)
#        return BaseModelOutput(
#            last_hidden_state=hidden_states,
#            hidden_states=all_hidden_states,
#            attentions=all_self_attentions,
#        )
#
#
#class ViTPooler(nn.Module):
#    def __init__(self, config: ViTConfig):
#        super().__init__()
#        self.dense = nn.Linear(config.hidden_size, config.hidden_size)
#        self.activation = nn.Tanh()
#
#    def forward(self, hidden_states):
#        # We "pool" the model by simply taking the hidden state corresponding
#        # to the first token.
#        first_token_tensor = hidden_states[:, 0]
#        pooled_output = self.dense(first_token_tensor)
#        pooled_output = self.activation(pooled_output)
#        return pooled_output
#
#
#@add_start_docstrings(
#    """ViT Model with a decoder on top for masked image modeling, as proposed in [SimMIM](https://arxiv.org/abs/2111.09886).
#
#    <Tip>
#
#    Note that we provide a script to pre-train this model on custom data in our [examples
#    directory](https://github.com/huggingface/transformers/tree/main/examples/pytorch/image-pretraining).
#
#    </Tip>
#    """,
#    VIT_START_DOCSTRING,
#)

#class ViTForMaskedImageModeling(ViTPreTrainedModel):
#    def __init__(self, config: ViTConfig) -> None:
#        super().__init__(config)
#
#        self.vit = ViTModel(config, add_pooling_layer=False, use_mask_token=True)
#
#        self.decoder = nn.Sequential(
#            nn.Conv2d(
#                in_channels=config.hidden_size,
#                out_channels=config.encoder_stride**2 * config.num_channels,
#                kernel_size=1,
#            ),
#            nn.PixelShuffle(config.encoder_stride),
#        )
#
#        # Initialize weights and apply final processing
#        self.post_init()
#
#    @add_start_docstrings_to_model_forward(VIT_INPUTS_DOCSTRING)
#    @replace_return_docstrings(output_type=MaskedImageModelingOutput, config_class=_CONFIG_FOR_DOC)
#    def forward(
#        self,
#        pixel_values: Optional[torch.Tensor] = None,
#        bool_masked_pos: Optional[torch.BoolTensor] = None,
#        head_mask: Optional[torch.Tensor] = None,
#        output_attentions: Optional[bool] = None,
#        output_hidden_states: Optional[bool] = None,
#        interpolate_pos_encoding: Optional[bool] = None,
#        return_dict: Optional[bool] = None,
#    ) -> Union[tuple, MaskedImageModelingOutput]:
#        r"""
#        bool_masked_pos (`torch.BoolTensor` of shape `(batch_size, num_patches)`):
#            Boolean masked positions. Indicates which patches are masked (1) and which aren't (0).
#
#        Returns:
#
#        Examples:
#        ```python
#        >>> from transformers import AutoImageProcessor, ViTForMaskedImageModeling
#        >>> import torch
#        >>> from PIL import Image
#        >>> import requests
#
#        >>> url = "http://images.cocodataset.org/val2017/000000039769.jpg"
#        >>> image = Image.open(requests.get(url, stream=True).raw)
#
#        >>> image_processor = AutoImageProcessor.from_pretrained("google/vit-base-patch16-224-in21k")
#        >>> model = ViTForMaskedImageModeling.from_pretrained("google/vit-base-patch16-224-in21k")
#
#        >>> num_patches = (model.config.image_size // model.config.patch_size) ** 2
#        >>> pixel_values = image_processor(images=image, return_tensors="pt").pixel_values
#        >>> # create random boolean mask of shape (batch_size, num_patches)
#        >>> bool_masked_pos = torch.randint(low=0, high=2, size=(1, num_patches)).bool()
#
#        >>> outputs = model(pixel_values, bool_masked_pos=bool_masked_pos)
#        >>> loss, reconstructed_pixel_values = outputs.loss, outputs.reconstruction
#        >>> list(reconstructed_pixel_values.shape)
#        [1, 3, 224, 224]
#        ```"""
#        return_dict = return_dict if return_dict is not None else self.config.use_return_dict
#
#        if bool_masked_pos is not None and (self.config.patch_size != self.config.encoder_stride):
#            raise ValueError(
#                "When `bool_masked_pos` is provided, `patch_size` must be equal to `encoder_stride` to ensure that "
#                "the reconstructed image has the same dimensions as the input."
#                f"Got `patch_size` = {self.config.patch_size} and `encoder_stride` = {self.config.encoder_stride}."
#            )
#
#        outputs = self.vit(
#            pixel_values,
#            bool_masked_pos=bool_masked_pos,
#            head_mask=head_mask,
#            output_attentions=output_attentions,
#            output_hidden_states=output_hidden_states,
#            interpolate_pos_encoding=interpolate_pos_encoding,
#            return_dict=return_dict,
#        )
#
#        sequence_output = outputs[0]
#
#        # Reshape to (batch_size, num_channels, height, width)
#        sequence_output = sequence_output[:, 1:]
#        batch_size, sequence_length, num_channels = sequence_output.shape
#        height = width = math.floor(sequence_length**0.5)
#        sequence_output = sequence_output.permute(0, 2, 1).reshape(batch_size, num_channels, height, width)
#
#        # Reconstruct pixel values
#        reconstructed_pixel_values = self.decoder(sequence_output)
#
#        masked_im_loss = None
#        if bool_masked_pos is not None:
#            size = self.config.image_size // self.config.patch_size
#            bool_masked_pos = bool_masked_pos.reshape(-1, size, size)
#            mask = (
#                bool_masked_pos.repeat_interleave(self.config.patch_size, 1)
#                .repeat_interleave(self.config.patch_size, 2)
#                .unsqueeze(1)
#                .contiguous()
#            )
#            reconstruction_loss = nn.functional.l1_loss(pixel_values, reconstructed_pixel_values, reduction="none")
#            masked_im_loss = (reconstruction_loss * mask).sum() / (mask.sum() + 1e-5) / self.config.num_channels
#
#        if not return_dict:
#            output = (reconstructed_pixel_values,) + outputs[1:]
#            return ((masked_im_loss,) + output) if masked_im_loss is not None else output
#
#        return MaskedImageModelingOutput(
#            loss=masked_im_loss,
#            reconstruction=reconstructed_pixel_values,
#            hidden_states=outputs.hidden_states,
#            attentions=outputs.attentions,
#        )
#
#
#@add_start_docstrings(
#    """
#    ViT Model transformer with an image classification head on top (a linear layer on top of the final hidden state of
#    the [CLS] token) e.g. for ImageNet.
#
#    <Tip>
#
#        Note that it's possible to fine-tune ViT on higher resolution images than the ones it has been trained on, by
#        setting `interpolate_pos_encoding` to `True` in the forward of the model. This will interpolate the pre-trained
#        position embeddings to the higher resolution.
#
#    </Tip>
#    """,
#    VIT_START_DOCSTRING,
#)

import numpy
model = ViTPoseBackbone(ViTPoseConfig())
test = torch.Tensor(numpy.zeros([1,3,256,192]))
print(model(test))


