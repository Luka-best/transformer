# coding=utf-8
# Copyright 2024 The HuggingFace Inc. team.
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
"""Convert DAB-DETR checkpoints."""


import argparse
import json
from collections import OrderedDict
from pathlib import Path

import requests
import torch
from huggingface_hub import hf_hub_download
from PIL import Image
from transformers import (
    DABDETRConfig,
    DABDETRForObjectDetection,
    DABDETRForSegmentation,
    DABDETRImageProcessor,
)
from transformers.utils import logging


logging.set_verbosity_info()
logger = logging.get_logger(__name__)

# here we list all keys to be renamed (original name on the left, HF name on the right)
rename_keys = []
for i in range(6):
    # encoder layers: output projection, 2 feedforward neural networks and 2 layernorms + activation function
    # input projection
    rename_keys.append(
        (f"transformer.encoder.layers.{i}.self_attn.in_proj_weight", f"encoder.layers.{i}.self_attn.in_proj_weight")
    )
    rename_keys.append(
        (f"transformer.encoder.layers.{i}.self_attn.in_proj_bias", f"encoder.layers.{i}.self_attn.in_proj_bias")
    )
    # output projection
    rename_keys.append(
        (f"transformer.encoder.layers.{i}.self_attn.out_proj.weight", f"encoder.layers.{i}.self_attn.out_proj.weight")
    )
    rename_keys.append(
        (f"transformer.encoder.layers.{i}.self_attn.out_proj.bias", f"encoder.layers.{i}.self_attn.out_proj.bias")
    )
    # FFN layer
    # FFN 1
    rename_keys.append((f"transformer.encoder.layers.{i}.linear1.weight", f"encoder.layers.{i}.fc1.weight"))
    rename_keys.append((f"transformer.encoder.layers.{i}.linear1.bias", f"encoder.layers.{i}.fc1.bias"))
    # FFN 2
    rename_keys.append((f"transformer.encoder.layers.{i}.linear2.weight", f"encoder.layers.{i}.fc2.weight"))
    rename_keys.append((f"transformer.encoder.layers.{i}.linear2.bias", f"encoder.layers.{i}.fc2.bias"))
    # normalization layers
    # nm1
    rename_keys.append(
        (f"transformer.encoder.layers.{i}.norm1.weight", f"encoder.layers.{i}.self_attn_layer_norm.weight")
    )
    rename_keys.append((f"transformer.encoder.layers.{i}.norm1.bias", f"encoder.layers.{i}.self_attn_layer_norm.bias"))
    # nm2
    rename_keys.append((f"transformer.encoder.layers.{i}.norm2.weight", f"encoder.layers.{i}.final_layer_norm.weight"))
    rename_keys.append((f"transformer.encoder.layers.{i}.norm2.bias", f"encoder.layers.{i}.final_layer_norm.bias"))
    # activation function weight
    rename_keys.append((f"transformer.encoder.layers.{i}.activation.weight", f"encoder.layers.{i}.activation_fn.weight"))
    #########################################################################################################################################
    # decoder layers: 2 times output projection, 2 feedforward neural networks and 3 layernorms + activiation function weight
    rename_keys.append(
        (f"transformer.decoder.layers.{i}.self_attn.out_proj.weight", f"decoder.layers.{i}.self_attn.out_proj.weight")
    )
    rename_keys.append(
        (f"transformer.decoder.layers.{i}.self_attn.out_proj.bias", f"decoder.layers.{i}.self_attn.out_proj.bias")
    )
    rename_keys.append(
        (
            f"transformer.decoder.layers.{i}.cross_attn.out_proj.weight",
            f"decoder.layers.{i}.cross_attn.out_proj.weight",
        )
    )
    # activation function weight
    rename_keys.append((f"transformer.decoder.layers.{i}.activation.weight", f"decoder.layers.{i}.activation_fn.weight"))
    rename_keys.append(
        (
            f"transformer.decoder.layers.{i}.cross_attn.out_proj.bias",
            f"decoder.layers.{i}.cross_attn.out_proj.bias",
        )
    )
    rename_keys.append((f"transformer.decoder.layers.{i}.linear1.weight", f"decoder.layers.{i}.fc1.weight"))
    rename_keys.append((f"transformer.decoder.layers.{i}.linear1.bias", f"decoder.layers.{i}.fc1.bias"))
    rename_keys.append((f"transformer.decoder.layers.{i}.linear2.weight", f"decoder.layers.{i}.fc2.weight"))
    rename_keys.append((f"transformer.decoder.layers.{i}.linear2.bias", f"decoder.layers.{i}.fc2.bias"))
    rename_keys.append(
        (f"transformer.decoder.layers.{i}.norm1.weight", f"decoder.layers.{i}.self_attn_layer_norm.weight")
    )
    rename_keys.append((f"transformer.decoder.layers.{i}.norm1.bias", f"decoder.layers.{i}.self_attn_layer_norm.bias"))
    rename_keys.append(
        (f"transformer.decoder.layers.{i}.norm2.weight", f"decoder.layers.{i}.cross_attn_layer_norm.weight")
    )
    rename_keys.append(
        (f"transformer.decoder.layers.{i}.norm2.bias", f"decoder.layers.{i}.cross_attn_layer_norm.bias")
    )
    rename_keys.append((f"transformer.decoder.layers.{i}.norm3.weight", f"decoder.layers.{i}.final_layer_norm.weight"))
    rename_keys.append((f"transformer.decoder.layers.{i}.norm3.bias", f"decoder.layers.{i}.final_layer_norm.bias"))

    # q, k, v projections in self/cross-attention in decoder for DAB-DETR
    rename_keys.append(
        (f"transformer.decoder.layers.{i}.sa_qcontent_proj.weight", f"decoder.layers.{i}.sa_qcontent_proj.weight")
    )
    rename_keys.append(
        (f"transformer.decoder.layers.{i}.sa_kcontent_proj.weight", f"decoder.layers.{i}.sa_kcontent_proj.weight")
    )
    rename_keys.append(
        (f"transformer.decoder.layers.{i}.sa_qpos_proj.weight", f"decoder.layers.{i}.sa_qpos_proj.weight")
    )
    rename_keys.append(
        (f"transformer.decoder.layers.{i}.sa_kpos_proj.weight", f"decoder.layers.{i}.sa_kpos_proj.weight")
    )
    rename_keys.append((f"transformer.decoder.layers.{i}.sa_v_proj.weight", f"decoder.layers.{i}.sa_v_proj.weight"))
    rename_keys.append(
        (f"transformer.decoder.layers.{i}.ca_qcontent_proj.weight", f"decoder.layers.{i}.ca_qcontent_proj.weight")
    )
    rename_keys.append(
        (f"transformer.decoder.layers.{i}.ca_kcontent_proj.weight", f"decoder.layers.{i}.ca_kcontent_proj.weight")
    )
    rename_keys.append(
        (f"transformer.decoder.layers.{i}.ca_kpos_proj.weight", f"decoder.layers.{i}.ca_kpos_proj.weight")
    )
    rename_keys.append((f"transformer.decoder.layers.{i}.ca_v_proj.weight", f"decoder.layers.{i}.ca_v_proj.weight"))
    rename_keys.append(
        (f"transformer.decoder.layers.{i}.ca_qpos_sine_proj.weight", f"decoder.layers.{i}.ca_qpos_sine_proj.weight")
    )

    rename_keys.append(
        (f"transformer.decoder.layers.{i}.sa_qcontent_proj.bias", f"decoder.layers.{i}.sa_qcontent_proj.bias")
    )
    rename_keys.append(
        (f"transformer.decoder.layers.{i}.sa_kcontent_proj.bias", f"decoder.layers.{i}.sa_kcontent_proj.bias")
    )
    rename_keys.append((f"transformer.decoder.layers.{i}.sa_qpos_proj.bias", f"decoder.layers.{i}.sa_qpos_proj.bias"))
    rename_keys.append((f"transformer.decoder.layers.{i}.sa_kpos_proj.bias", f"decoder.layers.{i}.sa_kpos_proj.bias"))
    rename_keys.append((f"transformer.decoder.layers.{i}.sa_v_proj.bias", f"decoder.layers.{i}.sa_v_proj.bias"))
    rename_keys.append(
        (f"transformer.decoder.layers.{i}.ca_qcontent_proj.bias", f"decoder.layers.{i}.ca_qcontent_proj.bias")
    )
    rename_keys.append(
        (f"transformer.decoder.layers.{i}.ca_kcontent_proj.bias", f"decoder.layers.{i}.ca_kcontent_proj.bias")
    )
    rename_keys.append((f"transformer.decoder.layers.{i}.ca_kpos_proj.bias", f"decoder.layers.{i}.ca_kpos_proj.bias"))
    rename_keys.append((f"transformer.decoder.layers.{i}.ca_v_proj.bias", f"decoder.layers.{i}.ca_v_proj.bias"))
    rename_keys.append(
        (f"transformer.decoder.layers.{i}.ca_qpos_sine_proj.bias", f"decoder.layers.{i}.ca_qpos_sine_proj.bias")
    )

# convolutional projection + query embeddings + layernorm of decoder + class and bounding box heads
# for conditional DETR, also convert reference point head and query scale MLP
rename_keys.extend(
    [
        ("input_proj.weight", "input_projection.weight"),
        ("input_proj.bias", "input_projection.bias"),

        ("refpoint_embed.weight", "query_refpoint_embeddings.weight"),

        ("class_embed.weight", "class_labels_classifier.weight"),
        ("class_embed.bias", "class_labels_classifier.bias"),

        ("transformer.encoder.query_scale.layers.0.weight", "encoder.query_scale.layers.0.weight"),
        ("transformer.encoder.query_scale.layers.0.bias", "encoder.query_scale.layers.0.bias"),
        ("transformer.encoder.query_scale.layers.1.weight", "encoder.query_scale.layers.1.weight"),
        ("transformer.encoder.query_scale.layers.1.bias", "encoder.query_scale.layers.1.bias"),
        
        ("transformer.decoder.bbox_embed.layers.0.weight", "decoder.bbox_embed.layers.0.weight"),
        ("transformer.decoder.bbox_embed.layers.0.bias", "decoder.bbox_embed.layers.0.bias"),
        ("transformer.decoder.bbox_embed.layers.1.weight", "decoder.bbox_embed.layers.1.weight"),
        ("transformer.decoder.bbox_embed.layers.1.bias", "decoder.bbox_embed.layers.1.bias"),
        ("transformer.decoder.bbox_embed.layers.2.weight", "decoder.bbox_embed.layers.2.weight"),
        ("transformer.decoder.bbox_embed.layers.2.bias", "decoder.bbox_embed.layers.2.bias"),

        ("transformer.decoder.norm.weight", "decoder.layernorm.weight"),
        ("transformer.decoder.norm.bias", "decoder.layernorm.bias"),

        ("transformer.decoder.ref_point_head.layers.0.weight", "decoder.ref_point_head.layers.0.weight"),
        ("transformer.decoder.ref_point_head.layers.0.bias", "decoder.ref_point_head.layers.0.bias"),
        ("transformer.decoder.ref_point_head.layers.1.weight", "decoder.ref_point_head.layers.1.weight"),
        ("transformer.decoder.ref_point_head.layers.1.bias", "decoder.ref_point_head.layers.1.bias"),

        ("transformer.decoder.ref_anchor_head.layers.0.weight", "decoder.ref_anchor_head.layers.0.weight"),
        ("transformer.decoder.ref_anchor_head.layers.0.bias", "decoder.ref_anchor_head.layers.0.bias"),
        ("transformer.decoder.ref_anchor_head.layers.1.weight", "decoder.ref_anchor_head.layers.1.weight"),
        ("transformer.decoder.ref_anchor_head.layers.1.bias", "decoder.ref_anchor_head.layers.1.bias"),

        ("transformer.decoder.query_scale.layers.0.weight", "decoder.query_scale.layers.0.weight"),
        ("transformer.decoder.query_scale.layers.0.bias", "decoder.query_scale.layers.0.bias"),
        ("transformer.decoder.query_scale.layers.1.weight", "decoder.query_scale.layers.1.weight"),
        ("transformer.decoder.query_scale.layers.1.bias", "decoder.query_scale.layers.1.bias"),

        ("transformer.decoder.layers.0.ca_qpos_proj.weight", "decoder.layers.0.ca_qpos_proj.weight"),
        ("transformer.decoder.layers.0.ca_qpos_proj.bias", "decoder.layers.0.ca_qpos_proj.bias"),
    ]
)


def rename_key(state_dict, old, new):
    val = state_dict.pop(old)
    state_dict[new] = val


def rename_backbone_keys(state_dict):
    new_state_dict = OrderedDict()
    for key, value in state_dict.items():
        if "backbone.0.body" in key:
            new_key = key.replace("backbone.0.body", "backbone.conv_encoder.model")
            new_state_dict[new_key] = value
        else:
            new_state_dict[key] = value

    return new_state_dict


# We will verify our results on an image of cute cats
def prepare_img():
    url = "http://images.cocodataset.org/val2017/000000039769.jpg"
    im = Image.open(requests.get(url, stream=True).raw)

    return im


@torch.no_grad()
def convert_dab_detr_checkpoint(model_name, pytorch_dump_folder_path):
    """
    Copy/paste/tweak model's weights to our DAB-DETR structure.
    """

    # load default config
    config = DABDETRConfig()
    # set backbone and dilation attributes
    if "resnet101" in model_name:
        config.backbone = "resnet101"
    if "dc5" in model_name:
        config.dilation = True
    is_panoptic = "panoptic" in model_name
    if is_panoptic:
        config.num_labels = 250
    else:
        config.num_labels = 91
        repo_id = "huggingface/label-files"
        filename = "coco-detection-id2label.json"
        id2label = json.load(open(hf_hub_download(repo_id, filename, repo_type="dataset"), "r"))
        id2label = {int(k): v for k, v in id2label.items()}
        config.id2label = id2label
        config.label2id = {v: k for k, v in id2label.items()}

    # load image processor
    format = "coco_panoptic" if is_panoptic else "coco_detection"
    image_processor = DABDETRImageProcessor(format=format)

    # prepare image
    img = prepare_img()
    encoding = image_processor(images=[img, img], return_tensors="pt")

    logger.info(f"Converting model {model_name}...")

    # load original model from torch hub
    state_dict = torch.load("/Users/davidhajdu/Desktop/dab_detr_r50.pth", map_location=torch.device('cpu'))['model']
    # rename keys
    for src, dest in rename_keys:
        if is_panoptic:
            src = "dab_detr." + src
        rename_key(state_dict, src, dest)
    state_dict = rename_backbone_keys(state_dict)
    # important: we need to prepend a prefix to each of the base model keys as the head models use different attributes for them
    prefix = "dab_detr.model." if is_panoptic else "model."
    for key in state_dict.copy().keys():
        if is_panoptic:
            if (
                key.startswith("dab_detr")
                and not key.startswith("class_labels_classifier")
                and not key.startswith("bbox_predictor")
            ):
                val = state_dict.pop(key)
                state_dict["dab_detr.model" + key[4:]] = val
            elif "class_labels_classifier" in key or "bbox_predictor" in key:
                val = state_dict.pop(key)
                state_dict["dab_detr." + key] = val
            elif key.startswith("bbox_attention") or key.startswith("mask_head"):
                continue
            else:
                val = state_dict.pop(key)
                state_dict[prefix + key] = val
        else:
            if not key.startswith("class_labels_classifier") and not key.startswith("bbox_predictor"):
                val = state_dict.pop(key)
                state_dict[prefix + key] = val

    expected_slice_logits = torch.tensor(
            [[-10.1765,  -5.5243,  -8.9324], [ -9.8138,  -5.6721,  -7.5161], [-10.3054,  -5.6081,  -8.5931]]
        )
    expected_slice_boxes = torch.tensor(
            [[0.3708, 0.3000, 0.2753], [0.5211, 0.6125, 0.9495], [0.2897, 0.6730, 0.5459]]
        )
    # finally, create HuggingFace model and load state dict
    model = DABDETRForSegmentation(config) if is_panoptic else DABDETRForObjectDetection(config)
    model.load_state_dict(state_dict)
    model.eval()
    # verify our conversion
    outputs = model(**encoding)
    assert torch.allclose(outputs.logits[0, :3, :3], expected_slice_logits, atol=3e-4)
    assert torch.allclose(outputs.pred_boxes[0, :3, :3], expected_slice_boxes, atol=1e-4)

    # Save model and image processor
    logger.info(f"Saving PyTorch model and image processor to {pytorch_dump_folder_path}...")
    Path(pytorch_dump_folder_path).mkdir(exist_ok=True)
    model.save_pretrained(pytorch_dump_folder_path, safe_serialization=False)
    image_processor.save_pretrained(pytorch_dump_folder_path)
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--model_name",
        default="dab_detr_resnet50",
        type=str,
        help="Name of the DAB_DETR model you'd like to convert.",
    )
    parser.add_argument(
        "--pytorch_dump_folder_path", default='DAB_DETR', type=str, help="Path to the folder to output PyTorch model."
    )
    args = parser.parse_args()
    convert_dab_detr_checkpoint(args.model_name, args.pytorch_dump_folder_path)
