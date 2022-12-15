# coding=utf-8
# Copyright 2022 Meta Platforms, Inc.s and The HuggingFace Inc. team. All rights reserved.
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
""" PyTorch Mask2Former model."""

import math
import warnings
from dataclasses import dataclass
from numbers import Number
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn.functional as F
from torch import Tensor, nn

from transformers import AutoBackbone, MaskFormerSwinConfig
from transformers.utils import logging

from ...activations import ACT2FN
from ...file_utils import (
    ModelOutput,
    add_start_docstrings,
    add_start_docstrings_to_model_forward,
    is_scipy_available,
    replace_return_docstrings,
    requires_backends,
)
from ...modeling_outputs import BaseModelOutput
from ...modeling_utils import PreTrainedModel
from .configuration_mask2former import Mask2FormerConfig


if is_scipy_available():
    from scipy.optimize import linear_sum_assignment

logger = logging.get_logger(__name__)


_CONFIG_FOR_DOC = "Mask2FormerConfig"
_CHECKPOINT_FOR_DOC = "shivi/mask2former-instance-swin-small-coco"
_FEAT_EXTRACTOR_FOR_DOC = "Mask2FormerFeatureExtractor"

MASK2FORMER_PRETRAINED_MODEL_ARCHIVE_LIST = [
    "shivi/mask2former-instance-swin-small-coco",
    # See all mask2former models at https://huggingface.co/models?filter=mask2former
]


@dataclass
class Mask2FormerPixelDecoderOutput(ModelOutput):
    """
    Mask2Former's pixel decoder module output, practically a Multi-Scale Deformable Attention based decoder. It returns
    the mask features and the multiscale features.

    Args:
        multi_scale_features (`tuple(torch.FloatTensor)`):
            Tuple of multi-scale features of scales [1/8, 1/16, 1/32] and shape `(batch_size, num_channels, height,
            width)`from the Multi-Scale Deformable Attenntion based Pixel Decoder.
        mask_features (`torch.FloatTensor`):
            Tensor of shape `(batch_size, num_channels, height, width)`, 1/4 scale features from the last Pixel Decoder
            Layer.
        attentions (`tuple(torch.FloatTensor)`, *optional*):
            Tuple of `torch.FloatTensor` (one for each layer) of shape `(batch_size, num_heads, sequence_length,
            sequence_length)`. Attentions weights from pixel decoder. Returned when `output_attentions=True` is passed
            or when `config.output_attentions=True`
    """

    multi_scale_features: Tuple[torch.FloatTensor] = None
    mask_features: torch.FloatTensor = None
    attentions: Optional[Tuple[torch.FloatTensor]] = None


@dataclass
class Mask2FormerTransformerDecoderOutput(BaseModelOutput):
    """
    Base class for outputs of the Transformer decoder. This class adds attributes for class predictions and mask
    predictions logits to BaseModelOutputWithCrossAttentions.

    Args:
        object_logits (`torch.FloatTensor` of shape `(batch_size, num_queries, hidden_dim)`):
            Queries representation for the region proposals.
        prediction_masks (`torch.FloatTensor` of shape `(batch_size, num_queries, height, width)`):
            Mask predictions from last layer of the transformer decoder.
        prediction_class (`torch.FloatTensor` of shape `(batch_size, num_queries, num_classes+1)`):
            Class predictions from last layer of the transformer decoder.
        auxiliary_predictions (Tuple of Dict of `str, torch.FloatTensor`, *optional*):
            Tuple of class and mask predictions from each layer of the transformer decoder.
    """

    object_queries: torch.FloatTensor = None
    prediction_masks: torch.FloatTensor = None
    prediction_class: torch.FloatTensor = None
    auxiliary_predictions: Optional[Tuple[Dict[str, torch.FloatTensor]]] = None


@dataclass
class Mask2FormerPixelLevelModuleOutput(ModelOutput):
    """
    Mask2Former's pixel level module output. It returns the output of the encoder (optional) and all hidden states
    (multi-scale features) from the `decoder`. By default, the `encoder` is a Swin Backbone and the `decoder` is a
    Multi-Scale Deformable Attention based decoder.

    The `decoder_last_hidden_state` are the **per-pixel embeddings** while `decoder_hidden_states` refer to multi-scale
    feature maps produced using **multi-scaling strategy** defined in the paper.

    Args:
        encoder_hidden_states (`tuple(torch.FloatTensor)`):
            Tuple of `torch.FloatTensor` of shape `(batch_size, num_channels, height, width)`. Hidden states (also
            called feature maps) of the model at the output of each stage.
        decoder_hidden_states (`tuple(torch.FloatTensor)`):
            Tuple of `torch.FloatTensor` of shape `(batch_size, num_channels, height, width)`. Hidden states (also
            called feature maps) of the model at the output of each stage.
        decoder_last_hidden_state (`torch.FloatTensor` of shape `(batch_size, num_channels, height, width)):
            1/4 scale features from the last Pixel Decoder Layer.
    """

    encoder_hidden_states: Tuple[torch.FloatTensor] = None
    decoder_last_hidden_state: torch.FloatTensor = None
    decoder_hidden_states: Tuple[torch.FloatTensor] = None


@dataclass
class Mask2FormerModelOutput(ModelOutput):
    """
    Class for outputs of [`Mask2FormerModel`]. This class returns all the needed hidden states to compute the logits.

    Args:
        encoder_hidden_states (`tuple(torch.FloatTensor)`, *optional*, returned when `output_hidden_states=True` is passed or when `config.output_hidden_states=True`):
            Tuple of `torch.FloatTensor` (one for the output of the embeddings + one for the output of each stage) of
            shape `(batch_size, num_channels, height, width)`. Hidden-states (also called feature maps) of the encoder
            model at the output of each stage.
        pixel_decoder_hidden_states (`tuple(torch.FloatTensor)`, *optional*, returned when `output_hidden_states=True` is passed or when `config.output_hidden_states=True`):
            Tuple of `torch.FloatTensor` (one for the output of the embeddings + one for the output of each stage) of
            shape `(batch_size, num_channels, height, width)`. Hidden-states (also called feature maps) of the pixel
            decoder model at the output of each stage.
        transformer_decoder_hidden_states (`tuple(torch.FloatTensor)`, *optional*, returned when `output_hidden_states=True` is passed or when `config.output_hidden_states=True`):
            Tuple of `torch.FloatTensor` (one for the output of the embeddings + one for the output of each stage) of
            shape `(batch_size, sequence_length, hidden_size)`. Hidden-states (also called feature maps) of the
            transformer decoder at the output of each stage.
        transformer_decoder_object_queries (`torch.FloatTensor` of shape `(batch_size, num_queries, hidden_dim)`)
            Output object queries from the last layer in the transformer decoder.
        transformer_decoder_mask_predictions (`torch.FloatTensor` of shape `(batch_size, num_queries, height, width)`)
            Mask Predictions from the last layer in the transformer decoder.
        transformer_decoder_class_predictions (`torch.FloatTensor` of shape `(batch_size, num_queries, num_classes+1)`):
            Class Predictions from the last layer in the transformer decoder.
        transformer_decoder_auxiliary_predictions (Tuple of Dict of `str, torch.FloatTensor`, *optional*):
            Tuple of class and mask predictions from each layer of the transformer decoder.
        attentions (`tuple(tuple(torch.FloatTensor))`, *optional*, returned when `output_attentions=True` is passed or when `config.output_attentions=True`):
            Tuple of `tuple(torch.FloatTensor)` (one for each layer) of shape `(batch_size, num_heads, sequence_length,
            sequence_length)`. Self and Cross Attentions weights from transformer decoder.
    """

    encoder_hidden_states: Optional[Tuple[torch.FloatTensor]] = None
    pixel_decoder_hidden_states: Optional[Tuple[torch.FloatTensor]] = None
    transformer_decoder_hidden_states: Optional[torch.FloatTensor] = None
    transformer_decoder_object_queries: torch.FloatTensor = None
    transformer_decoder_mask_predictions: torch.FloatTensor = None
    transformer_decoder_class_predictions: torch.FloatTensor = None
    transformer_decoder_auxiliary_predictions: Optional[Tuple[Dict[str, torch.FloatTensor]]] = None
    attentions: Optional[Tuple[torch.FloatTensor]] = None


@dataclass
class Mask2FormerForInstanceSegmentationOutput(ModelOutput):
    """
    Class for outputs of [`Mask2FormerForInstanceSegmentationOutput`].

    This output can be directly passed to [`~Mask2FormerImageProcessor.post_process_semantic_segmentation`] or
    [`~Mask2FormerImageProcessor.post_process_instance_segmentation`] or
    [`~Mask2FormerImageProcessor.post_process_panoptic_segmentation`] to compute final segmentation maps. Please, see
    [`~Mask2FormerImageProcessor] for details regarding usage.

    Args:
        loss (`torch.Tensor`, *optional*):
            The computed loss, returned when labels are present.
        class_queries_logits (`torch.FloatTensor`):
            A tensor of shape `(batch_size, num_queries, num_labels + 1)` representing the proposed classes for each
            query. Note the `+ 1` is needed because we incorporate the null class.
        masks_queries_logits (`torch.FloatTensor`):
            A tensor of shape `(batch_size, num_queries, height, width)` representing the proposed masks for each
            query.
        auxiliary_predictions (List of Dict of `str, torch.FloatTensor`, *optional*):
            List of class and mask predictions from each layer of the transformer decoder.
        encoder_hidden_states (`tuple(torch.FloatTensor)`, *optional*, returned when `output_hidden_states=True` is passed or when `config.output_hidden_states=True`):
            Tuple of `torch.FloatTensor` (one for the output of the embeddings + one for the output of each stage) of
            shape `(batch_size, num_channels, height, width)`. Hidden-states (also called feature maps) of the encoder
            model at the output of each stage.
        pixel_decoder_hidden_states (`tuple(torch.FloatTensor)`, *optional*, returned when `output_hidden_states=True` is passed or when `config.output_hidden_states=True`):
            Tuple of `torch.FloatTensor` (one for the output of the embeddings + one for the output of each stage) of
            shape `(batch_size, num_channels, height, width)`. Hidden-states (also called feature maps) of the pixel
            decoder model at the output of each stage.
        transformer_decoder_hidden_states (`tuple(torch.FloatTensor)`, *optional*, returned when `output_hidden_states=True` is passed or when `config.output_hidden_states=True`):
            Tuple of `torch.FloatTensor` (one for the output of the embeddings + one for the output of each stage) of
            shape `(batch_size, sequence_length, hidden_size)`. Hidden-states (also called feature maps) of the
            transformer decoder at the output of each stage.
        transformer_decoder_object_queries (`torch.FloatTensor` of shape `(batch_size, num_queries, hidden_dim)`)
            Output object queries from the last layer in the transformer decoder.
        transformer_decoder_mask_predictions (`torch.FloatTensor` of shape `(batch_size, num_queries, height, width)`)
            Mask Predictions from the last layer in the transformer decoder.
        transformer_decoder_class_predictions (`torch.FloatTensor` of shape `(batch_size, num_queries, num_classes+1)`):
            Class Predictions from the last layer in the transformer decoder.
        transformer_decoder_auxiliary_predictions (List of Dict of `str, torch.FloatTensor`, *optional*):
            List of class and mask predictions from each layer of the transformer decoder.
        attentions (`tuple(tuple(torch.FloatTensor))`, *optional*, returned when `output_attentions=True` is passed or when `config.output_attentions=True`):
            Tuple of `tuple(torch.FloatTensor)` (one for each layer) of shape `(batch_size, num_heads, sequence_length,
            sequence_length)`. Self and Cross Attentions weights from transformer decoder.
    """

    loss: Optional[torch.FloatTensor] = None
    class_queries_logits: torch.FloatTensor = None
    masks_queries_logits: torch.FloatTensor = None
    auxiliary_predictions: List[Dict[str, torch.FloatTensor]] = None
    encoder_hidden_states: Optional[Tuple[torch.FloatTensor]] = None
    pixel_decoder_hidden_states: Optional[List[torch.FloatTensor]] = None
    transformer_decoder_hidden_states: Optional[torch.FloatTensor] = None
    transformer_decoder_object_queries: torch.FloatTensor = None
    transformer_decoder_mask_predictions: torch.FloatTensor = None
    transformer_decoder_class_predictions: torch.FloatTensor = None
    transformer_decoder_auxiliary_predictions: Optional[List[Dict[str, torch.FloatTensor]]] = None
    attentions: Optional[Tuple[Tuple[torch.FloatTensor]]] = None


# Copied from transformers.models.detr.modeling_detr._expand_mask
def _expand_mask(mask: torch.Tensor, dtype: torch.dtype, target_len: Optional[int] = None):
    """
    Expands attention_mask from `[batch_size, seq_len]` to `[batch_size, 1, target_seq_len, source_seq_len]`.
    """
    batch_size, source_len = mask.size()
    target_len = target_len if target_len is not None else source_len

    expanded_mask = mask[:, None, None, :].expand(batch_size, 1, target_len, source_len).to(dtype)

    inverted_mask = 1.0 - expanded_mask

    return inverted_mask.masked_fill(inverted_mask.bool(), torch.finfo(dtype).min)


# Adapted from https://github.com/facebookresearch/detectron2/blob/main/projects/PointRend/point_rend/point_features.py
def sample_point(input_features: torch.Tensor, point_coordinates: torch.Tensor, add_dim=False) -> torch.Tensor:
    """
    A wrapper around `torch.nn.functional.grid_sample` to support 3D point_coordinates tensors.

    Args:
        input_features (`torch.Tensor` of shape (batch_size, channels, height, width)):
            A tensor that contains features map on a height * width grid
        point_coordinates (`torch.Tensor` of shape (batch_size, num_points, 2) or (batch_size, grid_height, grid_width,:
        2)):
            A tensor that contains [0, 1] * [0, 1] normalized point coordinates
        add_dim (`bool`):
            boolean value to keep track of added dimension

    Returns:
        point_features (`torch.Tensor` of shape (batch_size, channels, num_points) or (batch_size, channels,
        height_grid, width_grid):
            A tensor that contains features for points in `point_coordinates`.
    """
    if point_coordinates.dim() == 3:
        add_dim = True
        point_coordinates = point_coordinates.unsqueeze(2)

    # use nn.function.grid_sample to get features for points in `point_coordinates` via bilinear interpolation
    point_features = F.grid_sample(input_features, 2.0 * point_coordinates - 1.0)
    if add_dim:
        point_features = point_features.squeeze(3)

    return point_features


# Copied from transformers.models.maskformer.modeling_maskformer.dice_loss
def dice_loss(inputs: Tensor, labels: Tensor, num_masks: int) -> Tensor:
    r"""
    Compute the DICE loss, similar to generalized IOU for masks as follows:

    $$ \mathcal{L}_{\text{dice}(x, y) = 1 - \frac{2 * x \cap y }{x \cup y + 1}} $$

    In practice, since `labels` is a binary mask, (only 0s and 1s), dice can be computed as follow

    $$ \mathcal{L}_{\text{dice}(x, y) = 1 - \frac{2 * x * y }{x + y + 1}} $$

    Args:
        inputs (`torch.Tensor`):
            A tensor representing a mask.
        labels (`torch.Tensor`):
            A tensor with the same shape as inputs. Stores the binary classification labels for each element in inputs
            (0 for the negative class and 1 for the positive class).
        num_masks (`int`):
            The number of masks present in the current batch, used for normalization.

    Returns:
        `torch.Tensor`: The computed loss.
    """
    probs = inputs.sigmoid().flatten(1)
    numerator = 2 * (probs * labels).sum(-1)
    denominator = probs.sum(-1) + labels.sum(-1)
    loss = 1 - (numerator + 1) / (denominator + 1)
    loss = loss.sum() / num_masks
    return loss


def sigmoid_cross_entropy_loss(inputs: torch.Tensor, labels: torch.Tensor, num_masks: int) -> torch.Tensor:
    r"""
    Args:
        inputs (`torch.Tensor`):
            A float tensor of arbitrary shape.
        labels (`torch.Tensor`):
            A tensor with the same shape as inputs. Stores the binary classification labels for each element in inputs
            (0 for the negative class and 1 for the positive class).

    Returns:
        `torch.Tensor`: The computed loss.
    """
    criterion = nn.BCEWithLogitsLoss(reduction="none")
    cross_entropy_loss = criterion(inputs, labels)

    loss = cross_entropy_loss.mean(1).sum() / num_masks
    return loss


# Copied from transformers.models.maskformer.modeling_maskformer.pair_wise_dice_loss
def pair_wise_dice_loss(inputs: Tensor, labels: Tensor) -> Tensor:
    """
    A pair wise version of the dice loss, see `dice_loss` for usage.

    Args:
        inputs (`torch.Tensor`):
            A tensor representing a mask
        labels (`torch.Tensor`):
            A tensor with the same shape as inputs. Stores the binary classification labels for each element in inputs
            (0 for the negative class and 1 for the positive class).

    Returns:
        `torch.Tensor`: The computed loss between each pairs.
    """
    inputs = inputs.sigmoid().flatten(1)
    numerator = 2 * torch.einsum("nc,mc->nm", inputs, labels)
    # using broadcasting to get a [num_queries, NUM_CLASSES] matrix
    denominator = inputs.sum(-1)[:, None] + labels.sum(-1)[None, :]
    loss = 1 - (numerator + 1) / (denominator + 1)
    return loss


def pair_wise_sigmoid_cross_entropy_loss(inputs: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
    r"""
    A pair wise version of the cross entropy loss, see `sigmoid_cross_entropy_loss` for usage.

    Args:
        inputs (`torch.Tensor`):
            A tensor representing a mask.
        labels (`torch.Tensor`):
            A tensor with the same shape as inputs. Stores the binary classification labels for each element in inputs
            (0 for the negative class and 1 for the positive class).

    Returns:
        `torch.Tensor`: The computed loss between each pairs.
    """

    height_and_width = inputs.shape[1]

    criterion = nn.BCEWithLogitsLoss(reduction="none")
    cross_entropy_loss_pos = criterion(inputs, torch.ones_like(inputs))
    cross_entropy_loss_neg = criterion(inputs, torch.zeros_like(inputs))

    loss = torch.einsum("nc,mc->nm", cross_entropy_loss_pos, labels) + torch.einsum(
        "nc,mc->nm", cross_entropy_loss_neg, (1 - labels)
    )

    return loss / height_and_width


# Adapted from https://github.com/facebookresearch/Mask2Former/blob/main/mask2former/modeling/matcher.py
class Mask2FormerHungarianMatcher(nn.Module):
    """This class computes an assignment between the labels and the predictions of the network.

    For efficiency reasons, the labels don't include the no_object. Because of this, in general, there are more
    predictions than labels. In this case, we do a 1-to-1 matching of the best predictions, while the others are
    un-matched (and thus treated as non-objects).
    """

    def __init__(
        self, cost_class: float = 1.0, cost_mask: float = 1.0, cost_dice: float = 1.0, num_points: int = 12544
    ):
        """Creates the matcher

        Params:
            cost_class (float, *optional*, defaults to 1.0):
                Relative weight of the classification error in the matching cost.
            cost_mask (float, *optional*,  defaults to 1.0):
                This is the relative weight of the focal loss of the binary mask in the matching cost.
            cost_dice (float, *optional*, defaults to 1.0):
                This is the relative weight of the dice loss of the binary mask in the matching cost.
            num_points (int, *optional*, defaults to 12544):
                No. of points to sample on which the mask loss will be calculated. The same set of K points are
                uniformly sampled for all prediction and ground truth masks to construct the cost matrix for bipartite
                matching.
        """
        super().__init__()
        if cost_class == 0 and cost_mask == 0 and cost_dice == 0:
            raise ValueError("All costs cant be 0")

        self.num_points = num_points
        self.cost_class = cost_class
        self.cost_mask = cost_mask
        self.cost_dice = cost_dice

    @torch.no_grad()
    def forward(
        self,
        masks_queries_logits: torch.Tensor,
        class_queries_logits: torch.Tensor,
        mask_labels: torch.Tensor,
        class_labels: torch.Tensor,
    ) -> List[Tuple[Tensor]]:
        """
        Params:
            masks_queries_logits (`torch.Tensor`):
                A tensor` of dim `batch_size, num_queries, num_labels` with the
                  classification logits.
            class_queries_logits (`torch.Tensor`):
                A tensor` of dim `batch_size, num_queries, height, width` with the
                  predicted masks.
            class_labels (`torch.Tensor`):
                A tensor` of dim `num_target_boxes` (where num_target_boxes is the number
                  of ground-truth objects in the target) containing the class labels.
            mask_labels (`torch.Tensor`):
                A tensor` of dim `num_target_boxes, height, width` containing the target
                  masks.

        Returns:
            `List[Tuple[Tensor]]`: A list of size batch_size, containing tuples of (index_i, index_j) where:
                - index_i is the indices of the selected predictions (in order)
                - index_j is the indices of the corresponding selected labels (in order)
            For each batch element, it holds:
                len(index_i) = len(index_j) = min(num_queries, num_target_boxes).
        """
        indices: List[Tuple[np.array]] = []

        # iterate through batch size
        batch_size = masks_queries_logits.shape[0]
        for i in range(batch_size):
            pred_probs = class_queries_logits[i].softmax(-1)
            pred_mask = masks_queries_logits[i]

            # Compute the classification cost. Contrary to the loss, we don't use the NLL, but approximate it in 1 - proba[target class]. The 1 is a constant that doesn't change the matching, it can be ommitted.
            cost_class = -pred_probs[:, class_labels[i]]
            target_mask = mask_labels[i].to(pred_mask)
            target_mask = target_mask[:, None]
            pred_mask = pred_mask[:, None]

            # Sample ground truth and predicted masks
            point_coordinates = torch.rand(1, self.num_points, 2, device=pred_mask.device)

            target_coordinates = point_coordinates.repeat(target_mask.shape[0], 1, 1)
            target_mask = sample_point(target_mask, target_coordinates, align_corners=False).squeeze(1)

            pred_coordinates = point_coordinates.repeat(pred_mask.shape[0], 1, 1)
            pred_mask = sample_point(pred_mask, pred_coordinates, align_corners=False).squeeze(1)

            # compute the cross entropy loss between each mask pairs -> shape (num_queries, num_labels)
            cost_mask = pair_wise_sigmoid_cross_entropy_loss(pred_mask, target_mask)
            # Compute the dice loss betwen each mask pairs -> shape (num_queries, num_labels)
            cost_dice = pair_wise_dice_loss(pred_mask, target_mask)
            # final cost matrix
            cost_matrix = self.cost_mask * cost_mask + self.cost_class * cost_class + self.cost_dice * cost_dice
            # do the assigmented using the hungarian algorithm in scipy
            assigned_indices: Tuple[np.array] = linear_sum_assignment(cost_matrix.cpu())
            indices.append(assigned_indices)

        # It could be stacked in one tensor
        matched_indices = [
            (torch.as_tensor(i, dtype=torch.int64), torch.as_tensor(j, dtype=torch.int64)) for i, j in indices
        ]
        return matched_indices


# Adapted from https://github.com/facebookresearch/Mask2Former/blob/main/mask2former/modeling/criterion.py
class Mask2FormerLoss(nn.Module):
    def __init__(self, config: Mask2FormerConfig, weight_dict: Dict[str, float]):
        """
        The Mask2Former Loss. The loss is computed very similar to DETR. The process happens in two steps: 1) we
        compute hungarian assignment between ground truth masks and the outputs of the model 2) we supervise each pair
        of matched ground-truth / prediction (supervise class and mask)

        Args:
            config (`Mask2FormerConfig`):
                The configuration for Mask2Former model also containing loss calculation specific parameters
            weight_dict (`Dict[str, float]`):
                A dictionary of weights to be applied to the different losses.
        """

        super().__init__()
        requires_backends(self, ["scipy"])
        self.num_labels = config.num_labels
        self.weight_dict = weight_dict

        # Weight to apply to the null class
        general_config = config.general_config
        self.eos_coef = general_config.no_object_weight
        empty_weight = torch.ones(self.num_labels + 1)
        empty_weight[-1] = self.eos_coef
        self.register_buffer("empty_weight", empty_weight)

        # pointwise mask loss parameters
        self.num_points = general_config.train_num_points
        self.oversample_ratio = general_config.oversample_ratio
        self.importance_sample_ratio = general_config.importance_sample_ratio

        self.matcher = Mask2FormerHungarianMatcher(
            cost_class=1.0,
            cost_dice=general_config.dice_weight,
            cost_mask=general_config.mask_weight,
            num_points=self.num_points,
        )

    def _max_by_axis(self, sizes: List[List[int]]) -> List[int]:
        maxes = sizes[0]
        for sublist in sizes[1:]:
            for index, item in enumerate(sublist):
                maxes[index] = max(maxes[index], item)
        return maxes

    # Adapted from nested_tensor_from_tensor_list() in original implementation
    def _pad_images_to_max_in_batch(self, tensors: List[Tensor]) -> Tuple[Tensor, Tensor]:
        # get the maximum size in the batch
        max_size = self._max_by_axis([list(tensor.shape) for tensor in tensors])
        batch_size = len(tensors)
        # compute finel size
        batch_shape = [batch_size] + max_size
        b, _, h, w = batch_shape
        dtype = tensors[0].dtype
        device = tensors[0].device
        padded_tensors = torch.zeros(batch_shape, dtype=dtype, device=device)
        padding_masks = torch.ones((b, h, w), dtype=torch.bool, device=device)
        # pad the tensors to the size of the biggest one
        for tensor, padded_tensor, padding_mask in zip(tensors, padded_tensors, padding_masks):
            padded_tensor[: tensor.shape[0], : tensor.shape[1], : tensor.shape[2]].copy_(tensor)
            padding_mask[: tensor.shape[1], : tensor.shape[2]] = False

        return padded_tensors, padding_masks

    def loss_labels(
        self, class_queries_logits: Tensor, class_labels: List[Tensor], indices: Tuple[np.array]
    ) -> Dict[str, Tensor]:
        """Compute the losses related to the labels using cross entropy.

        Args:
            class_queries_logits (`torch.Tensor`):
                A tensor of shape `batch_size, num_queries, num_labels`
            class_labels (`List[torch.Tensor]`):
                List of class labels of shape `(labels)`.
            indices (`Tuple[np.array])`:
                The indices computed by the Hungarian matcher.

        Returns:
            `Dict[str, Tensor]`: A dict of `torch.Tensor` containing the following key:
            - **loss_cross_entropy** -- The loss computed using cross entropy on the predicted and ground truth labels.
        """
        pred_logits = class_queries_logits
        batch_size, num_queries, _ = pred_logits.shape
        criterion = nn.CrossEntropyLoss(weight=self.empty_weight)
        idx = self._get_predictions_permutation_indices(indices)  # shape of (batch_size, num_queries)
        target_classes_o = torch.cat(
            [target[j] for target, (_, j) in zip(class_labels, indices)]
        )  # shape of (batch_size, num_queries)
        target_classes = torch.full(
            (batch_size, num_queries), fill_value=self.num_labels, dtype=torch.int64, device=pred_logits.device
        )
        target_classes[idx] = target_classes_o
        # Permute target_classes (batch_size, num_queries, num_labels) -> (batch_size, num_labels, num_queries)
        pred_logits_transposed = pred_logits.transpose(1, 2)
        loss_ce = criterion(pred_logits_transposed, target_classes)
        losses = {"loss_cross_entropy": loss_ce}
        return losses

    def loss_masks(
        self,
        masks_queries_logits: torch.Tensor,
        mask_labels: List[torch.Tensor],
        indices: Tuple[np.array],
        num_masks: int,
    ) -> Dict[str, torch.Tensor]:
        """Compute the losses related to the masks using sigmoid_cross_entropy_loss and dice loss.

        Args:
            masks_queries_logits (`torch.Tensor`):
                A tensor of shape `batch_size, num_queries, height, width`
            mask_labels (`torch.Tensor`):
                List of mask labels of shape `(labels, height, width)`.
            indices (`Tuple[np.array])`:
                The indices computed by the Hungarian matcher.
            num_masks (`int)`:
                The number of masks, used for normalization.

        Returns:
            `Dict[str, Tensor]`: A dict of `torch.Tensor` containing two keys:
            - **loss_mask** -- The loss computed using sigmoid cross entropy loss on the predicted and ground truth
              masks.
            - **loss_dice** -- The loss computed using dice loss on the predicted on the predicted and ground truth
              masks.
        """
        src_idx = self._get_predictions_permutation_indices(indices)
        tgt_idx = self._get_targets_permutation_indices(indices)
        # shape (batch_size * num_queries, height, width)
        pred_masks = masks_queries_logits[src_idx]
        # shape (batch_size, num_queries, height, width)
        # pad all and stack the targets to the num_labels dimension
        target_masks, _ = self._pad_images_to_max_in_batch(mask_labels)
        target_masks = target_masks[tgt_idx]

        # No need to upsample predictions as we are using normalized coordinates
        pred_masks = pred_masks[:, None]
        target_masks = target_masks[:, None]

        # Sample point coordinates
        with torch.no_grad():
            point_coordinates = self.sample_points_using_uncertainty(
                pred_masks,
                lambda logits: self.calculate_uncertainty(logits),
                self.num_points,
                self.oversample_ratio,
                self.importance_sample_ratio,
            )

            point_labels = sample_point(target_masks, point_coordinates, align_corners=False).squeeze(1)

        point_logits = sample_point(pred_masks, point_coordinates, align_corners=False).squeeze(1)

        losses = {
            "loss_mask": sigmoid_cross_entropy_loss(point_logits, point_labels, num_masks),
            "loss_dice": dice_loss(point_logits, point_labels, num_masks),
        }

        del pred_masks
        del target_masks
        return losses

    def _get_predictions_permutation_indices(self, indices):
        # Permute predictions following indices
        batch_indices = torch.cat([torch.full_like(src, i) for i, (src, _) in enumerate(indices)])
        predictions_indices = torch.cat([src for (src, _) in indices])
        return batch_indices, predictions_indices

    def _get_targets_permutation_indices(self, indices):
        # Permute labels following indices
        batch_indices = torch.cat([torch.full_like(tgt, i) for i, (_, tgt) in enumerate(indices)])
        target_indices = torch.cat([tgt for (_, tgt) in indices])
        return batch_indices, target_indices

    def calculate_uncertainty(self, logits: torch.Tensor) -> torch.Tensor:
        """
        In Mask2Former paper, uncertainty is estimated as L1 distance between 0.0 and the logit prediction in 'logits'
        for the foreground class in `classes`.

        Args:
            logits (Tensor):
            A tensor of shape (R, 1, ...) for class-specific or class-agnostic, where R is the total number of predicted masks in all images and C is:
            the number of foreground classes. The values are logits.

        Returns:
            scores (Tensor): A tensor of shape (R, 1, ...) that contains uncertainty scores with the most uncertain
            locations having the highest uncertainty score.
        """
        uncertainty_scores = -(torch.abs(logits))
        return uncertainty_scores

    def sample_points_using_uncertainty(
        self,
        logits: torch.Tensor,
        uncertainty_function,
        num_points: int,
        oversample_ratio: int,
        importance_sample_ratio: float,
    ) -> torch.Tensor:
        """
        This function is meant for sampling points in [0, 1] * [0, 1] coordinate space based on their uncertainty. The
        uncertainty is calculated for each point using the passed `uncertainty function` that takes points logit
        prediction as input.

        Args:
            logits (float):
                logit predictions for P points
            uncertainty_function:
                A function that takes logit predictions for P points and returns their uncertainties
            num_points (int):
                The number of points P to sample.
            oversample_ratio (int):
                Oversampling parameter.
            importance_sample_ratio (float):
                Ratio of points that are sampled via importance sampling.

        Returns:
            point_coordinates (torch.Tensor):
                coordinates for P sampled points
        """

        num_boxes = logits.shape[0]
        num_points_sampled = int(num_points * oversample_ratio)

        # Get random point coordinates
        point_coordinates = torch.rand(num_boxes, num_points_sampled, 2, device=logits.device)
        # Get sampled prediction value for the point coordinates
        point_logits = sample_point(logits, point_coordinates, align_corners=False)
        # Calculate the uncertainties based on the sampled prediction values of the points
        point_uncertainties = uncertainty_function(point_logits)

        num_uncertain_points = int(importance_sample_ratio * num_points)
        num_random_points = num_points - num_uncertain_points

        idx = torch.topk(point_uncertainties[:, 0, :], k=num_uncertain_points, dim=1)[1]
        shift = num_points_sampled * torch.arange(num_boxes, dtype=torch.long, device=logits.device)
        idx += shift[:, None]
        point_coordinates = point_coordinates.view(-1, 2)[idx.view(-1), :].view(num_boxes, num_uncertain_points, 2)

        if num_random_points > 0:
            point_coordinates = torch.cat(
                [point_coordinates, torch.rand(num_boxes, num_random_points, 2, device=logits.device)],
                dim=1,
            )
        return point_coordinates

    def forward(
        self,
        masks_queries_logits: torch.Tensor,
        class_queries_logits: torch.Tensor,
        mask_labels: List[torch.Tensor],
        class_labels: List[torch.Tensor],
        auxiliary_predictions: Optional[Dict[str, torch.Tensor]] = None,
    ) -> Dict[str, torch.Tensor]:
        """
        This performs the loss computation.

        Args:
            masks_queries_logits (`torch.Tensor`):
                A tensor of shape `batch_size, num_queries, height, width`
            class_queries_logits (`torch.Tensor`):
                A tensor of shape `batch_size, num_queries, num_labels`
            mask_labels (`torch.Tensor`):
                List of mask labels of shape `(labels, height, width)`.
            class_labels (`List[torch.Tensor]`):
                List of class labels of shape `(labels)`.
            auxiliary_predictions (`Dict[str, torch.Tensor]`, *optional*):
                if `use_auxiliary_loss` was set to `true` in [`Mask2FormerConfig`], then it contains the logits from
                the inner layers of the MaskedAttentionDecoder.

        Returns:
            `Dict[str, Tensor]`: A dict of `torch.Tensor` containing two keys:
            - **loss_cross_entropy** -- The loss computed using cross entropy on the predicted and ground truth labels.
            - **loss_mask** -- The loss computed using sigmoid cross_entropy loss on the predicted and ground truth
              masks.
            - **loss_dice** -- The loss computed using dice loss on the predicted on the predicted and ground truth
              masks.
            if `use_auxiliary_loss` was set to `true` in [`Mask2FormerConfig`], the dictionary contains additional
            losses for each auxiliary predictions.
        """

        # retrieve the matching between the outputs of the last layer and the labels
        indices = self.matcher(masks_queries_logits, class_queries_logits, mask_labels, class_labels)
        # compute the average number of target masks for normalization purposes
        num_masks: Number = self.get_num_masks(class_labels, device=class_labels[0].device)
        # get all the losses
        losses: Dict[str, Tensor] = {
            **self.loss_masks(masks_queries_logits, mask_labels, indices, num_masks),
            **self.loss_labels(class_queries_logits, class_labels, indices),
        }
        # in case of auxiliary losses, we repeat this process with the output of each intermediate layer.
        if auxiliary_predictions is not None:
            for idx, aux_outputs in enumerate(auxiliary_predictions):
                masks_queries_logits = aux_outputs["masks_queries_logits"]
                class_queries_logits = aux_outputs["class_queries_logits"]
                loss_dict = self.forward(masks_queries_logits, class_queries_logits, mask_labels, class_labels)
                loss_dict = {f"{key}_{idx}": value for key, value in loss_dict.items()}
                losses.update(loss_dict)

        return losses

    def get_num_masks(self, class_labels: torch.Tensor, device: torch.device) -> torch.Tensor:
        """
        Computes the average number of target masks across the batch, for normalization purposes.
        """
        num_masks = sum([len(classes) for classes in class_labels])
        num_masks_pt = torch.as_tensor([num_masks], dtype=torch.float, device=device)
        return num_masks_pt


def multi_scale_deformable_attention(value, value_spatial_shapes, sampling_locations, attention_weights):
    batch_size, S_, num_attn_head, D_ = value.shape
    _, Lq_, num_attn_head, L_, P_, _ = sampling_locations.shape
    value_list = value.split([height * width for height, width in value_spatial_shapes], dim=1)
    sampling_grids = 2 * sampling_locations - 1
    sampling_value_list = []

    for idx, (height, width) in enumerate(value_spatial_shapes):
        # batch_size, height*width, num_attn_head, D_ -> batch_size*num_attn_head, D_, height, width
        value_l_ = value_list[idx].flatten(2).transpose(1, 2).reshape(batch_size * num_attn_head, D_, height, width)
        # (batch_size, Lq_, num_attn_head, P_) -> (batch_size * num_attn_head, Lq_, P_, 2)
        sampling_grid_l_ = sampling_grids[:, :, :, idx].transpose(1, 2).flatten(0, 1)
        # batch_size*num_attn_head, D_, Lq_, P_
        sampling_value_l_ = F.grid_sample(
            value_l_, sampling_grid_l_, mode="bilinear", padding_mode="zeros", align_corners=False
        )
        sampling_value_list.append(sampling_value_l_)

    # (batch_size, Lq_, num_attn_head, L_, P_) -> (batch_size, num_attn_head, 1, Lq_, L_*P_)
    attention_weights = attention_weights.transpose(1, 2).reshape(batch_size * num_attn_head, 1, Lq_, L_ * P_)
    output = (
        (torch.stack(sampling_value_list, dim=-2).flatten(-2) * attention_weights)
        .sum(-1)
        .view(batch_size, num_attn_head * D_, Lq_)
    )
    return output.transpose(1, 2).contiguous()


# Copied from transformers.models.maskformer.modeling_maskformer.MaskFormerSinePositionEmbedding with MaskFormer->Mask2Former
class Mask2FormerSinePositionEmbedding(nn.Module):
    """
    This is a more standard version of the position embedding, very similar to the one used by the Attention is all you
    need paper, generalized to work on images.
    """

    def __init__(
        self, num_pos_feats: int = 64, temperature: int = 10000, normalize: bool = False, scale: Optional[float] = None
    ):
        super().__init__()
        if scale is not None and normalize is False:
            raise ValueError("normalize should be True if scale is passed")
        self.num_pos_feats = num_pos_feats
        self.temperature = temperature
        self.normalize = normalize
        self.scale = 2 * math.pi if scale is None else scale

    def forward(self, x: Tensor, mask: Optional[Tensor] = None) -> Tensor:
        if mask is None:
            mask = torch.zeros((x.size(0), x.size(2), x.size(3)), device=x.device, dtype=torch.bool)
        not_mask = ~mask
        y_embed = not_mask.cumsum(1, dtype=torch.float32)
        x_embed = not_mask.cumsum(2, dtype=torch.float32)
        if self.normalize:
            eps = 1e-6
            y_embed = y_embed / (y_embed[:, -1:, :] + eps) * self.scale
            x_embed = x_embed / (x_embed[:, :, -1:] + eps) * self.scale

        dim_t = torch.arange(self.num_pos_feats, dtype=torch.float32, device=x.device)
        dim_t = self.temperature ** (2 * torch.div(dim_t, 2, rounding_mode="floor") / self.num_pos_feats)

        pos_x = x_embed[:, :, :, None] / dim_t
        pos_y = y_embed[:, :, :, None] / dim_t
        pos_x = torch.stack((pos_x[:, :, :, 0::2].sin(), pos_x[:, :, :, 1::2].cos()), dim=4).flatten(3)
        pos_y = torch.stack((pos_y[:, :, :, 0::2].sin(), pos_y[:, :, :, 1::2].cos()), dim=4).flatten(3)
        pos = torch.cat((pos_y, pos_x), dim=3).permute(0, 3, 1, 2)
        return pos


# Modified from transformers.models.detr.modeling_deformable_detr.DeformableDetrMultiscaleDeformableAttention with DeformableDetr->Mask2FormerPixelDecoderEncoder
class Mask2FormerPixelDecoderEncoderMultiscaleDeformableAttention(nn.Module):
    """
    Multiscale deformable attention as proposed in Deformable DETR.
    """

    def __init__(self, embed_dim: int, num_heads: int, n_levels: int, n_points: int):
        super().__init__()
        if embed_dim % num_heads != 0:
            raise ValueError(
                f"embed_dim (d_model) must be divisible by num_heads, but got {embed_dim} and {num_heads}"
            )
        dim_per_head = embed_dim // num_heads
        # check if dim_per_head is power of 2
        if not ((dim_per_head & (dim_per_head - 1) == 0) and dim_per_head != 0):
            warnings.warn(
                "You'd better set embed_dim (d_model) in DeformableDetrMultiscaleDeformableAttention to make the"
                " dimension of each attention head a power of 2 which is more efficient in the authors' CUDA"
                " implementation."
            )

        self.im2col_step = 128

        self.d_model = embed_dim
        self.n_levels = n_levels
        self.n_heads = num_heads
        self.n_points = n_points

        self.sampling_offsets = nn.Linear(embed_dim, num_heads * n_levels * n_points * 2)
        self.attention_weights = nn.Linear(embed_dim, num_heads * n_levels * n_points)
        self.value_proj = nn.Linear(embed_dim, embed_dim)
        self.output_proj = nn.Linear(embed_dim, embed_dim)

        self._reset_parameters()

    def _reset_parameters(self):
        nn.init.constant_(self.sampling_offsets.weight.data, 0.0)
        thetas = torch.arange(self.n_heads, dtype=torch.float32) * (2.0 * math.pi / self.n_heads)
        grid_init = torch.stack([thetas.cos(), thetas.sin()], -1)
        grid_init = (
            (grid_init / grid_init.abs().max(-1, keepdim=True)[0])
            .view(self.n_heads, 1, 1, 2)
            .repeat(1, self.n_levels, self.n_points, 1)
        )
        for i in range(self.n_points):
            grid_init[:, :, i, :] *= i + 1
        with torch.no_grad():
            self.sampling_offsets.bias = nn.Parameter(grid_init.view(-1))
        nn.init.constant_(self.attention_weights.weight.data, 0.0)
        nn.init.constant_(self.attention_weights.bias.data, 0.0)
        nn.init.xavier_uniform_(self.value_proj.weight.data)
        nn.init.constant_(self.value_proj.bias.data, 0.0)
        nn.init.xavier_uniform_(self.output_proj.weight.data)
        nn.init.constant_(self.output_proj.bias.data, 0.0)

    def with_pos_embed(self, tensor: torch.Tensor, position_embeddings: Optional[Tensor]):
        return tensor if position_embeddings is None else tensor + position_embeddings

    def forward(
        self,
        hidden_states: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        encoder_hidden_states=None,
        encoder_attention_mask=None,
        position_embeddings: Optional[torch.Tensor] = None,
        reference_points=None,
        spatial_shapes=None,
        level_start_index=None,
        output_attentions: bool = False,
    ):
        # add position embeddings to the hidden states before projecting to queries and keys
        if position_embeddings is not None:
            hidden_states = self.with_pos_embed(hidden_states, position_embeddings)

        batch_size, num_queries, _ = hidden_states.shape
        batch_size, sequence_length, _ = encoder_hidden_states.shape
        if (spatial_shapes[:, 0] * spatial_shapes[:, 1]).sum() != sequence_length:
            raise ValueError(
                "Make sure to align the spatial shapes with the sequence length of the encoder hidden states"
            )

        value = self.value_proj(encoder_hidden_states)
        if attention_mask is not None:
            # we invert the attention_mask
            value = value.masked_fill(attention_mask[..., None], float(0))
        value = value.view(batch_size, sequence_length, self.n_heads, self.d_model // self.n_heads)
        sampling_offsets = self.sampling_offsets(hidden_states).view(
            batch_size, num_queries, self.n_heads, self.n_levels, self.n_points, 2
        )
        attention_weights = self.attention_weights(hidden_states).view(
            batch_size, num_queries, self.n_heads, self.n_levels * self.n_points
        )
        attention_weights = F.softmax(attention_weights, -1).view(
            batch_size, num_queries, self.n_heads, self.n_levels, self.n_points
        )
        # batch_size, num_queries, n_heads, n_levels, n_points, 2
        if reference_points.shape[-1] == 2:
            offset_normalizer = torch.stack([spatial_shapes[..., 1], spatial_shapes[..., 0]], -1)
            sampling_locations = (
                reference_points[:, :, None, :, None, :]
                + sampling_offsets / offset_normalizer[None, None, None, :, None, :]
            )
        elif reference_points.shape[-1] == 4:
            sampling_locations = (
                reference_points[:, :, None, :, None, :2]
                + sampling_offsets / self.n_points * reference_points[:, :, None, :, None, 2:] * 0.5
            )
        else:
            raise ValueError(f"Last dim of reference_points must be 2 or 4, but got {reference_points.shape[-1]}")

        output = multi_scale_deformable_attention(value, spatial_shapes, sampling_locations, attention_weights)
        output = self.output_proj(output)

        return output, attention_weights


class Mask2FormerPixelDecoderEncoderLayer(nn.Module):
    def __init__(self, config: Mask2FormerConfig):
        super().__init__()
        self.embed_dim = config.decoder_config["feature_size"]
        self.self_attn = Mask2FormerPixelDecoderEncoderMultiscaleDeformableAttention(
            embed_dim=self.embed_dim,
            num_heads=config.decoder_config["num_heads"],
            n_levels=3,
            n_points=4,
        )

        self.self_attn_layer_norm = nn.LayerNorm(self.embed_dim)
        self.dropout = config.decoder_config["dropout"]
        self.activation_fn = F.relu
        self.activation_dropout = config.decoder_config["dropout"]
        self.fc1 = nn.Linear(self.embed_dim, config.decoder_config["encoder_feedforward_dim"])
        self.fc2 = nn.Linear(config.decoder_config["encoder_feedforward_dim"], self.embed_dim)
        self.final_layer_norm = nn.LayerNorm(self.embed_dim)

        self.training = config.general_config["is_train"]

    def forward(
        self,
        hidden_states: torch.Tensor,
        attention_mask: torch.Tensor,
        position_embeddings: torch.Tensor = None,
        reference_points=None,
        spatial_shapes=None,
        level_start_index=None,
        output_attentions: bool = False,
    ):
        """
        Args:
            hidden_states (`torch.FloatTensor` of shape `(batch_size, sequence_length, hidden_size)`):
                Input to the layer.
            attention_mask (`torch.FloatTensor` of shape `(batch_size, sequence_length)`):
                Attention mask.
            position_embeddings (`torch.FloatTensor`, *optional*):
                Position embeddings, to be added to `hidden_states`.
            reference_points (`torch.FloatTensor`, *optional*):
                Reference points.
            spatial_shapes (`torch.LongTensor`, *optional*):
                Spatial shapes of the backbone feature maps.
            level_start_index (`torch.LongTensor`, *optional*):
                Level start index.
            output_attentions (`bool`, *optional*):
                Whether or not to return the attentions tensors of all attention layers. See `attentions` under
                returned tensors for more detail.
        """
        residual = hidden_states

        # Apply Multi-scale Deformable Attention Module on the multi-scale feature maps.
        hidden_states, attn_weights = self.self_attn(
            hidden_states=hidden_states,
            attention_mask=attention_mask,
            encoder_hidden_states=hidden_states,
            encoder_attention_mask=attention_mask,
            position_embeddings=position_embeddings,
            reference_points=reference_points,
            spatial_shapes=spatial_shapes,
            level_start_index=level_start_index,
            output_attentions=output_attentions,
        )

        hidden_states = F.dropout(hidden_states, p=self.dropout, training=self.training)
        hidden_states = residual + hidden_states
        hidden_states = self.self_attn_layer_norm(hidden_states)

        residual = hidden_states
        hidden_states = self.activation_fn(self.fc1(hidden_states))
        hidden_states = F.dropout(hidden_states, p=self.activation_dropout, training=self.training)

        hidden_states = self.fc2(hidden_states)
        hidden_states = F.dropout(hidden_states, p=self.dropout, training=self.training)

        hidden_states = residual + hidden_states
        hidden_states = self.final_layer_norm(hidden_states)

        if self.training:
            if torch.isinf(hidden_states).any() or torch.isnan(hidden_states).any():
                clamp_value = torch.finfo(hidden_states.dtype).max - 1000
                hidden_states = torch.clamp(hidden_states, min=-clamp_value, max=clamp_value)

        outputs = (hidden_states,)

        if output_attentions:
            outputs += (attn_weights,)

        return outputs


# Modified from from transformers.models.detr.modeling_deformable_detr.DeformableDetrEncoder with DeformableDetrEncoder->Mask2FormerPixelDecoderEncoderOnly
class Mask2FormerPixelDecoderEncoderOnly(nn.Module):
    """
    Transformer encoder consisting of *config.decoder_config["encoder_layers"]* deformable attention layers. Each layer
    is a [`Mask2FormerPixelDecoderEncoderLayer`]. The encoder updates the flattened multi-scale feature maps through
    multiple deformable attention layers.

    Args:
        config: Mask2FormerConfig
    """

    def __init__(self, config: Mask2FormerConfig):
        super().__init__()

        self.config = config
        self.dropout = config.decoder_config["dropout"]
        self.layers = nn.ModuleList(
            [Mask2FormerPixelDecoderEncoderLayer(config) for _ in range(config.decoder_config["encoder_layers"])]
        )

        self._reset_parameters()

    def _reset_parameters(self):
        for p in self.parameters():
            if p.dim() > 1:
                nn.init.xavier_uniform_(p)

    @staticmethod
    def get_reference_points(spatial_shapes, valid_ratios, device):
        """
        Get reference points for each feature map. Used in decoder.

        Args:
            spatial_shapes (`torch.LongTensor`):
                Spatial shapes of each feature map, has shape of `(num_feature_levels, 2)`.
            valid_ratios (`torch.FloatTensor`):
                Valid ratios of each feature map, has shape of `(batch_size, num_feature_levels, 2)`.
            device (`torch.device`):
                Device on which to create the tensors.
        Returns:
            `torch.FloatTensor` of shape `(batch_size, num_queries, num_feature_levels, 2)`
        """
        reference_points_list = []
        for lvl, (height, width) in enumerate(spatial_shapes):
            ref_y, ref_x = torch.meshgrid(
                torch.linspace(0.5, height - 0.5, height, dtype=torch.float32, device=device),
                torch.linspace(0.5, width - 0.5, width, dtype=torch.float32, device=device),
            )
            ref_y = ref_y.reshape(-1)[None] / (valid_ratios[:, None, lvl, 1] * height)
            ref_x = ref_x.reshape(-1)[None] / (valid_ratios[:, None, lvl, 0] * width)
            ref = torch.stack((ref_x, ref_y), -1)
            reference_points_list.append(ref)

        reference_points = torch.cat(reference_points_list, 1)
        reference_points = reference_points[:, :, None] * valid_ratios[:, None]

        return reference_points

    def forward(
        self,
        inputs_embeds=None,
        attention_mask=None,
        position_embeddings=None,
        spatial_shapes=None,
        level_start_index=None,
        valid_ratios=None,
        output_attentions=None,
        output_hidden_states=None,
        return_dict=None,
    ):
        r"""
        Args:
            inputs_embeds (`torch.FloatTensor` of shape `(batch_size, sequence_length, hidden_size)`):
                Flattened feature map (output of the backbone + projection layer) that is passed to the encoder.
            attention_mask (`torch.Tensor` of shape `(batch_size, sequence_length)`, *optional*):
                Mask to avoid performing attention on padding pixel features. Mask values selected in `[0, 1]`:
                - 1 for pixel features that are real (i.e. **not masked**),
                - 0 for pixel features that are padding (i.e. **masked**).
                [What are attention masks?](../glossary#attention-mask)
            position_embeddings (`torch.FloatTensor` of shape `(batch_size, sequence_length, hidden_size)`):
                Position embeddings that are added to the queries and keys in each self-attention layer.
            spatial_shapes (`torch.LongTensor` of shape `(num_feature_levels, 2)`):
                Spatial shapes of each feature map.
            level_start_index (`torch.LongTensor` of shape `(num_feature_levels)`):
                Starting index of each feature map.
            valid_ratios (`torch.FloatTensor` of shape `(batch_size, num_feature_levels, 2)`):
                Ratio of valid area in each feature level.
            output_attentions (`bool`, *optional*):
                Whether or not to return the attentions tensors of all attention layers. See `attentions` under
                returned tensors for more detail.
            output_hidden_states (`bool`, *optional*):
                Whether or not to return the hidden states of all layers. See `hidden_states` under returned tensors
                for more detail.
            return_dict (`bool`, *optional*):
                Whether or not to return a [`~file_utils.ModelOutput`] instead of a plain tuple.
        """
        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )
        return_dict = return_dict if return_dict is not None else self.config.use_return_dict

        hidden_states = inputs_embeds
        reference_points = self.get_reference_points(spatial_shapes, valid_ratios, device=inputs_embeds.device)

        encoder_states = () if output_hidden_states else None
        all_attentions = () if output_attentions else None

        for i, encoder_layer in enumerate(self.layers):
            if output_hidden_states:
                encoder_states = encoder_states + (hidden_states,)

            layer_outputs = encoder_layer(
                hidden_states,
                attention_mask,
                position_embeddings=position_embeddings,
                reference_points=reference_points,
                spatial_shapes=spatial_shapes,
                level_start_index=level_start_index,
                output_attentions=output_attentions,
            )

            hidden_states = layer_outputs[0]

            if output_attentions:
                all_attentions = all_attentions + (layer_outputs[1],)

        if output_hidden_states:
            encoder_states = encoder_states + (hidden_states,)

        return BaseModelOutput(
            last_hidden_state=hidden_states, hidden_states=encoder_states, attentions=all_attentions
        )


# Modified from from transformers.models.detr.modeling_deformable_detr.DeformableDetrModel with DeformableDetrModel->Mask2FormerPixelDecoder
class Mask2FormerPixelDecoder(nn.Module):
    def __init__(self, config: Mask2FormerConfig, feature_channels):
        super().__init__()

        self.config = config

        feature_dim = config.decoder_config["feature_size"]
        mask_dim = config.decoder_config["mask_feature_size"]
        num_pos_features = feature_dim // 2

        self.position_embedding = Mask2FormerSinePositionEmbedding(num_pos_feats=num_pos_features, normalize=True)
        self.num_feature_levels = 3
        transformer_in_channels = feature_channels[-self.num_feature_levels :]

        self.transformer_feature_strides = config.general_config["feature_strides"][-self.num_feature_levels :]
        self.feature_channels = feature_channels
        self.level_embed = nn.Parameter(torch.Tensor(self.num_feature_levels, feature_dim))

        # Create input projection layers
        if self.num_feature_levels > 1:
            input_projections_list = []
            for in_channels in transformer_in_channels[::-1]:
                input_projections_list.append(
                    nn.Sequential(
                        nn.Conv2d(in_channels, feature_dim, kernel_size=1),
                        nn.GroupNorm(32, feature_dim),
                    )
                )
            self.input_projections = nn.ModuleList(input_projections_list)
        else:
            self.input_projections = nn.ModuleList(
                [
                    nn.Sequential(
                        nn.Conv2d(transformer_in_channels[-1], feature_dim, kernel_size=1),
                        nn.GroupNorm(32, feature_dim),
                    )
                ]
            )

        self.encoder = Mask2FormerPixelDecoderEncoderOnly(config)
        self.mask_projection = nn.Conv2d(feature_dim, mask_dim, kernel_size=1, stride=1, padding=0)

        # Extra FPN levels
        stride = min(self.transformer_feature_strides)
        self.common_stride = config.decoder_config["common_stride"]
        self.num_fpn_levels = int(np.log2(stride) - np.log2(self.common_stride))

        lateral_convs = []
        output_convs = []

        for idx, in_channels in enumerate(self.feature_channels[: self.num_fpn_levels]):
            lateral_conv = nn.Sequential(
                nn.Conv2d(in_channels, feature_dim, kernel_size=1, bias=False),
                nn.GroupNorm(32, feature_dim),
            )

            output_conv = nn.Sequential(
                nn.Conv2d(feature_dim, feature_dim, kernel_size=3, stride=1, padding=1, bias=False),
                nn.GroupNorm(32, feature_dim),
                nn.ReLU(),
            )
            self.add_module("adapter_{}".format(idx + 1), lateral_conv)
            self.add_module("layer_{}".format(idx + 1), output_conv)

            lateral_convs.append(lateral_conv)
            output_convs.append(output_conv)

        # Order convolutional layers from low to high resolution
        self.lateral_convolutions = lateral_convs[::-1]
        self.output_convolutions = output_convs[::-1]

        self._reset_parameters()

    def _reset_parameters(self):
        for p in self.parameters():
            if p.dim() > 1:
                nn.init.xavier_uniform_(p)
        nn.init.normal_(self.level_embed, std=0)

    def get_valid_ratio(self, mask):
        """Get the valid ratio of all feature maps."""

        _, height, width = mask.shape
        valid_height = torch.sum(~mask[:, :, 0], 1)
        valid_width = torch.sum(~mask[:, 0, :], 1)
        valid_ratio_heigth = valid_height.float() / height
        valid_ratio_width = valid_width.float() / width
        valid_ratio = torch.stack([valid_ratio_width, valid_ratio_heigth], -1)
        return valid_ratio

    def forward(
        self,
        features,
        encoder_outputs=None,
        output_attentions=None,
        output_hidden_states=None,
        return_dict=None,
    ):
        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )

        # Then, apply 1x1 convolution to reduce the channel dimension to d_model (256 by default)
        input_embeds = []
        position_embeddings = []
        for level, x in enumerate(features[::-1][: self.num_feature_levels]):
            input_embeds.append(self.input_projections[level](x.float()))
            position_embeddings.append(self.position_embedding(x.float()))

        masks = [
            torch.zeros((x.size(0), x.size(2), x.size(3)), device=x.device, dtype=torch.bool) for x in input_embeds
        ]

        # Prepare encoder inputs (by flattening)
        spatial_shapes = [(embed.shape[2], embed.shape[3]) for embed in input_embeds]
        input_embeds_flat = torch.cat([embed.flatten(2).transpose(1, 2) for embed in input_embeds], 1)
        spatial_shapes = torch.as_tensor(spatial_shapes, dtype=torch.long, device=input_embeds_flat.device)
        masks_flat = torch.cat([mask.flatten(1) for mask in masks], 1)

        position_embeddings = [embed.flatten(2).transpose(1, 2) for embed in position_embeddings]
        level_pos_embed_flat = [x + self.level_embed[i].view(1, 1, -1) for i, x in enumerate(position_embeddings)]
        level_pos_embed_flat = torch.cat(level_pos_embed_flat, 1)

        level_start_index = torch.cat((spatial_shapes.new_zeros((1,)), spatial_shapes.prod(1).cumsum(0)[:-1]))
        valid_ratios = torch.stack([self.get_valid_ratio(mask) for mask in masks], 1)

        # Send input_embeds_flat + masks_flat + level_pos_embed_flat (backbone + proj layer output) through encoder
        if encoder_outputs is None:
            encoder_outputs = self.encoder(
                inputs_embeds=input_embeds_flat,
                attention_mask=masks_flat,
                position_embeddings=level_pos_embed_flat,
                spatial_shapes=spatial_shapes,
                level_start_index=level_start_index,
                valid_ratios=valid_ratios,
                output_attentions=output_attentions,
                output_hidden_states=output_hidden_states,
                return_dict=return_dict,
            )

        # Compute final features
        encoder_features = []
        for i, feature in enumerate(encoder_outputs):
            batch_size = feature.shape[0]
            height, width = spatial_shapes[i][0], spatial_shapes[i][1]
            feature = feature.transpose(1, 2).view(batch_size, -1, height, width)
            encoder_features.append(feature)

        return encoder_features

        last_hidden_state = encoder_outputs.last_hidden_state
        batch_size = last_hidden_state.shape[0]

        split_sizes = [None] * self.num_feature_levels
        for i in range(self.num_feature_levels):
            if i < self.num_feature_levels - 1:
                split_sizes[i] = level_start_index[i + 1] - level_start_index[i]
            else:
                split_sizes[i] = last_hidden_state.shape[1] - level_start_index[i]

        encoder_output = torch.split(last_hidden_state, split_sizes, dim=1)

        # Compute final features
        outputs = [
            x.transpose(1, 2).view(batch_size, -1, spatial_shapes[i][0], spatial_shapes[i][1])
            for i, x in enumerate(encoder_output)
        ]

        # Append extra FPN levels to outputs, ordered from low to high resolution
        for idx, feature in enumerate(features[: self.num_fpn_levels][::-1]):
            lateral_conv = self.lateral_convolutions[idx]
            output_conv = self.output_convolutions[idx]
            current_fpn = lateral_conv(feature.float())

            # Following FPN implementation, we use nearest upsampling here
            out = current_fpn + F.interpolate(
                outputs[-1], size=current_fpn.shape[-2:], mode="bilinear", align_corners=False
            )
            out = output_conv(out)
            outputs.append(out)

        num_cur_levels = 0
        multi_scale_features = []

        for out in outputs:
            if num_cur_levels < self.num_feature_levels:
                multi_scale_features.append(out)
                num_cur_levels += 1

        return Mask2FormerPixelDecoderOutput(
            mask_features=self.mask_projection(outputs[-1]),
            multi_scale_features=multi_scale_features,
            attentions=encoder_outputs.attentions,
        )


class Mask2FormerPixelLevelModule(nn.Module):
    def __init__(self, config: Mask2FormerConfig):
        """
        Pixel Level Module proposed in [Masked-attention Mask Transformer for Universal Image
        Segmentation](https://arxiv.org/abs/2112.01527). It runs the input image through a backbone and a pixel
        decoder, generating multi-scale feature maps and pixel embeddings.

        Args:
            config ([`Mask2FormerConfig`]):
                The configuration used to instantiate this model.
        """
        super().__init__()
        backbone_config = config.backbone_config
        if backbone_config.model_type == "swin":
            # for backwards compatibility
            backbone_config = MaskFormerSwinConfig.from_dict(backbone_config.to_dict())
            backbone_config.out_features = ["stage1", "stage2", "stage3", "stage4"]

        self.encoder = AutoBackbone.from_config(backbone_config)
        self.decoder = Mask2FormerPixelDecoder(config, feature_channels=self.encoder.channels)

    def forward(self, pixel_values: Tensor, output_hidden_states: bool = False) -> Mask2FormerPixelLevelModuleOutput:
        backbone_features = self.encoder(pixel_values).feature_maps
        decoder_output: Mask2FormerPixelDecoderOutput = self.decoder(
            backbone_features, output_hidden_states=output_hidden_states
        )

        return Mask2FormerPixelLevelModuleOutput(
            encoder_hidden_states=tuple(backbone_features) if output_hidden_states else (),
            decoder_last_hidden_state=decoder_output.mask_features,
            decoder_hidden_states=decoder_output.multi_scale_features,
        )


MASK2FORMER_START_DOCSTRING = r"""
    This model is a PyTorch [torch.nn.Module](https://pytorch.org/docs/stable/nn.html#torch.nn.Module) sub-class. Use
    it as a regular PyTorch Module and refer to the PyTorch documentation for all matter related to general usage and
    behavior.

    Parameters:
        config ([`Mask2FormerConfig`]): Model configuration class with all the parameters of the model.
            Initializing with a config file does not load the weights associated with the model, only the
            configuration. Check out the [`~PreTrainedModel.from_pretrained`] method to load the model weights.
"""

MASK2FORMER_INPUTS_DOCSTRING = r"""
    Args:
        pixel_values (`torch.FloatTensor` of shape `(batch_size, num_channels, height, width)`):
            Pixel values. Pixel values can be obtained using [`AutoFeatureExtractor`]. See
            [`AutoFeatureExtractor.__call__`] for details.
        pixel_mask (`torch.LongTensor` of shape `(batch_size, height, width)`, *optional*):
            Mask to avoid performing attention on padding pixel values. Mask values selected in `[0, 1]`:

            - 1 for pixels that are real (i.e. **not masked**),
            - 0 for pixels that are padding (i.e. **masked**).

            [What are attention masks?](../glossary#attention-mask)
        output_hidden_states (`bool`, *optional*):
            Whether or not to return the hidden states of all layers. See `hidden_states` under returned tensors for
            more detail.
        output_attentions (`bool`, *optional*):
            Whether or not to return the attentions tensors of Detr's decoder attention layers.
        return_dict (`bool`, *optional*):
            Whether or not to return a [`~Mask2FormerModelOutput`] instead of a plain tuple.
"""


def c2_xavier_fill(module: nn.Module) -> None:
    """
    Initialize `module.weight` using the "XavierFill" implemented in Caffe2. Also initializes `module.bias` to 0.
    Caffe2 implementation of XavierFill corresponds to kaiming_uniform_ in PyTorch

    Args:
        module (torch.nn.Module): module to initialize.
    """
    nn.init.kaiming_uniform_(module.weight, a=1)
    if module.bias is not None:
        nn.init.constant_(module.bias, 0)


class Mask2FormerPreTrainedModel(PreTrainedModel):
    config_class = Mask2FormerConfig
    base_model_prefix = "model"
    main_input_name = "pixel_values"

    def _init_weights(self, module: nn.Module):
        xavier_std = self.config.init_xavier_std
        std = self.config.init_std

        if isinstance(module, Mask2FormerTransformerModule):
            if module.input_projections is not None:
                for input_projection in module.input_projections:
                    if not isinstance(input_projection, nn.Sequential):
                        nn.init.xavier_uniform_(input_projection.weight, gain=xavier_std)
                        nn.init.constant_(input_projection.bias, 0)
        elif isinstance(module, Mask2FormerTransformerDecoder):
            nn.init.xavier_uniform_(module.query_input_projection.weight, gain=xavier_std)
            nn.init.constant_(module.query_input_projection.bias, 0)
        elif isinstance(module, Mask2FormerPixelDecoderEncoderMultiscaleDeformableAttention):
            module._reset_parameters()
        elif isinstance(module, Mask2FormerPixelLevelModule):
            for submodule in module.modules():
                if isinstance(submodule, (nn.Conv2d, nn.Linear)):
                    submodule.weight.data.normal_(mean=0.0, std=std)
                    if submodule.bias is not None:
                        submodule.bias.data.zero_()
        elif isinstance(module, (nn.Linear, nn.Conv2d, nn.BatchNorm2d)):
            module.weight.data.normal_(mean=0.0, std=std)
            if module.bias is not None:
                module.bias.data.zero_()
        elif isinstance(module, nn.Embedding):
            module.weight.data.normal_(mean=0.0, std=std)
            if module.padding_idx is not None:
                module.weight.data[module.padding_idx].zero_()
        if hasattr(module, "reference_points"):
            nn.init.xavier_uniform_(module.reference_points.weight.data, gain=1.0)
            nn.init.constant_(module.reference_points.bias.data, 0.0)
        elif isinstance(module, nn.Embedding):
            module.weight.data.normal_(mean=0.0, std=std)
            if module.padding_idx is not None:
                module.weight.data[module.padding_idx].zero_()
        elif isinstance(module, nn.MultiheadAttention):
            module.in_proj_weight.data.normal_(mean=0.0, std=std)
            module.in_proj_bias.data.zero_()


# Copied from transformers.models.maskformer.modeling_maskformer.PredictionBlock with MaskFormer->Mask2Former
class PredictionBlock(nn.Module):
    def __init__(self, in_dim: int, out_dim: int, activation: nn.Module) -> None:
        super().__init__()
        self.layers = [nn.Linear(in_dim, out_dim), activation]
        # Maintain submodule indexing as if part of a Sequential block
        for i, layer in enumerate(self.layers):
            self.add_module(str(i), layer)

    def forward(self, input: Tensor) -> Tensor:
        hidden_state = input
        for layer in self.layers:
            hidden_state = layer(hidden_state)
        return hidden_state


# Modified from transformers.models.detr.modeling_detr.DetrAttention with Detr->Mask2Former
class Mask2FormerAttention(nn.Module):
    """
    Multi-headed attention from 'Attention Is All You Need' paper. Here, we add position embeddings to the queries and
    keys (as explained in the DETR paper).
    """

    def __init__(
        self,
        embed_dim: int,
        num_heads: int,
        dropout: float = 0.0,
        is_decoder: bool = False,
        bias: bool = True,
    ):
        super().__init__()
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.dropout = dropout
        self.head_dim = embed_dim // num_heads
        if self.head_dim * num_heads != self.embed_dim:
            raise ValueError(
                f"embed_dim must be divisible by num_heads (got `embed_dim`: {self.embed_dim} and `num_heads`:"
                f" {num_heads})."
            )
        self.scaling = self.head_dim**-0.5

        self.k_proj = nn.Linear(embed_dim, embed_dim, bias=bias)
        self.v_proj = nn.Linear(embed_dim, embed_dim, bias=bias)
        self.q_proj = nn.Linear(embed_dim, embed_dim, bias=bias)
        self.out_proj = nn.Linear(embed_dim, embed_dim, bias=bias)

    def _shape(self, tensor: torch.Tensor, seq_len: int, batch_size: int):
        return tensor.view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2).contiguous()

    def with_pos_embed(self, tensor: torch.Tensor, position_embeddings: Optional[Tensor]):
        return tensor if position_embeddings is None else tensor + position_embeddings

    def forward(
        self,
        hidden_states: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        position_embeddings: Optional[torch.Tensor] = None,
        key_value_states: Optional[torch.Tensor] = None,
        key_value_position_embeddings: Optional[torch.Tensor] = None,
        output_attentions: bool = False,
    ) -> Tuple[torch.Tensor, Optional[torch.Tensor], Optional[Tuple[torch.Tensor]]]:
        """Input shape: Batch x Time x Channel"""

        hidden_states = hidden_states.permute(1, 0, 2) if hidden_states is not None else None
        position_embeddings = position_embeddings.permute(1, 0, 2) if position_embeddings is not None else None
        key_value_states = key_value_states.permute(1, 0, 2) if key_value_states is not None else None
        key_value_position_embeddings = (
            key_value_position_embeddings.permute(1, 0, 2) if key_value_position_embeddings is not None else None
        )

        # if key_value_states are provided this layer is used as a cross-attention layer
        # for the decoder
        is_cross_attention = key_value_states is not None
        batch_size, target_len, embed_dim = hidden_states.size()

        # add position embeddings to the hidden states before projecting to queries and keys
        if position_embeddings is not None:
            hidden_states_original = hidden_states
            hidden_states = self.with_pos_embed(hidden_states, position_embeddings)

        # add key-value position embeddings to the key value states
        if key_value_position_embeddings is not None:
            key_value_states_original = key_value_states
            key_value_states = self.with_pos_embed(key_value_states, key_value_position_embeddings)

        # get query proj
        query_states = self.q_proj(hidden_states) * self.scaling
        # get key, value proj
        if is_cross_attention:
            # cross_attentions
            key_states = self._shape(self.k_proj(key_value_states), -1, batch_size)
            value_states = self._shape(self.v_proj(key_value_states_original), -1, batch_size)
        else:
            # self_attention
            key_states = self._shape(self.k_proj(hidden_states), -1, batch_size)
            value_states = self._shape(self.v_proj(hidden_states_original), -1, batch_size)

        proj_shape = (batch_size * self.num_heads, -1, self.head_dim)
        query_states = self._shape(query_states, target_len, batch_size).view(*proj_shape)
        key_states = key_states.view(*proj_shape)
        value_states = value_states.view(*proj_shape)

        source_len = key_states.size(1)

        attn_weights = torch.bmm(query_states, key_states.transpose(1, 2))

        if attn_weights.size() != (batch_size * self.num_heads, target_len, source_len):
            raise ValueError(
                f"Attention weights should be of size {(batch_size * self.num_heads, target_len, source_len)}, but is"
                f" {attn_weights.size()}"
            )

        if attention_mask is not None:
            if attention_mask.size() != (batch_size * self.num_heads, target_len, source_len):
                raise ValueError(
                    f"Attention mask should be of size {(target_len, batch_size * self.num_heads, source_len)}, but is"
                    f" {attention_mask.size()}"
                )
            attn_weights += attention_mask

        attn_weights = nn.functional.softmax(attn_weights, dim=-1)

        if output_attentions:
            # this operation is a bit awkward, but it's required to
            # make sure that attn_weights keeps its gradient.
            # In order to do so, attn_weights have to reshaped
            # twice and have to be reused in the following
            attn_weights_reshaped = attn_weights.view(batch_size, self.num_heads, target_len, source_len)
            attn_weights = attn_weights_reshaped.view(batch_size * self.num_heads, target_len, source_len)
        else:
            attn_weights_reshaped = None

        attn_probs = nn.functional.dropout(attn_weights, p=self.dropout, training=self.training)

        attn_output = torch.bmm(attn_probs, value_states)

        if attn_output.size() != (batch_size * self.num_heads, target_len, self.head_dim):
            raise ValueError(
                f"`attn_output` should be of size {(batch_size, self.num_heads, target_len, self.head_dim)}, but is"
                f" {attn_output.size()}"
            )

        attn_output = attn_output.view(batch_size, self.num_heads, target_len, self.head_dim)
        attn_output = attn_output.transpose(1, 2)
        attn_output = attn_output.reshape(batch_size, target_len, embed_dim)

        attn_output = self.out_proj(attn_output).permute(1, 0, 2)

        return attn_output, attn_weights_reshaped


class Mask2FormerTransformerDecoderSelfAttentionLayer(nn.Module):
    def __init__(self, embed_dim, num_heads, dropout=0.0, activation="relu", normalize_before=False):
        super().__init__()
        self.self_attn = Mask2FormerAttention(
            embed_dim=embed_dim, num_heads=num_heads, dropout=dropout, is_decoder=True
        )

        self.norm = nn.LayerNorm(embed_dim)
        self.dropout = nn.Dropout(dropout)

        self.activation = ACT2FN[activation]
        self.normalize_before = normalize_before

        self._reset_parameters()

    def _reset_parameters(self):
        for p in self.parameters():
            if p.dim() > 1:
                nn.init.xavier_uniform_(p)

    def with_pos_embed(self, tensor, pos: Optional[Tensor]):
        return tensor if pos is None else tensor + pos

    def forward_post(
        self,
        output,
        output_mask: Optional[Tensor] = None,
        output_key_padding_mask: Optional[Tensor] = None,
        query_pos: Optional[Tensor] = None,
    ):
        output2, attention_weights = self.self_attn(
            hidden_states=output, position_embeddings=query_pos, attention_mask=output_mask, output_attentions=True
        )
        output = output + self.dropout(output2)
        output = self.norm(output)

        return output, attention_weights

    def forward_pre(
        self,
        output,
        output_mask: Optional[Tensor] = None,
        output_key_padding_mask: Optional[Tensor] = None,
        query_pos: Optional[Tensor] = None,
    ):
        output2 = self.norm(output)
        output2, attention_weights = self.self_attn(
            hidden_states=output2, position_embeddings=query_pos, attention_mask=output_mask, output_attentions=True
        )
        output = output + self.dropout(output2)

        return output, attention_weights

    def forward(
        self,
        output,
        output_mask: Optional[Tensor] = None,
        output_key_padding_mask: Optional[Tensor] = None,
        query_pos: Optional[Tensor] = None,
    ):
        if self.normalize_before:
            return self.forward_pre(output, output_mask, output_key_padding_mask, query_pos)

        return self.forward_post(output, output_mask, output_key_padding_mask, query_pos)


class Mask2FormerTransformerDecoderCrossAttentionLayer(nn.Module):
    def __init__(self, embed_dim, num_heads, dropout=0.0, activation="relu", normalize_before=False):
        super().__init__()
        self.multihead_attn = nn.MultiheadAttention(embed_dim, num_heads, dropout=dropout)

        self.norm = nn.LayerNorm(embed_dim)
        self.dropout = nn.Dropout(dropout)

        self.activation = ACT2FN[activation]
        self.normalize_before = normalize_before

        self._reset_parameters()

    def _reset_parameters(self):
        for p in self.parameters():
            if p.dim() > 1:
                nn.init.xavier_uniform_(p)

    def with_pos_embed(self, tensor, pos: Optional[Tensor]):
        return tensor if pos is None else tensor + pos

    def forward_post(
        self,
        output,
        memory,
        memory_mask: Optional[Tensor] = None,
        memory_key_padding_mask: Optional[Tensor] = None,
        pos: Optional[Tensor] = None,
        query_pos: Optional[Tensor] = None,
    ):
        output2, attention_weights = self.multihead_attn(
            query=self.with_pos_embed(output, query_pos),
            key=self.with_pos_embed(memory, pos),
            value=memory,
            attn_mask=memory_mask,
            key_padding_mask=memory_key_padding_mask,
        )
        output = output + self.dropout(output2)
        output = self.norm(output)

        return output, attention_weights

    def forward_pre(
        self,
        output,
        memory,
        memory_mask: Optional[Tensor] = None,
        memory_key_padding_mask: Optional[Tensor] = None,
        pos: Optional[Tensor] = None,
        query_pos: Optional[Tensor] = None,
    ):
        output2 = self.norm(output)
        output2, attention_weights = self.multihead_attn(
            query=self.with_pos_embed(output2, query_pos),
            key=self.with_pos_embed(memory, pos),
            value=memory,
            attn_mask=memory_mask,
            key_padding_mask=memory_key_padding_mask,
        )
        output = output + self.dropout(output2)

        return output, attention_weights

    def forward(
        self,
        output,
        memory,
        memory_mask: Optional[Tensor] = None,
        memory_key_padding_mask: Optional[Tensor] = None,
        pos: Optional[Tensor] = None,
        query_pos: Optional[Tensor] = None,
    ):
        if self.normalize_before:
            return self.forward_pre(output, memory, memory_mask, memory_key_padding_mask, pos, query_pos)
        return self.forward_post(output, memory, memory_mask, memory_key_padding_mask, pos, query_pos)


class Mask2FormerTransformerDecoderFFNLayer(nn.Module):
    def __init__(self, d_model, dim_feedforward=2048, dropout=0.0, activation="relu", normalize_before=False):
        super().__init__()
        # Implementation of Feedforward model
        self.linear1 = nn.Linear(d_model, dim_feedforward)
        self.dropout = nn.Dropout(dropout)
        self.linear2 = nn.Linear(dim_feedforward, d_model)

        self.norm = nn.LayerNorm(d_model)

        self.activation = ACT2FN[activation]
        self.normalize_before = normalize_before

        self._reset_parameters()

    def _reset_parameters(self):
        for p in self.parameters():
            if p.dim() > 1:
                nn.init.xavier_uniform_(p)

    def with_pos_embed(self, tensor, pos: Optional[Tensor]):
        return tensor if pos is None else tensor + pos

    def forward_post(self, output):
        output2 = self.linear2(self.dropout(self.activation(self.linear1(output))))
        output = output + self.dropout(output2)
        output = self.norm(output)
        return output

    def forward_pre(self, output):
        output2 = self.norm(output)
        output2 = self.linear2(self.dropout(self.activation(self.linear1(output2))))
        output = output + self.dropout(output2)
        return output

    def forward(self, output):
        if self.normalize_before:
            return self.forward_pre(output)
        return self.forward_post(output)


# Copied from transformers.models.maskformer.modeling_maskformer.MaskformerMLPPredictionHead with MaskFormer->Mask2Former
class Mask2FormerMLPPredictionHead(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int, output_dim: int, num_layers: int = 3):
        """
        A classic Multi Layer Perceptron (MLP).

        Args:
            input_dim (`int`):
                The input dimensions.
            hidden_dim (`int`):
                The hidden dimensions.
            output_dim (`int`):
                The output dimensions.
            num_layers (int, *optional*, defaults to 3):
                The number of layers.
        """
        super().__init__()
        in_dims = [input_dim] + [hidden_dim] * (num_layers - 1)
        out_dims = [hidden_dim] * (num_layers - 1) + [output_dim]

        self.layers = []
        for i, (in_dim, out_dim) in enumerate(zip(in_dims, out_dims)):
            activation = nn.ReLU() if i < num_layers - 1 else nn.Identity()
            layer = PredictionBlock(in_dim, out_dim, activation=activation)
            self.layers.append(layer)
            # Provide backwards compatibility from when the class inherited from nn.Sequential
            # In nn.Sequential subclasses, the name given to the layer is its index in the sequence.
            # In nn.Module subclasses they derived from the instance attribute they are assigned to e.g.
            # self.my_layer_name = Layer()
            # We can't give instance attributes integer names i.e. self.0 is not permitted and so need to register
            # explicitly
            self.add_module(str(i), layer)

    def forward(self, input: Tensor) -> Tensor:
        hidden_state = input
        for layer in self.layers:
            hidden_state = layer(hidden_state)
        return hidden_state


# refactored from original implementation
class Mask2FormerTransformerDecoderLayer(nn.Module):
    def __init__(self, config: Mask2FormerConfig):
        super().__init__()
        self.embed_dim = config.decoder_config["hidden_dim"]
        self.num_feature_levels = 3

        self.cross_attn = Mask2FormerTransformerDecoderCrossAttentionLayer(
            embed_dim=self.embed_dim,
            num_heads=config.decoder_config["num_heads"],
            dropout=0.0,
            normalize_before=config.decoder_config["pre_norm"],
        )

        self.self_attn = Mask2FormerTransformerDecoderSelfAttentionLayer(
            embed_dim=self.embed_dim,
            num_heads=config.decoder_config["num_heads"],
            dropout=0.0,
            normalize_before=config.decoder_config["pre_norm"],
        )

        self.ffn = Mask2FormerTransformerDecoderFFNLayer(
            d_model=self.embed_dim,
            dim_feedforward=config.decoder_config["dim_feedforward"],
            dropout=0.0,
            normalize_before=config.decoder_config["pre_norm"],
        )

    def forward(
        self,
        index: int,
        output: torch.Tensor,
        multi_stage_features: List[torch.Tensor],
        multi_stage_positional_embeddings: List[torch.Tensor],
        attention_mask: Optional[torch.Tensor] = None,
        query_embeddings: Optional[torch.Tensor] = None,
        output_attentions: Optional[bool] = False,
    ):
        """
        Args:
            index (`int`): index of the layer in the Transformer decoder.
            output (`torch.FloatTensor`): the object queries of shape `(N, batch, hidden_dim)`
            multi_stage_features (`List[torch.Tensor]`): the multi-scale features from the pixel decoder.
            multi_stage_positional_embeddings (`List[torch.Tensor]`):
                positional embeddings for the multi_stage_features
            attention_mask (`torch.FloatTensor`): attention mask for the masked cross attention layer
            query_embeddings (`torch.FloatTensor`, *optional*):
                position embeddings that are added to the queries and keys in the self-attention layer.
            output_attentions (`bool`, *optional*):
                Whether or not to return the attentions tensors of all attention layers. See `attentions` under
                returned tensors for more detail.
        """

        level_index = index % self.num_feature_levels
        attention_mask[torch.where(attention_mask.sum(-1) == attention_mask.shape[-1])] = False

        # Masked Cross Attention
        output, cross_attn_weights = self.cross_attn(
            output,
            multi_stage_features[level_index],
            memory_mask=attention_mask,
            memory_key_padding_mask=None,  # here we do not apply masking on padded region
            pos=multi_stage_positional_embeddings[level_index],
            query_pos=query_embeddings,
        )

        # Self Attention
        output, self_attn_weights = self.self_attn(
            output,
            output_mask=None,
            output_key_padding_mask=None,
            query_pos=query_embeddings,
        )

        # Fully Connected
        output = self.ffn(output)

        outputs = (output,)

        if output_attentions:
            outputs += (self_attn_weights, cross_attn_weights)

        return outputs


class Mask2FormerTransformerDecoder(nn.Module):
    """
    Transformer decoder
    """

    def __init__(self, in_channels: int, config: Mask2FormerConfig):
        super().__init__()
        self.config = config
        self.num_heads = config.decoder_config["num_heads"]
        self.is_train = config.general_config["is_train"]
        self.use_auxiliary_loss = config.general_config["use_auxiliary_loss"]

        self.decoder_norm = nn.LayerNorm(config.decoder_config["hidden_dim"])
        self.num_feature_levels = 3

        self.layers = nn.ModuleList(
            [Mask2FormerTransformerDecoderLayer(config) for _ in range(config.decoder_config["decoder_layers"] - 1)]
        )

        self.class_embed = nn.Linear(config.decoder_config["hidden_dim"], config.general_config["num_classes"] + 1)
        self.mask_embed = Mask2FormerMLPPredictionHead(
            config.decoder_config["hidden_dim"],
            config.decoder_config["hidden_dim"],
            config.decoder_config["mask_dim"],
            3,
        )

    def forward(
        self,
        multi_stage_features=None,
        multi_stage_positional_embeddings=None,
        mask_features=None,
        query_features=None,
        query_features_weight=None,
        query_embeddings=None,
        size_list=None,
        output_attentions=None,
    ):

        intermediate_class_predictions = []
        intermediate_mask_predictions = []

        # Prediction heads on learnable query features
        outputs_class, outputs_mask, attention_mask = self.forward_prediction_heads(
            query_features_weight, mask_features, attention_mask_target_size=size_list[0]
        )
        intermediate_class_predictions.append(outputs_class)
        intermediate_mask_predictions.append(outputs_mask)

        attentions = ()

        for index, layer in enumerate(self.layers):
            layer_outputs = layer(
                index=index,
                output=query_features_weight,
                multi_stage_features=multi_stage_features,
                multi_stage_positional_embeddings=multi_stage_positional_embeddings,
                attention_mask=attention_mask,
                query_embeddings=query_embeddings,
                output_attentions=output_attentions,
            )

            output = layer_outputs[0]
            attentions += (layer_outputs[1:],)

            outputs_class, outputs_mask, attention_mask = self.forward_prediction_heads(
                output, mask_features, attention_mask_target_size=size_list[(index + 1) % self.num_feature_levels]
            )
            intermediate_class_predictions.append(outputs_class)
            intermediate_mask_predictions.append(outputs_mask)

        object_queries = layer_outputs[0].permute(1, 0, 2)

        return Mask2FormerTransformerDecoderOutput(
            object_queries=object_queries,
            prediction_masks=intermediate_mask_predictions[-1],
            prediction_class=intermediate_class_predictions[-1],
            auxiliary_predictions=self._get_aux_predictions(
                intermediate_class_predictions, intermediate_mask_predictions
            )
            if self.use_auxiliary_loss
            else None,
            attentions=attentions,
        )

    def forward_prediction_heads(self, output, mask_features, attention_mask_target_size):
        decoder_output = self.decoder_norm(output)
        decoder_output = decoder_output.transpose(0, 1)
        outputs_class = self.class_embed(decoder_output)
        mask_embed = self.mask_embed(decoder_output)
        outputs_mask = torch.einsum("bqc,bchw->bqhw", mask_embed, mask_features)

        # NOTE: prediction is of higher-resolution
        # [B, Q, H, W] -> [B, Q, H*W] -> [B, h, Q, H*W] -> [B*h, Q, HW]
        attention_mask = F.interpolate(
            outputs_mask, size=attention_mask_target_size, mode="bilinear", align_corners=False
        )

        # If a BoolTensor is provided, positions with ``True`` are not allowed to attend while ``False`` values will be unchanged.
        attention_mask = attention_mask.sigmoid().flatten(2).unsqueeze(1)
        attention_mask = (attention_mask.repeat(1, self.num_heads, 1, 1).flatten(0, 1) < 0.5).bool()
        attention_mask = attention_mask.detach()

        return outputs_class, outputs_mask, attention_mask

    @torch.jit.unused
    def _get_aux_predictions(self, outputs_class, outputs_seg_masks):
        aux_list = [
            {"class_queries_logits": a, "masks_queries_logits": b}
            for a, b in zip(outputs_class[:-1], outputs_seg_masks[:-1])
        ]
        return tuple(aux_list)


class Mask2FormerTransformerModule(nn.Module):
    """
    The Mask2Former's transformer module.
    """

    def __init__(self, in_features: int, config: Mask2FormerConfig):
        super().__init__()
        hidden_dim = config.decoder_config["hidden_dim"]
        self.num_feature_levels = 3
        self.position_embedder = Mask2FormerSinePositionEmbedding(num_pos_feats=hidden_dim // 2, normalize=True)
        self.queries_embedder = nn.Embedding(config.general_config["num_queries"], hidden_dim)
        self.queries_features = nn.Embedding(config.general_config["num_queries"], hidden_dim)
        self.input_projections = []

        for _ in range(self.num_feature_levels):
            if in_features != hidden_dim or config.decoder_config["enforce_input_proj"]:
                self.input_projections.append(nn.Conv2d(in_features, hidden_dim, kernel_size=1))
            else:
                self.input_projections.append(nn.Sequential())

        self.decoder = Mask2FormerTransformerDecoder(in_channels=in_features, config=config)
        self.level_embed = nn.Embedding(self.num_feature_levels, hidden_dim)

    def forward(
        self,
        multi_scale_features: List[Tensor],
        mask_features: Tensor,
        output_attentions: bool = False,
    ) -> Mask2FormerTransformerDecoderOutput:

        multi_stage_features = []
        multi_stage_positional_embeddings = []
        size_list = []

        for i in range(self.num_feature_levels):
            size_list.append(multi_scale_features[i].shape[-2:])
            multi_stage_positional_embeddings.append(self.position_embedder(multi_scale_features[i], None).flatten(2))
            multi_stage_features.append(
                self.input_projections[i](multi_scale_features[i]).flatten(2)
                + self.level_embed.weight[i][None, :, None]
            )

            # Flatten (batch_size, num_channels, height, width) -> (height*width, batch_size, num_channels)
            multi_stage_positional_embeddings[-1] = multi_stage_positional_embeddings[-1].permute(2, 0, 1)
            multi_stage_features[-1] = multi_stage_features[-1].permute(2, 0, 1)

        _, batch_size, _ = multi_stage_features[0].shape

        # QxNxC
        query_embeddings = self.queries_embedder.weight.unsqueeze(1).repeat(1, batch_size, 1)
        query_features_weight = self.query_features.weight.unsqueeze(1).repeat(1, batch_size, 1)
        query_features = self.position_embedder(mask_features, None)

        decoder_output: Mask2FormerTransformerDecoderOutput = self.decoder(
            multi_stage_features=multi_stage_features,
            multi_stage_positional_embeddings=multi_stage_positional_embeddings,
            mask_features=mask_features,
            query_features=query_features,
            query_features_weight=query_features_weight,
            query_embeddings=query_embeddings,
            size_list=size_list,
            output_attentions=output_attentions,
        )
        return decoder_output


@add_start_docstrings(
    "The bare Mask2Former Model outputting raw hidden-states without any specific head on top.",
    MASK2FORMER_START_DOCSTRING,
)
class Mask2FormerModel(Mask2FormerPreTrainedModel):
    main_input_name = ["pixel_values"]

    def __init__(self, config: Mask2FormerConfig):
        super().__init__(config)
        self.pixel_level_module = Mask2FormerPixelLevelModule(config)
        self.transformer_module = Mask2FormerTransformerModule(
            in_features=config.decoder_config["feature_size"], config=config
        )
        self.is_train = config.general_config["is_train"]

        self.post_init()

    @add_start_docstrings_to_model_forward(MASK2FORMER_INPUTS_DOCSTRING)
    @replace_return_docstrings(output_type=Mask2FormerModelOutput, config_class=_CONFIG_FOR_DOC)
    def forward(
        self,
        pixel_values: Tensor,
        pixel_mask: Optional[Tensor] = None,
        output_hidden_states: Optional[bool] = None,
        output_attentions: Optional[bool] = None,
        return_dict: Optional[bool] = None,
    ) -> Mask2FormerModelOutput:
        r"""
        Returns:
            `Mask2FormerModelOutput`

        Examples:
        ```python
        >>> import torch
        >>> from PIL import Image
        >>> import requests
        >>> from transformers import Mask2FormerImageProcessor, Mask2FormerModel

        >>> # download texting image
        >>> url = "http://images.cocodataset.org/val2017/000000039769.jpg"
        >>> image = Image.open(requests.get(url, stream=True).raw)

        >>> # load feature extractor for preprocessing the inputs
        >>> image_processor = Mask2FormerImageProcessor.from_pretrained("FILL")
        >>> model = Mask2FormerModel.from_pretrained("FILL")
        >>> inputs = image_processor(image, return_tensors="pt")

        >>> with torch.no_grad():
        ...     outputs = model(**inputs)

        >>> mask_predictions = outputs.transformer_decoder_mask_predictions
        >>> class_predictions = outputs.transformer_decoder_class_predictions
        ```
        """

        if pixel_values is None:
            raise ValueError("You have to specify pixel_values")

        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )
        return_dict = return_dict if return_dict is not None else self.config.use_return_dict

        batch_size, _, height, width = pixel_values.shape

        if pixel_mask is None:
            pixel_mask = torch.ones((batch_size, height, width), device=pixel_values.device)

        pixel_level_module_output = self.pixel_level_module(pixel_values, output_hidden_states)

        multi_scale_features = pixel_level_module_output.decoder_hidden_states
        mask_features = pixel_level_module_output.decoder_last_hidden_state

        transformer_module_output = self.transformer_module(
            multi_scale_features=multi_scale_features,
            mask_features=mask_features,
            output_attentions=output_attentions,
        )

        queries = transformer_module_output.object_queries

        encoder_hidden_states = None
        pixel_decoder_hidden_states = None
        transformer_decoder_hidden_states = None

        if output_hidden_states:
            encoder_hidden_states = pixel_level_module_output.encoder_hidden_states
            pixel_decoder_hidden_states = pixel_level_module_output.decoder_hidden_states
            transformer_decoder_hidden_states = transformer_module_output.auxiliary_predictions

        output = Mask2FormerModelOutput(
            encoder_hidden_states=encoder_hidden_states,
            pixel_decoder_hidden_states=pixel_decoder_hidden_states,
            transformer_decoder_hidden_states=transformer_decoder_hidden_states,
            transformer_decoder_object_queries=queries,
            masks_queries_logits=transformer_module_output.prediction_masks,
            class_queries_logits=transformer_module_output.prediction_class,
            transformer_decoder_auxiliary_predictions=transformer_module_output.auxiliary_predictions,
            attentions=transformer_module_output.attentions,
        )

        if not return_dict:
            output = tuple(v for v in output.values())

        return output


class Mask2FormerForInstanceSegmentation(Mask2FormerPreTrainedModel):
    main_input_name = ["pixel_values"]

    def __init__(self, config: Mask2FormerConfig):
        super().__init__(config)
        self.model = Mask2FormerModel(config)

        self.matcher = Mask2FormerHungarianMatcher(
            cost_class=config.general_config["class_weight"],
            cost_dice=config.general_config["dice_weight"],
            cost_mask=config.general_config["mask_weight"],
            num_points=config.general_config["train_num_points"],
        )

        self.weight_dict: Dict[str, float] = {
            "loss_cross_entropy": config.general_config["class_weight"],
            "loss_mask": config.general_config["mask_weight"],
            "loss_dice": config.general_config["dice_weight"],
        }

        self.criterion = Mask2FormerLoss(
            num_classes=config.general_config["num_classes"],
            matcher=self.matcher,
            weight_dict=self.weight_dict,
            eos_coef=config.general_config["no_object_weight"],
            num_points=config.general_config["train_num_points"],
            oversample_ratio=config.general_config["oversample_ratio"],
            importance_sample_ratio=config.general_config["importance_sample_ratio"],
        )

        self.post_init()

    def get_loss_dict(
        self,
        masks_queries_logits: Tensor,
        class_queries_logits: Tensor,
        mask_labels: Tensor,
        class_labels: Tensor,
        text_queries: Tensor,
        auxiliary_predictions: Dict[str, Tensor],
    ) -> Dict[str, Tensor]:
        loss_dict: Dict[str, Tensor] = self.criterion(
            masks_queries_logits=masks_queries_logits,
            class_queries_logits=class_queries_logits,
            mask_labels=mask_labels,
            class_labels=class_labels,
            text_queries=text_queries,
            auxiliary_predictions=auxiliary_predictions,
        )

        # weight each loss by `self.weight_dict[<LOSS_NAME>]` including auxiliary losses
        for key, weight in self.weight_dict.items():
            for loss_key, loss in loss_dict.items():
                if key in loss_key:
                    loss *= weight

        return loss_dict

    def get_loss(self, loss_dict: Dict[str, Tensor]) -> Tensor:
        return sum(loss_dict.values())

    @add_start_docstrings_to_model_forward(MASK2FORMER_INPUTS_DOCSTRING)
    @replace_return_docstrings(output_type=Mask2FormerForInstanceSegmentationOutput, config_class=_CONFIG_FOR_DOC)
    def forward(
        self,
        pixel_values: Tensor,
        mask_labels: Optional[List[Tensor]] = None,
        class_labels: Optional[List[Tensor]] = None,
        pixel_mask: Optional[Tensor] = None,
        output_auxiliary_logits: Optional[bool] = None,
        output_hidden_states: Optional[bool] = None,
        output_attentions: Optional[bool] = None,
        return_dict: Optional[bool] = None,
    ) -> Mask2FormerForInstanceSegmentationOutput:
        r"""
        mask_labels (`List[torch.Tensor]`, *optional*):
            List of mask labels of shape `(num_labels, height, width)` to be fed to a model
        class_labels (`List[torch.LongTensor]`, *optional*):
            list of target class labels of shape `(num_labels, height, width)` to be fed to a model. They identify the
            labels of `mask_labels`, e.g. the label of `mask_labels[i][j]` if `class_labels[i][j]`.

        Returns:
            `Mask2FormerInstanceSegmentationOutput`

        Examples:
        ```python
        >>> from transformers import Mask2FormerImageProcessor, Mask2FormerForInstanceSegmentation
        >>> from PIL import Image
        >>> import requests
        >>> import torch

        >>> # Load Mask2Former trained on ADE20k
        >>> image_processor = Mask2FormerImageProcessor.from_pretrained("FILL")
        >>> model = Mask2FormerForInstanceSegmentation.from_pretrained("FILL")

        >>> url = (
        ...     "https://huggingface.co/datasets/hf-internal-testing/fixtures_ade20k/resolve/main/ADE_val_00000001.jpg"
        ... )
        >>> image = Image.open(requests.get(url, stream=True).raw)
        >>> inputs = image_processor(image, return_tensors="pt")

        >>> with torch.no_grad():
        ...     outputs = model(**inputs)

        >>> # Model predicts class_queries_logits of shape `(batch_size, num_queries)`
        >>> # and masks_queries_logits of shape `(batch_size, num_queries, height, width)`
        >>> class_queries_logits = outputs.class_queries_logits
        >>> masks_queries_logits = outputs.masks_queries_logits

        >>> # Perform post-processing to get panoptic segmentation maps
        >>> predicted_panoptic_map = feature_extractor.post_process_panoptic_segmentation(
        ...     outputs, target_sizes=[image.size[::-1]]
        ... )[0]["segmentation"]
        ```
        """

        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )
        return_dict = return_dict if return_dict is not None else self.config.use_return_dict

        outputs: Mask2FormerModelOutput = self.model(
            pixel_values=pixel_values,
            pixel_mask=pixel_mask,
            output_hidden_states=output_hidden_states or self.config.general_config["use_auxiliary_loss"],
            output_attentions=output_attentions,
            return_dict=True,
        )

        loss, loss_dict, auxiliary_predictions = None, None, None

        class_queries_logits = outputs.transformer_decoder_class_predictions
        masks_queries_logits = outputs.transformer_decoder_mask_predictions
        auxiliary_predictions = outputs.transformer_decoder_auxiliary_predictions

        if mask_labels is not None and class_labels is not None:
            loss_dict: Dict[str, Tensor] = self.get_loss_dict(
                masks_queries_logits=masks_queries_logits,
                class_queries_logits=class_queries_logits,
                mask_labels=mask_labels,
                class_labels=class_labels,
                auxiliary_predictions=auxiliary_predictions,
            )
            loss = self.get_loss(loss_dict)

        output_auxiliary_logits = (
            self.config.general_config["output_auxiliary_logits"]
            if output_auxiliary_logits is None
            else output_auxiliary_logits
        )
        if not output_auxiliary_logits:
            auxiliary_predictions = None

        output = Mask2FormerForInstanceSegmentationOutput(
            class_queries_logits=class_queries_logits,
            masks_queries_logits=masks_queries_logits,
            auxiliary_predictions=auxiliary_predictions,
            loss=loss,
            **outputs,
        )

        if not return_dict:
            output = tuple(v for v in output.values())
            if loss is not None:
                output = ((loss)) + output
        return output
