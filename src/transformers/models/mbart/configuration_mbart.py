# coding=utf-8
# Copyright 2021, The Facebook AI Research Team and The HuggingFace Inc. team. All rights reserved.
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
""" MBART model configuration """
from collections import OrderedDict
from typing import Any, Mapping, Optional

from ... import PreTrainedTokenizer
from ...configuration_utils import PretrainedConfig
from ...file_utils import TensorType, is_torch_available
from ...onnx import OnnxConfigWithPast, OnnxSeq2SeqConfigWithPast
from ...utils import logging


logger = logging.get_logger(__name__)

MBART_PRETRAINED_CONFIG_ARCHIVE_MAP = {
    "facebook/mbart-large-cc25": "https://huggingface.co/facebook/mbart-large-cc25/resolve/main/config.json",
    # See all MBART models at https://huggingface.co/models?filter=mbart
}


class MBartConfig(PretrainedConfig):
    r"""
    This is the configuration class to store the configuration of a :class:`~transformers.MBartModel`. It is used to
    instantiate an MBART model according to the specified arguments, defining the model architecture. Instantiating a
    configuration with the defaults will yield a similar configuration to that of the MBART `facebook/mbart-large-cc25
    <https://huggingface.co/facebook/mbart-large-cc25>`__ architecture.

    Configuration objects inherit from :class:`~transformers.PretrainedConfig` and can be used to control the model
    outputs. Read the documentation from :class:`~transformers.PretrainedConfig` for more information.


    Args:
        vocab_size (:obj:`int`, `optional`, defaults to 50265):
            Vocabulary size of the MBART model. Defines the number of different tokens that can be represented by the
            :obj:`inputs_ids` passed when calling :class:`~transformers.MBartModel` or
            :class:`~transformers.TFMBartModel`.
        d_model (:obj:`int`, `optional`, defaults to 1024):
            Dimensionality of the layers and the pooler layer.
        encoder_layers (:obj:`int`, `optional`, defaults to 12):
            Number of encoder layers.
        decoder_layers (:obj:`int`, `optional`, defaults to 12):
            Number of decoder layers.
        encoder_attention_heads (:obj:`int`, `optional`, defaults to 16):
            Number of attention heads for each attention layer in the Transformer encoder.
        decoder_attention_heads (:obj:`int`, `optional`, defaults to 16):
            Number of attention heads for each attention layer in the Transformer decoder.
        decoder_ffn_dim (:obj:`int`, `optional`, defaults to 4096):
            Dimensionality of the "intermediate" (often named feed-forward) layer in decoder.
        encoder_ffn_dim (:obj:`int`, `optional`, defaults to 4096):
            Dimensionality of the "intermediate" (often named feed-forward) layer in decoder.
        activation_function (:obj:`str` or :obj:`function`, `optional`, defaults to :obj:`"gelu"`):
            The non-linear activation function (function or string) in the encoder and pooler. If string,
            :obj:`"gelu"`, :obj:`"relu"`, :obj:`"silu"` and :obj:`"gelu_new"` are supported.
        dropout (:obj:`float`, `optional`, defaults to 0.1):
            The dropout probability for all fully connected layers in the embeddings, encoder, and pooler.
        attention_dropout (:obj:`float`, `optional`, defaults to 0.0):
            The dropout ratio for the attention probabilities.
        activation_dropout (:obj:`float`, `optional`, defaults to 0.0):
            The dropout ratio for activations inside the fully connected layer.
        classifier_dropout (:obj:`float`, `optional`, defaults to 0.0):
            The dropout ratio for classifier.
        max_position_embeddings (:obj:`int`, `optional`, defaults to 1024):
            The maximum sequence length that this model might ever be used with. Typically set this to something large
            just in case (e.g., 512 or 1024 or 2048).
        init_std (:obj:`float`, `optional`, defaults to 0.02):
            The standard deviation of the truncated_normal_initializer for initializing all weight matrices.
        encoder_layerdrop: (:obj:`float`, `optional`, defaults to 0.0):
            The LayerDrop probability for the encoder. See the `LayerDrop paper <see
            https://arxiv.org/abs/1909.11556>`__ for more details.
        decoder_layerdrop: (:obj:`float`, `optional`, defaults to 0.0):
            The LayerDrop probability for the decoder. See the `LayerDrop paper <see
            https://arxiv.org/abs/1909.11556>`__ for more details.
        scale_embedding (:obj:`bool`, `optional`, defaults to :obj:`False`):
            Scale embeddings by diving by sqrt(d_model).
        use_cache (:obj:`bool`, `optional`, defaults to :obj:`True`):
            Whether or not the model should return the last key/values attentions (not used by all models)
        forced_eos_token_id (:obj:`int`, `optional`, defaults to 2):
            The id of the token to force as the last generated token when :obj:`max_length` is reached. Usually set to
            :obj:`eos_token_id`.

    Example::

        >>> from transformers import MBartModel, MBartConfig

        >>> # Initializing a MBART facebook/mbart-large-cc25 style configuration
        >>> configuration = MBartConfig()

        >>> # Initializing a model from the facebook/mbart-large-cc25 style configuration
        >>> model = MBartModel(configuration)

        >>> # Accessing the model configuration
        >>> configuration = model.config
    """
    model_type = "mbart"
    keys_to_ignore_at_inference = ["past_key_values"]
    attribute_map = {"num_attention_heads": "encoder_attention_heads", "hidden_size": "d_model"}

    def __init__(
        self,
        vocab_size=50265,
        max_position_embeddings=1024,
        encoder_layers=12,
        encoder_ffn_dim=4096,
        encoder_attention_heads=16,
        decoder_layers=12,
        decoder_ffn_dim=4096,
        decoder_attention_heads=16,
        encoder_layerdrop=0.0,
        decoder_layerdrop=0.0,
        use_cache=True,
        is_encoder_decoder=True,
        activation_function="gelu",
        d_model=1024,
        dropout=0.1,
        attention_dropout=0.0,
        activation_dropout=0.0,
        init_std=0.02,
        classifier_dropout=0.0,
        scale_embedding=False,
        pad_token_id=1,
        bos_token_id=0,
        eos_token_id=2,
        forced_eos_token_id=2,
        **kwargs
    ):
        self.vocab_size = vocab_size
        self.max_position_embeddings = max_position_embeddings
        self.d_model = d_model
        self.encoder_ffn_dim = encoder_ffn_dim
        self.encoder_layers = encoder_layers
        self.encoder_attention_heads = encoder_attention_heads
        self.decoder_ffn_dim = decoder_ffn_dim
        self.decoder_layers = decoder_layers
        self.decoder_attention_heads = decoder_attention_heads
        self.dropout = dropout
        self.attention_dropout = attention_dropout
        self.activation_dropout = activation_dropout
        self.activation_function = activation_function
        self.init_std = init_std
        self.encoder_layerdrop = encoder_layerdrop
        self.decoder_layerdrop = decoder_layerdrop
        self.classifier_dropout = classifier_dropout
        self.use_cache = use_cache
        self.num_hidden_layers = encoder_layers
        self.scale_embedding = scale_embedding  # scale factor will be sqrt(d_model) if True
        super().__init__(
            pad_token_id=pad_token_id,
            bos_token_id=bos_token_id,
            eos_token_id=eos_token_id,
            is_encoder_decoder=is_encoder_decoder,
            forced_eos_token_id=forced_eos_token_id,
            **kwargs,
        )


# Copied from transformers.models.bart.configuration_bart.BartOnnxConfig with Bart->MBart
class MBartOnnxConfig(OnnxSeq2SeqConfigWithPast):
    @property
    def inputs(self) -> Mapping[str, Mapping[int, str]]:
        if self.task in ["default", "seq2seq-lm"]:
            common_inputs = OrderedDict(
                [
                    ("input_ids", {0: "batch", 1: "encoder_sequence"}),
                    ("attention_mask", {0: "batch", 1: "encoder_sequence"}),
                ]
            )

            if self.use_past:
                common_inputs["decoder_input_ids"] = {0: "batch"}
                common_inputs["decoder_attention_mask"] = {0: "batch", 1: "past_decoder_sequence + sequence"}
            else:
                common_inputs["decoder_input_ids"] = {0: "batch", 1: "decoder_sequence"}
                common_inputs["decoder_attention_mask"] = {0: "batch", 1: "decoder_sequence"}

            if self.use_past:
                self.fill_with_past_key_values_(common_inputs, direction="inputs")
        elif self.task == "causal-lm":
            # TODO: figure this case out.
            common_inputs = OrderedDict(
                [
                    ("input_ids", {0: "batch", 1: "encoder_sequence"}),
                    ("attention_mask", {0: "batch", 1: "encoder_sequence"}),
                ]
            )
            if self.use_past:
                num_encoder_layers, _ = self.num_layers
                for i in range(num_encoder_layers):
                    common_inputs[f"past_key_values.{i}.key"] = {0: "batch", 2: "past_sequence + sequence"}
                    common_inputs[f"past_key_values.{i}.value"] = {0: "batch", 2: "past_sequence + sequence"}
        else:
            common_inputs = OrderedDict(
                [
                    ("input_ids", {0: "batch", 1: "encoder_sequence"}),
                    ("attention_mask", {0: "batch", 1: "encoder_sequence"}),
                    ("decoder_input_ids", {0: "batch", 1: "decoder_sequence"}),
                    ("decoder_attention_mask", {0: "batch", 1: "decoder_sequence"}),
                ]
            )

        return common_inputs

    @property
    def outputs(self) -> Mapping[str, Mapping[int, str]]:
        if self.task in ["default", "seq2seq-lm"]:
            common_outputs = super().outputs
        else:
            common_outputs = super(OnnxConfigWithPast, self).outputs
            if self.use_past:
                num_encoder_layers, _ = self.num_layers
                for i in range(num_encoder_layers):
                    common_outputs[f"present.{i}.key"] = {0: "batch", 2: "past_sequence + sequence"}
                    common_outputs[f"present.{i}.value"] = {0: "batch", 2: "past_sequence + sequence"}
        return common_outputs

    def generate_dummy_inputs(
        self,
        tokenizer: PreTrainedTokenizer,
        batch_size: int = -1,
        seq_length: int = -1,
        is_pair: bool = False,
        framework: Optional[TensorType] = None,
    ) -> Mapping[str, Any]:

        if self.task in ["default", "seq2seq-lm"]:
            encoder_inputs = super(OnnxConfigWithPast, self).generate_dummy_inputs(
                tokenizer, batch_size, seq_length, is_pair, framework
            )

            # Generate decoder inputs
            decoder_inputs = super(OnnxConfigWithPast, self).generate_dummy_inputs(
                tokenizer, batch_size, 1, is_pair, framework
            )
            decoder_inputs = {f"decoder_{name}": tensor for name, tensor in decoder_inputs.items()}
            common_inputs = dict(**encoder_inputs, **decoder_inputs)

            if self.use_past:
                if not is_torch_available():
                    raise ValueError("Cannot generate dummy past_keys inputs without PyTorch installed.")
                else:
                    import torch
                batch = common_inputs["input_ids"].shape[0]
                encoder_seq_length = common_inputs["input_ids"].shape[1]
                num_encoder_attention_heads, num_decoder_attention_heads = self.num_attention_heads
                encoder_shape = (
                    batch,
                    num_encoder_attention_heads,
                    encoder_seq_length,
                    self._config.hidden_size // num_encoder_attention_heads,
                )
                decoder_shape = (
                    batch,
                    num_decoder_attention_heads,
                    1,
                    self._config.hidden_size // num_decoder_attention_heads,
                )

                common_inputs["decoder_attention_mask"] = torch.cat(
                    [common_inputs["decoder_attention_mask"], torch.ones(batch, 1)], dim=1
                )

                common_inputs["past_key_values"] = []
                # If the number of encoder and decoder layers are present in the model configuration, both are considered
                num_encoder_layers, num_decoder_layers = self.num_layers
                min_num_layers = min(num_encoder_layers, num_decoder_layers)
                max_num_layers = max(num_encoder_layers, num_decoder_layers) - min_num_layers
                remaining_side_name = "encoder" if num_encoder_layers > num_decoder_layers else "decoder"

                for _ in range(min_num_layers):
                    common_inputs["past_key_values"].append(
                        (
                            torch.zeros(decoder_shape),
                            torch.zeros(decoder_shape),
                            torch.zeros(encoder_shape),
                            torch.zeros(encoder_shape),
                        )
                    )

                # TODO: test this.
                shape = encoder_shape if remaining_side_name == "encoder" else decoder_shape
                for _ in range(min_num_layers, max_num_layers):
                    common_inputs["past_key_values"].append((torch.zeros(shape), torch.zeros(shape)))

        elif self.task == "causal-lm":
            common_inputs = super(OnnxConfigWithPast, self).generate_dummy_inputs(
                tokenizer, batch_size, seq_length, is_pair, framework
            )

            if self.use_past:
                if not is_torch_available():
                    raise ValueError("Cannot generate dummy past_keys inputs without PyTorch installed.")
                else:
                    import torch

                    batch = common_inputs["input_ids"].shape[0]
                    num_encoder_layers, _ = self.num_layers
                    num_encoder_attention_heads, _ = self.num_attention_heads
                    past_shape = (
                        batch,
                        num_encoder_attention_heads,
                        1,
                        self._config.hidden_size // num_encoder_attention_heads,
                    )

                    common_inputs["attention_mask"] = torch.cat(
                        [common_inputs["attention_mask"], torch.ones(batch, 1)], dim=1
                    )
                    common_inputs["past_key_values"] = [
                        (torch.zeros(past_shape), torch.zeros(past_shape)) for _ in range(num_encoder_layers)
                    ]
        else:
            common_inputs = super(OnnxConfigWithPast, self).generate_dummy_inputs(
                tokenizer, batch_size, seq_length, is_pair, framework
            )

        return common_inputs

    def _flatten_past_key_values_(self, flattened_output, name, idx, t):
        if self.task in ["default", "seq2seq-lm"]:
            flattened_output = super()._flatten_past_key_values_(flattened_output, name, idx, t)
        else:
            flattened_output = super(OnnxSeq2SeqConfigWithPast, self)._flatten_past_key_values_(
                flattened_output, name, idx, t
            )
