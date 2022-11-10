# coding=utf-8
# Copyright 2022 The HuggingFace Inc. team.
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
"""Convert MobileNetV2 checkpoints from the tensorflow/models library."""


import argparse
import json
import re
from pathlib import Path

import torch
from PIL import Image

import requests
from huggingface_hub import hf_hub_download
from transformers import (
    MobileNetV2Config,
    MobileNetV2FeatureExtractor,
    MobileNetV2ForImageClassification,
    load_tf_weights_in_mobilenet_v2,
)
from transformers.utils import logging


logging.set_verbosity_info()
logger = logging.get_logger(__name__)


def get_mobilenet_v2_config(model_name):
    config = MobileNetV2Config(layer_norm_eps=0.001)

    if "quant" in model_name:
        raise ValueError("Quantized models are not supported.")

    matches = re.match(r"^mobilenet_v2_([^_]*)_([^_]*)$", model_name)
    if matches:
        config.depth_multiplier = float(matches[1])
        config.image_size = int(matches[2])

    # The TensorFlow version of MobileNetV2 predicts 1001 classes instead of
    # the usual 1000. The first class (index 0) is "background".
    config.num_labels = 1001
    filename = "imagenet-1k-id2label.json"
    repo_id = "datasets/huggingface/label-files"
    id2label = json.load(open(hf_hub_download(repo_id, filename), "r"))
    id2label = {int(k) + 1: v for k, v in id2label.items()}
    id2label[0] = "background"
    config.id2label = id2label
    config.label2id = {v: k for k, v in id2label.items()}

    return config


# We will verify our results on an image of cute cats
def prepare_img():
    url = "http://images.cocodataset.org/val2017/000000039769.jpg"
    im = Image.open(requests.get(url, stream=True).raw)
    return im


@torch.no_grad()
def convert_movilevit_checkpoint(model_name, checkpoint_path, pytorch_dump_folder_path, push_to_hub=False):
    """
    Copy/paste/tweak model's weights to our MobileNetV2 structure.
    """
    config = get_mobilenet_v2_config(model_name)

    # Load 🤗 model
    model = MobileNetV2ForImageClassification(config).eval()

    # Load weights from TensorFlow checkpoint
    load_tf_weights_in_mobilenet_v2(model, config, checkpoint_path)

    # Check outputs on an image, prepared by MobileNetV2FeatureExtractor
    feature_extractor = MobileNetV2FeatureExtractor(crop_size=config.image_size, size=config.image_size + 32)
    encoding = feature_extractor(images=prepare_img(), return_tensors="pt")
    outputs = model(**encoding)
    logits = outputs.logits

    assert logits.shape == (1, 1001)

    if model_name == "mobilenet_v2_1.4_224":
        expected_logits = torch.tensor([0.0181, -1.0015, 0.4688])
    elif model_name == "mobilenet_v2_1.0_224":
        expected_logits = torch.tensor([0.2445, -1.1993, 0.1905])
    elif model_name == "mobilenet_v2_0.75_160":
        expected_logits = torch.tensor([0.2482, 0.4136, 0.6669])
    elif model_name == "mobilenet_v2_0.35_96":
        expected_logits = torch.tensor([0.1451, -0.4624, 0.7192])
    else:
        expected_logits = None

    if expected_logits is not None:
        assert torch.allclose(logits[0, :3], expected_logits, atol=1e-4)

    Path(pytorch_dump_folder_path).mkdir(exist_ok=True)
    print(f"Saving model {model_name} to {pytorch_dump_folder_path}")
    model.save_pretrained(pytorch_dump_folder_path)
    print(f"Saving feature extractor to {pytorch_dump_folder_path}")
    feature_extractor.save_pretrained(pytorch_dump_folder_path)

    if push_to_hub:
        print("Pushing to the hub...")
        organization_name = "Matthijs"
        feature_extractor.push_to_hub(model_name, organization=organization_name)
        model.push_to_hub(model_name, organization=organization_name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # Required parameters
    parser.add_argument(
        "--model_name",
        default="mobilenet_v2_1.0_224",
        type=str,
        help="Name of the MobileNetV2 model you'd like to convert. Should in the form 'mobilenet_v2_<depth>_<size>'.",
    )
    parser.add_argument(
        "--checkpoint_path", required=True, type=str, help="Path to the original TensorFlow checkpoint (.ckpt file)."
    )
    parser.add_argument(
        "--pytorch_dump_folder_path", required=True, type=str, help="Path to the output PyTorch model directory."
    )
    parser.add_argument(
        "--push_to_hub", action="store_true", help="Whether or not to push the converted model to the 🤗 hub."
    )

    args = parser.parse_args()
    convert_movilevit_checkpoint(
        args.model_name, args.checkpoint_path, args.pytorch_dump_folder_path, args.push_to_hub
    )
