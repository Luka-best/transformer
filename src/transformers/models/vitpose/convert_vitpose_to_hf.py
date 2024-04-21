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
"""Convert ViTPose checkpoints from the original repository.

URL: https://github.com/vitae-transformer/vitpose
"""


import argparse
from pathlib import Path

import numpy as np
import requests
import torch
from huggingface_hub import hf_hub_download
from PIL import Image

from transformers import ViTPoseConfig, ViTPoseForPoseEstimation, ViTPoseImageProcessor


def _xywh2xyxy(bbox_xywh):
    """Transform the bbox format from xywh to x1y1x2y2.

    Args:
        bbox_xywh (ndarray): Bounding boxes (with scores),
            shaped (n, 4) or (n, 5). (left, top, width, height, [score])
    Returns:
        np.ndarray: Bounding boxes (with scores), shaped (n, 4) or
          (n, 5). (left, top, right, bottom, [score])
    """
    bbox_xyxy = bbox_xywh.copy()
    bbox_xyxy[:, 2] = bbox_xyxy[:, 2] + bbox_xyxy[:, 0] - 1
    bbox_xyxy[:, 3] = bbox_xyxy[:, 3] + bbox_xyxy[:, 1] - 1

    return bbox_xyxy


def get_config(model_name):
    use_simple_decoder = "simple" in model_name
    config = ViTPoseConfig(num_labels=17, use_simple_decoder=use_simple_decoder)
    # size of the architecture
    if "small" in model_name:
        config.hidden_size = 768
        config.intermediate_size = 2304
        config.num_hidden_layers = 8
        config.num_attention_heads = 8
    elif "large" in model_name:
        config.hidden_size = 1024
        config.intermediate_size = 4096
        config.num_hidden_layers = 24
        config.num_attention_heads = 16
    elif "huge" in model_name:
        config.hidden_size = 1280
        config.intermediate_size = 5120
        config.num_hidden_layers = 32
        config.num_attention_heads = 16

    return config


def rename_key(name, config):
    if "backbone" in name:
        name = name.replace("backbone", "vit")
    if "patch_embed.proj" in name:
        name = name.replace("patch_embed.proj", "embeddings.patch_embeddings.projection")
    if "pos_embed" in name:
        name = name.replace("pos_embed", "embeddings.position_embeddings")
    if "blocks" in name:
        name = name.replace("blocks", "encoder.layer")
    if "attn.proj" in name:
        name = name.replace("attn.proj", "attention.output.dense")
    if "attn" in name:
        name = name.replace("attn", "attention.self")
    if "norm1" in name:
        name = name.replace("norm1", "layernorm_before")
    if "norm2" in name:
        name = name.replace("norm2", "layernorm_after")
    if "mlp.fc1" in name:
        name = name.replace("mlp.fc1", "intermediate.dense")
    if "mlp.fc2" in name:
        name = name.replace("mlp.fc2", "output.dense")
    if "last_norm" in name:
        name = name.replace("last_norm", "layernorm")

    # keypoint head
    if "keypoint_head" in name and config.use_simple_decoder:
        name = name.replace("final_layer.", "")
        name = name.replace("keypoint_head", "head.conv")
    elif "keypoint_head" in name and not config.use_simple_decoder:
        name = name.replace("keypoint_head", "head")
        name = name.replace("deconv_layers.0.weight", "deconv1.weight")
        name = name.replace("deconv_layers.1.weight", "batchnorm1.weight")
        name = name.replace("deconv_layers.1.bias", "batchnorm1.bias")
        name = name.replace("deconv_layers.1.running_mean", "batchnorm1.running_mean")
        name = name.replace("deconv_layers.1.running_var", "batchnorm1.running_var")
        name = name.replace("deconv_layers.1.num_batches_tracked", "batchnorm1.num_batches_tracked")
        name = name.replace("deconv_layers.3.weight", "deconv2.weight")
        name = name.replace("deconv_layers.4.weight", "batchnorm2.weight")
        name = name.replace("deconv_layers.4.bias", "batchnorm2.bias")
        name = name.replace("deconv_layers.4.running_mean", "batchnorm2.running_mean")
        name = name.replace("deconv_layers.4.running_var", "batchnorm2.running_var")
        name = name.replace("deconv_layers.4.num_batches_tracked", "batchnorm2.num_batches_tracked")

        name = name.replace("final_layer.weight", "conv.weight")
        name = name.replace("final_layer.bias", "conv.bias")

    return name


def convert_state_dict(orig_state_dict, dim, config):
    for key in orig_state_dict.copy().keys():
        val = orig_state_dict.pop(key)

        if "qkv" in key:
            key_split = key.split(".")
            layer_num = int(key_split[2])
            if "weight" in key:
                orig_state_dict[f"vit.encoder.layer.{layer_num}.attention.attention.query.weight"] = val[:dim, :]
                orig_state_dict[f"vit.encoder.layer.{layer_num}.attention.attention.key.weight"] = val[
                    dim : dim * 2, :
                ]
                orig_state_dict[f"vit.encoder.layer.{layer_num}.attention.attention.value.weight"] = val[-dim:, :]
            else:
                orig_state_dict[f"vit.encoder.layer.{layer_num}.attention.attention.query.bias"] = val[:dim]
                orig_state_dict[f"vit.encoder.layer.{layer_num}.attention.attention.key.bias"] = val[dim : dim * 2]
                orig_state_dict[f"vit.encoder.layer.{layer_num}.attention.attention.value.bias"] = val[-dim:]
        else:
            orig_state_dict[rename_key(key, config)] = val

    return orig_state_dict


# We will verify our results on a COCO image
def prepare_img():
    url = "http://images.cocodataset.org/val2017/000000000139.jpg"
    image = Image.open(requests.get(url, stream=True).raw)
    return image


name_to_path = {
    "vitpose-base-simple": "/Users/nielsrogge/Documents/ViTPose/vitpose-b-simple.pth",
    "vitpose-base": "/Users/nielsrogge/Documents/ViTPose/vitpose-b.pth",
}


@torch.no_grad()
def convert_vitpose_checkpoint(model_name, pytorch_dump_folder_path, push_to_hub):
    """
    Copy/paste/tweak model's weights to our ViTPose structure.
    """

    # define default ViTPose configuration
    config = get_config(model_name)

    # load HuggingFace model
    model = ViTPoseForPoseEstimation(config)
    model.eval()

    # load original state_dict
    checkpoint_path = name_to_path[model_name]
    state_dict = torch.load(checkpoint_path, map_location="cpu")["state_dict"]

    # for name, param in state_dict.items():
    #     print(name, param.shape)

    # rename some keys
    new_state_dict = convert_state_dict(state_dict, dim=config.hidden_size, config=config)
    model.load_state_dict(new_state_dict)

    # create image processor
    image_processor = ViTPoseImageProcessor()

    # verify image processor
    image = prepare_img()
    boxes = [[[412.8, 157.61, 53.05, 138.01], [384.43, 172.21, 15.12, 35.74]]]
    pixel_values = image_processor(images=image, boxes=boxes, return_tensors="pt").pixel_values

    filepath = hf_hub_download(repo_id="nielsr/test-image", filename="vitpose_batch_data.pt", repo_type="dataset")
    original_pixel_values = torch.load(filepath, map_location="cpu")["img"]
    assert torch.allclose(pixel_values, original_pixel_values)

    img_metas = torch.load(filepath, map_location="cpu")["img_metas"]

    print("Shape of pixel values:", pixel_values.shape)
    with torch.no_grad():
        # first forward pass
        output_heatmap = model(pixel_values).logits

        # TODO assert logits (output heatmap)
        print("Shape of heatmap:", output_heatmap.shape)
        print("Mean value of heatmap:", output_heatmap.numpy().mean())

        print("----------------")

        # second forward pass (flipped)
        pixel_values_flipped = torch.flip(pixel_values, [3])
        print("Mean of pixel_values_flipped:", pixel_values_flipped.mean())
        output_flipped_heatmap = model(
            pixel_values_flipped, flip_pairs=[[1, 2], [3, 4], [5, 6], [7, 8], [9, 10], [11, 12], [13, 14], [15, 16]]
        ).logits

        print("Shape of flipped heatmap:", output_flipped_heatmap.shape)
        print("Mean value of flipped heatmap:", output_flipped_heatmap.mean())

    output_heatmap = (output_heatmap + output_flipped_heatmap) * 0.5

    print("Mean of final output_heatmap:", output_heatmap.mean())

    # TODO verify postprocessing
    batch_size = pixel_values.shape[0]
    heatmaps = output_heatmap.cpu().numpy()

    if "bbox_id" in img_metas[0]:
        bbox_ids = []
    else:
        bbox_ids = None

    c = np.zeros((batch_size, 2), dtype=np.float32)
    s = np.zeros((batch_size, 2), dtype=np.float32)
    image_paths = []
    score = np.ones(batch_size)
    for i in range(batch_size):
        c[i, :] = img_metas[i]["center"]
        s[i, :] = img_metas[i]["scale"]
        image_paths.append(img_metas[i]["image_file"])

        if "bbox_score" in img_metas[i]:
            score[i] = np.array(img_metas[i]["bbox_score"]).reshape(-1)
        if bbox_ids is not None:
            bbox_ids.append(img_metas[i]["bbox_id"])

    preds, maxvals = image_processor.keypoints_from_heatmaps(heatmaps, center=c, scale=s, use_udp=True)

    all_preds = np.zeros((batch_size, preds.shape[1], 3), dtype=np.float32)
    all_boxes = np.zeros((batch_size, 6), dtype=np.float32)
    all_preds[:, :, 0:2] = preds[:, :, 0:2]
    all_preds[:, :, 2:3] = maxvals
    all_boxes[:, 0:2] = c[:, 0:2]
    all_boxes[:, 2:4] = s[:, 0:2]
    all_boxes[:, 4] = np.prod(s * 200.0, axis=1)
    all_boxes[:, 5] = score

    result = {}

    result["preds"] = all_preds
    result["boxes"] = all_boxes
    result["image_paths"] = image_paths
    result["bbox_ids"] = bbox_ids
    result["output_heatmap"] = None  # return_heatmap = False for inference in mmpose

    # print(result)
    poses, _ = result["preds"], result["output_heatmap"]

    # create final results by adding person bbox information
    filepath = hf_hub_download(repo_id="nielsr/test-image", filename="vitpose_person_results.pt", repo_type="dataset")
    person_results = torch.load(filepath, map_location="cpu")
    bboxes = np.array([box["bbox"] for box in person_results])
    bboxes_xyxy = _xywh2xyxy(bboxes)

    pose_results = []
    for pose, person_result, bbox_xyxy in zip(poses, person_results, bboxes_xyxy):
        pose_result = person_result.copy()
        pose_result["keypoints"] = pose
        pose_result["bbox"] = bbox_xyxy
        pose_results.append(pose_result)

    print("Pose results:", pose_results)

    # Verify pose_results
    # This is a list of dictionaries, containing the bounding box and keypoints per detected person
    assert torch.allclose(
        torch.from_numpy(pose_results[0]["bbox"]).float(), torch.tensor([412.8, 157.61, 464.85, 294.62])
    )
    assert torch.allclose(
        torch.from_numpy(pose_results[1]["bbox"]).float(), torch.tensor([384.43, 172.21, 398.55, 206.95])
    )
    assert pose_results[0]["keypoints"].shape == (17, 3)
    assert pose_results[1]["keypoints"].shape == (17, 3)

    if model_name == "vitpose-base-simple":
        assert torch.allclose(
            torch.from_numpy(pose_results[1]["keypoints"][0, :3]),
            torch.tensor([3.98180511e02, 1.81808380e02, 8.66642594e-01]),
        )
    elif model_name == "vitpose-base":
        # TODO not sure this is right
        assert torch.allclose(
            torch.from_numpy(pose_results[1]["keypoints"][0, :3]),
            torch.tensor([3.9807913e02, 1.8182812e02, 8.8235235e-01]),
        )

    if pytorch_dump_folder_path is not None:
        Path(pytorch_dump_folder_path).mkdir(exist_ok=True)
        print(f"Saving model and image processor for {model_name} to {pytorch_dump_folder_path}")
        model.save_pretrained(pytorch_dump_folder_path)
        image_processor.save_pretrained(pytorch_dump_folder_path)

    if push_to_hub:
        print(f"Pushing model and image processor for {model_name} to hub")
        model.push_to_hub(f"nielsr/{model_name}")
        image_processor.push_to_hub(f"nielsr/{model_name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # Required parameters
    parser.add_argument(
        "--model_name",
        default="vitpose-base-simple",
        choices=name_to_path.keys(),
        type=str,
        help="Name of the ViTPose model you'd like to convert.",
    )
    parser.add_argument(
        "--pytorch_dump_folder_path", default=None, type=str, help="Path to the output PyTorch model directory."
    )
    parser.add_argument(
        "--push_to_hub", action="store_true", help="Whether or not to push the converted model to the 🤗 hub."
    )

    args = parser.parse_args()
    convert_vitpose_checkpoint(args.model_name, args.pytorch_dump_folder_path, args.push_to_hub)
