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
"""Convert Wav2Vec2BERT BERT checkpoint."""


import argparse

import torch
from seamless_communication.models.conformer_shaw import load_conformer_shaw_model

from transformers import (
    Wav2Vec2BERTFeatureExtractor,
    Wav2Vec2BERTConfig,
    Wav2Vec2BERTForPreTraining,
    logging,
)


logging.set_verbosity_info()
logger = logging.get_logger(__name__)


wav2vec_convert_list = [
    ("encoder", "wav2vec2_bert.encoder"),
    ("encoder_frontend.model_dim_proj", "feature_projection.projection"),
    ("encoder_frontend.post_extract_layer_norm", "feature_projection.layer_norm"),
    ("encoder_frontend.pos_encoder.conv", "encoder.pos_conv_embed.conv"),
    ("encoder.inner.layers", "encoder.layers"),
    ("encoder.inner_layer_norm", "encoder.layer_norm"),
    ("encoder.adaptor_layers", "adapter.layers"),
    ("inner_proj", "intermediate_dense"),
    ("self_attn.output_proj", "self_attn.linear_out"),
    ("output_proj", "output_dense"),
    ("self_attn.k_proj", "self_attn.linear_k"),
    ("self_attn.v_proj", "self_attn.linear_v"),
    ("self_attn.q_proj", "self_attn.linear_q"),
    ("self_attn.sdpa.u_bias", "self_attn.pos_bias_u"),
    ("self_attn.sdpa.v_bias", "self_attn.pos_bias_v"),
    ("self_attn.sdpa.rel_k_embed", "self_attn.distance_embedding"),
    ("self_attn.sdpa.r_proj", "self_attn.linear_pos"),
    ("conv.pointwise_conv1", "conv_module.pointwise_conv1"),
    ("conv.pointwise_conv2", "conv_module.pointwise_conv2"),
    ("conv.depthwise_conv", "conv_module.depthwise_conv"),
    ("conv.layer_norm", "conv_module.depthwise_layer_norm"),
    ("conv_layer_norm", "conv_module.layer_norm"),
    ("encoder.proj1", "intermediate_ffn.intermediate_dense"),
    ("encoder.proj2", "intermediate_ffn.output_dense"),
    ("encoder.layer_norm", "inner_layer_norm"),
    ("quantizer.entry_proj", "quantizer.weight_proj"),
    ("final_proj", "project_hid"),
    ("final_target_proj", "project_q"),
    ("masker.temporal_mask_embed", "wav2vec2_bert.masked_spec_embed"),
    ("quantizer.entries", "quantizer.codevectors"),
]


def param_count(model):
    return sum(p[1].numel() for p in model.named_parameters() if "final_proj" not in p[0])


def _convert_model(
    original_model,
    hf_model,
    convert_list,
):
    state_dict = original_model.state_dict()

    for k, v in list(state_dict.items()):
        new_key = k
        for old_layer_name, new_layer_name in convert_list:
            if old_layer_name in new_key:
                new_key = new_key.replace(old_layer_name, new_layer_name)

        # must do it by hand
        if ".layer_norm" in new_key and new_key.split(".layer_norm")[0][-1].isnumeric():
            new_key = new_key.replace("layer_norm", "final_layer_norm")

        state_dict[new_key] = state_dict.pop(k)

    extra_keys = set(state_dict.keys()) - set(hf_model.state_dict().keys())
    extra_keys = set({k for k in extra_keys if "num_updates" not in k})  # filter unecessary param
    missing_keys = set(hf_model.state_dict().keys()) - set(state_dict.keys())
    if len(extra_keys) != 0:
        raise ValueError(f"extra keys found: {extra_keys}")
    if len(missing_keys) != 0:
        raise ValueError(f"missing keys: {missing_keys}")
    hf_model.load_state_dict(state_dict, strict=False)
    n_params = param_count(hf_model)

    logger.info(f"model loaded: {round(n_params/1e6,1)}M params")

    hf_model.eval()
    del state_dict

    return hf_model


@torch.no_grad()
def convert_wav2vec2_bert_checkpoint(
    checkpoint_path,
    pytorch_dump_folder_path,
    config_path=None,
    repo_id=None,
):
    """
    Copy/paste/tweak model's weights to transformers design.
    """
    if config_path is not None:
        config = Wav2Vec2BERTConfig.from_pretrained(config_path, hidden_act="swish")
    else:
        config = Wav2Vec2BERTConfig(apply_spec_augment=False)

    hf_wav2vec = Wav2Vec2BERTForPreTraining(config)

    model = load_conformer_shaw_model(checkpoint_path, dtype=torch.float32)
    model.eval()

    hf_wav2vec = _convert_model(model, hf_wav2vec, wav2vec_convert_list)

    hf_wav2vec.save_pretrained(pytorch_dump_folder_path)

    if repo_id:
        hf_wav2vec.push_to_hub(repo_id, create_pr=True)

    # save feature extractor
    fe = Wav2Vec2BERTFeatureExtractor(padding_value=1)
    fe.save_pretrained(pytorch_dump_folder_path)

    if repo_id:
        fe.push_to_hub(repo_id, create_pr=True)

    if args.audio_path:
        import torchaudio
        from fairseq2.data import Collater
        from fairseq2.data.audio import WaveformToFbankConverter
        from fairseq2.nn.padding import get_seqs_and_padding_mask

        waveform, sample_rate = torchaudio.load(args.audio_path)
        waveform = torchaudio.functional.resample(waveform, sample_rate, fe.sampling_rate)

        fbank_converter = WaveformToFbankConverter(
            num_mel_bins=80,
            waveform_scale=2**15,
            channel_last=True,
            standardize=True,
            dtype=torch.float32,
        )
        collater = Collater(pad_value=1)

        decoded_audio = {"waveform": waveform.T, "sample_rate": fe.sampling_rate, "format": -1}
        src = collater(fbank_converter(decoded_audio))["fbank"]
        seqs, padding_mask = get_seqs_and_padding_mask(src)

        with torch.inference_mode():
            seqs, padding_mask = model.encoder_frontend(seqs, padding_mask)
            original_output, padding_mask = model.encoder(seqs, padding_mask)

        hf_wav2vec.eval()

        inputs = fe(waveform, return_tensors="pt", padding=True)
        with torch.no_grad():
            outputs = hf_wav2vec.wav2vec2_bert(**inputs)

        torch.testing.assert_close(original_output, outputs.last_hidden_state, atol=5e-3, rtol=5e-3)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pytorch_dump_folder_path",
        default="/home/yoach/tmp/wav2vec_seamless",
        type=str,
        help="Path to the output PyTorch model.",
    )
    parser.add_argument(
        "--checkpoint_path", default="conformer_shaw", type=str, help="Path to seamless communication checkpoint"
    )
    parser.add_argument(
        "--config_path",
        default=None,
        type=str,
        help="Path to hf config.json of model to convert",
    )
    parser.add_argument(
        "--repo_id", default="w2v-bert-2.0", type=str, help="Push to this repo id if precised."
    )
    parser.add_argument(
        "--audio_path",
        default="/home/yoach/transformers/audio_vits.wav",
        type=str,
        help="If specified, check that the original model and the converted model produce the same outputs.",
    )

    args = parser.parse_args()
    convert_wav2vec2_bert_checkpoint(
        args.checkpoint_path, args.pytorch_dump_folder_path, args.config_path, args.repo_id
    )
