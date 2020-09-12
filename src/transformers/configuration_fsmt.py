# coding=utf-8
# Copyright 2019-present, Facebook, Inc and the HuggingFace Inc. team.
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
""" FSMT configuration """


import copy
import logging

from .configuration_utils import PretrainedConfig
from .file_utils import add_start_docstrings_to_callable


logger = logging.getLogger(__name__)

FSMT_PRETRAINED_CONFIG_ARCHIVE_MAP = {
    "stas/wmt19-ru-en": "https://s3.amazonaws.com/models.huggingface.co/bert/stas/wmt19-ru-en/config.json",
    "stas/wmt19-en-ru": "https://s3.amazonaws.com/models.huggingface.co/bert/stas/wmt19-en-ru/config.json",
    "stas/wmt19-de-en": "https://s3.amazonaws.com/models.huggingface.co/bert/stas/wmt19-de-en/config.json",
    "stas/wmt19-en-de": "https://s3.amazonaws.com/models.huggingface.co/bert/stas/wmt19-en-de/config.json",
}


FSMT_CONFIG_ARGS_DOC = r"""
    Args:
        src_vocab_size (:obj:`int`, optional, defaults to None):
            defines the different tokens that can be represented by `inputs_ids` passed to the forward
            method in the encoder.
        tgt_vocab_size (:obj:`int`, optional, defaults to None):
            defines the different tokens that can be represented by `inputs_ids` passed to the forward
            method in the decoder.
        d_model (:obj:`int`, optional, defaults to 1024):
            Dimensionality of the layers and the pooler layer.
        encoder_layers (:obj:`int`, optional, defaults to 12):
            Number of encoder layers, 16 for pegasus, 6 for bart-base and marian
        decoder_layers (:obj:`int`, optional, defaults to 12):
            Number of decoder layers, 16 for pegasus, 6 for bart-base and marian
        encoder_attention_heads (:obj:`int`, optional, defaults to 16):
            Number of attention heads for each attention layer in the Transformer encoder.
        decoder_attention_heads (:obj:`int`, optional, defaults to 16):
            Number of attention heads for each attention layer in the Transformer decoder.
        decoder_ffn_dim (:obj:`int`, optional, defaults to 4096):
            Dimensionality of the "intermediate" (i.e., feed-forward) layer in decoder.
        encoder_ffn_dim (:obj:`int`, optional, defaults to 4096):
            Dimensionality of the "intermediate" (i.e., feed-forward) layer in decoder.
        activation_function (:obj:`str` or :obj:`function`, optional, defaults to "relu"):
            The non-linear activation function (function or string) in the encoder and pooler.
            If string, "gelu", "relu", "swish" and "gelu_new" are supported.
        dropout (:obj:`float`, optional, defaults to 0.1):
            The dropout probabilitiy for all fully connected layers in the embeddings, encoder, and pooler.
        attention_dropout (:obj:`float`, optional, defaults to 0.0):
            The dropout ratio for the attention probabilities.
        activation_dropout (:obj:`float`, optional, defaults to 0.0):
            The dropout ratio for activations inside the fully connected layer.
        max_position_embeddings (:obj:`int`, optional, defaults to 1024):
            The maximum sequence length that this model might ever be used with.
            Typically set this to something large just in case (e.g., 512 or 1024 or 2048).
        init_std (:obj:`float`, optional, defaults to 0.02):
            The standard deviation of the truncated_normal_initializer for initializing all weight matrices.
        scale_embedding (:obj:`bool`, optional, defaults to :obj:`True`):
            Scale embeddings by diving by sqrt(d_model).
        bos_token_id (:obj:`int`, optional, defaults to 0)
            Beginning of stream token id.
        pad_token_id (:obj:`int`, optional, defaults to 1)
            Padding token id.
        eos_token_id (:obj:`int`, optional, defaults to 2)
            End of stream token id.
        decoder_start_token_id (:obj:`int`, `optional`):
            This model starts decoding with `eos_token_id`
        encoder_layerdrop: (:obj:`float`, optional, defaults to 0.0):
            Google "layerdrop arxiv", as its not explainable in one line.
        decoder_layerdrop: (:obj:`float`, optional, defaults to 0.0):
            Google "layerdrop arxiv", as its not explainable in one line.
        is_encoder_decoder (:obj:`bool`, optional, defaults to :obj:`True`):
            Whether this is an encoder/decoder model.
        tie_word_embeddings (:obj:`bool`, optional, defaults to :obj:`False`):
            Whether to tie input and output embeddings.
"""


class DecoderConfig(PretrainedConfig):
    r"""
    Configuration class for FSMT's decoder specific things.
    note: this is a private helper class
    """
    model_type = "fsmt_decoder"

    def __init__(self, vocab_size=0, bos_token_id=0):
        super().__init__()
        self.vocab_size = vocab_size
        self.bos_token_id = bos_token_id


@add_start_docstrings_to_callable(FSMT_CONFIG_ARGS_DOC)
class FSMTConfig(PretrainedConfig):
    r"""
    Configuration class for FSMT.
    """
    model_type = "fsmt"

    # update the defaults from config file
    def __init__(
        self,
        langs=None,
        src_vocab_size=None,
        tgt_vocab_size=None,
        activation_function="relu",
        d_model=1024,
        max_length=200,
        num_beams=8,
        max_position_embeddings=1024,
        encoder_ffn_dim=4096,
        encoder_layers=12,
        encoder_attention_heads=16,
        encoder_layerdrop=0.0,
        decoder_ffn_dim=4096,
        decoder_layers=12,
        decoder_attention_heads=16,
        decoder_layerdrop=0.0,
        attention_dropout=0.0,
        dropout=0.1,
        activation_dropout=0.0,
        init_std=0.02,
        pad_token_id=1,
        bos_token_id=0,
        eos_token_id=2,
        decoder_start_token_id=2,
        is_encoder_decoder=True,
        scale_embedding=True,
        tie_word_embeddings=False,
        **common_kwargs
    ):
        r"""
        :class:`~transformers.FSMTConfig` is the configuration class for `FSMTModel`.

        Examples::

            >>> from transformers import FSMTConfig, FSMTModel

            >>> config = FSMTConfig.from_pretrained('stas/wmt19-en-ru')
            >>> model = FSMTModel(config)

        """
        if "hidden_size" in common_kwargs:
            raise ValueError("hidden size is called d_model")
        super().__init__(
            pad_token_id=pad_token_id,
            bos_token_id=bos_token_id,
            eos_token_id=eos_token_id,
            decoder_start_token_id=decoder_start_token_id,
            is_encoder_decoder=is_encoder_decoder,
            tie_word_embeddings=tie_word_embeddings,
            **common_kwargs,
        )
        self.langs = langs
        self.src_vocab_size = src_vocab_size
        self.tgt_vocab_size = tgt_vocab_size
        self.d_model = d_model  # encoder_embed_dim and decoder_embed_dim
        self.max_length = max_length
        self.num_beams = num_beams
        self.encoder_ffn_dim = encoder_ffn_dim
        self.encoder_layers = self.num_hidden_layers = encoder_layers
        self.encoder_attention_heads = encoder_attention_heads
        self.encoder_layerdrop = encoder_layerdrop
        self.decoder_layerdrop = decoder_layerdrop
        self.decoder_ffn_dim = decoder_ffn_dim
        self.decoder_layers = decoder_layers
        self.decoder_attention_heads = decoder_attention_heads
        self.max_position_embeddings = max_position_embeddings
        self.init_std = init_std  # Normal(0, this parameter)
        self.activation_function = activation_function

        self.decoder = DecoderConfig(vocab_size=tgt_vocab_size, bos_token_id=eos_token_id)

        self.scale_embedding = scale_embedding  # scale factor will be sqrt(d_model) if True

        # 3 Types of Dropout
        self.attention_dropout = attention_dropout
        self.activation_dropout = activation_dropout
        self.dropout = dropout

    @property
    def num_attention_heads(self) -> int:
        return self.encoder_attention_heads

    @property
    def hidden_size(self) -> int:
        return self.d_model

    def to_dict(self):
        """
        Serializes this instance to a Python dictionary. Override the default `to_dict()` from `PretrainedConfig`.

        Returns:
            :obj:`Dict[str, any]`: Dictionary of all the attributes that make up this configuration instance,
        """
        output = copy.deepcopy(self.__dict__)
        output["decoder"] = self.decoder.to_dict()
        output["model_type"] = self.__class__.model_type
        return output
