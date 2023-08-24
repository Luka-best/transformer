# coding=utf-8
# Copyright 2023 The HuggingFace Inc. team. All rights reserved.
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
"""Convert VITS checkpoint."""

import argparse
import json
import os
import tempfile
import torch

from transformers import (
    VitsConfig,
    VitsModel,
    VitsMmsTokenizer,
    logging,
)


logging.set_verbosity_info()
logger = logging.get_logger("transformers.models.vits")

MAPPING_TEXT_ENCODER = {
    "enc_p.emb": "text_encoder.embed_tokens",
    "enc_p.encoder.attn_layers.*.conv_k": "text_encoder.encoder.layers.*.attention.k_proj",
    "enc_p.encoder.attn_layers.*.conv_v": "text_encoder.encoder.layers.*.attention.v_proj",
    "enc_p.encoder.attn_layers.*.conv_q": "text_encoder.encoder.layers.*.attention.q_proj",
    "enc_p.encoder.attn_layers.*.conv_o": "text_encoder.encoder.layers.*.attention.out_proj",
    "enc_p.encoder.attn_layers.*.emb_rel_k": "text_encoder.encoder.layers.*.attention.emb_rel_k",
    "enc_p.encoder.attn_layers.*.emb_rel_v": "text_encoder.encoder.layers.*.attention.emb_rel_v",
    "enc_p.encoder.norm_layers_1.*.gamma": "text_encoder.encoder.layers.*.layer_norm.weight",
    "enc_p.encoder.norm_layers_1.*.beta": "text_encoder.encoder.layers.*.layer_norm.bias",
    "enc_p.encoder.ffn_layers.*.conv_1": "text_encoder.encoder.layers.*.feed_forward.conv_1",
    "enc_p.encoder.ffn_layers.*.conv_2": "text_encoder.encoder.layers.*.feed_forward.conv_2",
    "enc_p.encoder.norm_layers_2.*.gamma": "text_encoder.encoder.layers.*.final_layer_norm.weight",
    "enc_p.encoder.norm_layers_2.*.beta": "text_encoder.encoder.layers.*.final_layer_norm.bias",
    "enc_p.proj": "text_encoder.project",
}
MAPPING_STOCHASTIC_DURATION_PREDICTOR = {
    "dp.pre": "duration_predictor.pre",
    "dp.proj": "duration_predictor.proj",
    "dp.convs.convs_sep.0" : "duration_predictor.convs.convs_sep.0",
    "dp.convs.convs_sep.1" : "duration_predictor.convs.convs_sep.1",
    "dp.convs.convs_sep.2" : "duration_predictor.convs.convs_sep.2",
    "dp.convs.convs_1x1.0" : "duration_predictor.convs.convs_1x1.0",
    "dp.convs.convs_1x1.1" : "duration_predictor.convs.convs_1x1.1",
    "dp.convs.convs_1x1.2" : "duration_predictor.convs.convs_1x1.2",
    "dp.convs.norms_1.*.gamma" : "duration_predictor.convs.norms_1.*.weight",
    "dp.convs.norms_1.*.beta" : "duration_predictor.convs.norms_1.*.bias",
    "dp.convs.norms_2.*.gamma" : "duration_predictor.convs.norms_2.*.weight",
    "dp.convs.norms_2.*.beta" : "duration_predictor.convs.norms_2.*.bias",
    "dp.flows.0.logs" : "duration_predictor.flows.0.logs",
    "dp.flows.0.m" : "duration_predictor.flows.0.m",
    "dp.flows.*.pre" : "duration_predictor.flows.*.pre",
    "dp.flows.*.proj" : "duration_predictor.flows.*.proj",
    "dp.flows.*.convs.convs_1x1.0" : "duration_predictor.flows.*.convs.convs_1x1.0",
    "dp.flows.*.convs.convs_1x1.1" : "duration_predictor.flows.*.convs.convs_1x1.1",
    "dp.flows.*.convs.convs_1x1.2" : "duration_predictor.flows.*.convs.convs_1x1.2",
    "dp.flows.*.convs.convs_sep.0" : "duration_predictor.flows.*.convs.convs_sep.0",
    "dp.flows.*.convs.convs_sep.1" : "duration_predictor.flows.*.convs.convs_sep.1",
    "dp.flows.*.convs.convs_sep.2" : "duration_predictor.flows.*.convs.convs_sep.2",
    "dp.flows.*.convs.norms_1.0.gamma" : "duration_predictor.flows.*.convs.norms_1.0.weight",
    "dp.flows.*.convs.norms_1.0.beta" : "duration_predictor.flows.*.convs.norms_1.0.bias",
    "dp.flows.*.convs.norms_1.1.gamma" : "duration_predictor.flows.*.convs.norms_1.1.weight",
    "dp.flows.*.convs.norms_1.1.beta" : "duration_predictor.flows.*.convs.norms_1.1.bias",
    "dp.flows.*.convs.norms_1.2.gamma" : "duration_predictor.flows.*.convs.norms_1.2.weight",
    "dp.flows.*.convs.norms_1.2.beta" : "duration_predictor.flows.*.convs.norms_1.2.bias",
    "dp.flows.*.convs.norms_2.0.gamma" : "duration_predictor.flows.*.convs.norms_2.0.weight",
    "dp.flows.*.convs.norms_2.0.beta" : "duration_predictor.flows.*.convs.norms_2.0.bias",
    "dp.flows.*.convs.norms_2.1.gamma" : "duration_predictor.flows.*.convs.norms_2.1.weight",
    "dp.flows.*.convs.norms_2.1.beta" : "duration_predictor.flows.*.convs.norms_2.1.bias",
    "dp.flows.*.convs.norms_2.2.gamma" : "duration_predictor.flows.*.convs.norms_2.2.weight",
    "dp.flows.*.convs.norms_2.2.beta" : "duration_predictor.flows.*.convs.norms_2.2.bias",
}
MAPPING_FLOW = {
    "flow.flows.*.pre" : "flow.flows.*.pre",
    "flow.flows.*.enc.in_layers.0" : "flow.flows.*.enc.in_layers.0",
    "flow.flows.*.enc.in_layers.1" : "flow.flows.*.enc.in_layers.1",
    "flow.flows.*.enc.in_layers.2" : "flow.flows.*.enc.in_layers.2",
    "flow.flows.*.enc.in_layers.3" : "flow.flows.*.enc.in_layers.3",
    "flow.flows.*.enc.res_skip_layers.0" : "flow.flows.*.enc.res_skip_layers.0",
    "flow.flows.*.enc.res_skip_layers.1" : "flow.flows.*.enc.res_skip_layers.1",
    "flow.flows.*.enc.res_skip_layers.2" : "flow.flows.*.enc.res_skip_layers.2",
    "flow.flows.*.enc.res_skip_layers.3" : "flow.flows.*.enc.res_skip_layers.3",
    "flow.flows.*.post" : "flow.flows.*.post",
}
MAPPING_GENERATOR = {
    "dec.conv_pre" : "dec.conv_pre",
    "dec.ups.0" : "dec.ups.0",
    "dec.ups.1" : "dec.ups.1",
    "dec.ups.2" : "dec.ups.2",
    "dec.ups.3" : "dec.ups.3",
    "dec.resblocks.*.convs1.0" : "dec.resblocks.*.convs1.0",
    "dec.resblocks.*.convs1.1" : "dec.resblocks.*.convs1.1",
    "dec.resblocks.*.convs1.2" : "dec.resblocks.*.convs1.2",
    "dec.resblocks.*.convs2.0" : "dec.resblocks.*.convs2.0",
    "dec.resblocks.*.convs2.1" : "dec.resblocks.*.convs2.1",
    "dec.resblocks.*.convs2.2" : "dec.resblocks.*.convs2.2",
    "dec.conv_post" : "dec.conv_post",
}
MAPPING = {
    **MAPPING_TEXT_ENCODER,
    **MAPPING_STOCHASTIC_DURATION_PREDICTOR,
    **MAPPING_FLOW,
    **MAPPING_GENERATOR,
}
TOP_LEVEL_KEYS = []
IGNORE_KEYS = []


def set_recursively(hf_pointer, key, value, full_name, weight_type):
    for attribute in key.split("."):
        hf_pointer = getattr(hf_pointer, attribute)

    if weight_type is not None:
        hf_shape = getattr(hf_pointer, weight_type).shape
    else:
        hf_shape = hf_pointer.shape

    # strip off the kernel dimension at the end (original weights are Conv1d)
    if key.endswith(".k_proj") or key.endswith(".v_proj") or key.endswith(".q_proj") or key.endswith(".out_proj"):
        value = value.squeeze(-1)

    if hf_shape != value.shape:
        raise ValueError(
            f"Shape of hf {key + '.' + weight_type if weight_type is not None else ''} is {hf_shape}, but should be"
            f" {value.shape} for {full_name}"
        )

    if weight_type == "weight":
        hf_pointer.weight.data = value
    elif weight_type == "weight_g":
        hf_pointer.weight_g.data = value
    elif weight_type == "weight_v":
        hf_pointer.weight_v.data = value
    elif weight_type == "bias":
        hf_pointer.bias.data = value
    elif weight_type == "running_mean":
        hf_pointer.running_mean.data = value
    elif weight_type == "running_var":
        hf_pointer.running_var.data = value
    elif weight_type == "num_batches_tracked":
        hf_pointer.num_batches_tracked.data = value
    else:
        hf_pointer.data = value

    logger.info(f"{key + ('.' + weight_type if weight_type is not None else '')} was initialized from {full_name}.")


def should_ignore(name, ignore_keys):
    for key in ignore_keys:
        if key.endswith(".*"):
            if name.startswith(key[:-1]):
                return True
        elif ".*." in key:
            prefix, suffix = key.split(".*.")
            if prefix in name and suffix in name:
                return True
        elif key in name:
            return True
    return False


def recursively_load_weights(fairseq_dict, hf_model):
    unused_weights = []

    for name, value in fairseq_dict.items():
        if should_ignore(name, IGNORE_KEYS):
            logger.info(f"{name} was ignored")
            continue

        is_used = False
        for key, mapped_key in MAPPING.items():
            if "*" in key:
                prefix, suffix = key.split(".*.")
                if prefix in name and suffix in name:
                    key = suffix

            if key in name:
                is_used = True
                if "*" in mapped_key:
                    layer_index = name.split(key)[0].split(".")[-2]
                    mapped_key = mapped_key.replace("*", layer_index)
                if "weight_g" in name:
                    weight_type = "weight_g"
                elif "weight_v" in name:
                    weight_type = "weight_v"
                elif "bias" in name:
                    weight_type = "bias"
                elif "weight" in name:
                    weight_type = "weight"
                elif "running_mean" in name:
                    weight_type = "running_mean"
                elif "running_var" in name:
                    weight_type = "running_var"
                elif "num_batches_tracked" in name:
                    weight_type = "num_batches_tracked"
                else:
                    weight_type = None
                set_recursively(hf_model, mapped_key, value, name, weight_type)
            continue
        if not is_used:
            unused_weights.append(name)

    logger.warning(f"Unused weights: {unused_weights}")


@torch.no_grad()
def convert_checkpoint(
    checkpoint_path,
    pytorch_dump_folder_path,
    config_path=None,
    vocab_path=None,
    language=None,
    repo_id=None,
):
    """
    Copy/paste/tweak model's weights to transformers design.
    """
    if config_path is not None:
        config = VitsConfig.from_pretrained(config_path)
    else:
        config = VitsConfig()

    if vocab_path is None:
        vocab_path = os.path.join(checkpoint_path, "vocab.txt")

    # Save vocab as temporary json file
    symbols = [
        line.replace("\n", "") for line in open(vocab_path, encoding="utf-8").readlines()
    ]
    symbol_to_id = {s: i for i, s in enumerate(symbols)}

    with tempfile.NamedTemporaryFile() as tf:
        with open(tf.name, "w", encoding="utf-8") as f:
            f.write(json.dumps(symbol_to_id, indent=2, sort_keys=True, ensure_ascii=False) + "\n")

        tokenizer = VitsMmsTokenizer(tf.name)

    tokenizer.language = language
    config.vocab_size = tokenizer.vocab_size - 2  # added <pad> and <unk>
    model = VitsModel(config)

    orig_checkpoint = torch.load(os.path.join(checkpoint_path, "G_100000.pth"), map_location=torch.device("cpu"))
    recursively_load_weights(orig_checkpoint["model"], model)

    model.save_pretrained(pytorch_dump_folder_path)
    tokenizer.save_pretrained(pytorch_dump_folder_path)

    if repo_id:
        print("Pushing to the hub...")
        tokenizer.push_to_hub(repo_id)
        model.push_to_hub(repo_id)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint_path", required=True, default=None, type=str, help="Path to original checkpoint")
    parser.add_argument("--vocab_path", default=None, type=str, help="Path to vocab.txt")
    parser.add_argument("--config_path", default=None, type=str, help="Path to hf config.json of model to convert")
    parser.add_argument("--language", default=None, type=str, help="Tokenizer language")
    parser.add_argument(
        "--pytorch_dump_folder_path", required=True, default=None, type=str, help="Path to the output PyTorch model."
    )
    parser.add_argument(
        "--push_to_hub", default=None, type=str, help="Where to upload the converted model on the 🤗 hub."
    )

    args = parser.parse_args()
    convert_checkpoint(
        args.checkpoint_path,
        args.pytorch_dump_folder_path,
        args.config_path,
        args.vocab_path,
        args.language,
        args.push_to_hub,
    )
