# coding=utf-8
# Copyright 2023 The Kakao Enterprise Authors, the MMS-TTS Authors and the HuggingFace Inc. team. All rights reserved.
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
"""Tokenization class for VITS."""


import json
import os
import re
import subprocess
from typing import Any, Dict, List, Optional, Tuple, Union

from ...tokenization_utils import PreTrainedTokenizer
from ...utils import is_phonemizer_available, logging


if is_phonemizer_available():
    import phonemizer


logger = logging.get_logger(__name__)

VOCAB_FILES_NAMES = {"vocab_file": "vocab.json"}

PRETRAINED_VOCAB_FILES_MAP = {
    "vocab_file": {
        "sanchit-gandhi/mms-tts-eng": "https://huggingface.co/sanchit-gandhi/mms-tts-eng/resolve/main/vocab.json",
    }
}

PRETRAINED_POSITIONAL_EMBEDDINGS_SIZES = {
    # This model does not have a maximum input length.
    "sanchit-gandhi/mms-tts-eng": 4096,
}


def has_non_roman_characters(input_string):
    # Find any character outside the ASCII range
    non_roman_pattern = re.compile(r"[^\x00-\x7F]")

    # Search the input string for non-Roman characters
    match = non_roman_pattern.search(input_string)
    has_non_roman = match is not None
    return has_non_roman


def uromanize(input_string, uroman_path, language=None, chart=False):
    """Convert non-Roman strings to Roman using the `uroman` perl package."""
    script_path = os.path.join(uroman_path, "bin/uroman.pl")

    command = ["perl", script_path]

    # Add language flag if specified
    if language:
        command.extend(["-l", language])

    # Add chart flag if specified
    if chart:
        command.append("--chart")

    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Execute the perl command
    stdout, stderr = process.communicate(input=input_string.encode())

    if process.returncode != 0:
        raise ValueError(f"Error {process.returncode}: {stderr.decode()}")

    # Return the output as a string and skip the new-line character at the end
    return stdout.decode()[:-1]


class VitsTokenizer(PreTrainedTokenizer):
    """
    Construct a VITS tokenizer. Also supports MMS-TTS.

    This tokenizer inherits from [`PreTrainedTokenizer`] which contains most of the main methods. Users should refer to
    this superclass for more information regarding those methods.

    Args:
        vocab_file (`str`):
            Path to the vocabulary file.
        language (`str`, *optional*):
            Language identifier.
        add_blank (`bool`, *optional*, defaults to `True`):
            Whether to insert token id 0 in between the other tokens.
        phonemize (`bool`, *optional*, defaults to `True`):
            Whether to convert the input text into phonemes.
        is_uroman (`bool`, *optional*, defaults to `False`):
            Whether the `uroman` Romanizer needs to be applied to the input text prior to tokenizing.
    """

    vocab_files_names = VOCAB_FILES_NAMES
    pretrained_vocab_files_map = PRETRAINED_VOCAB_FILES_MAP
    max_model_input_sizes = PRETRAINED_POSITIONAL_EMBEDDINGS_SIZES
    model_input_names = ["input_ids", "attention_mask"]

    def __init__(
        self,
        vocab_file,
        pad_token="<pad>",
        unk_token="<unk>",
        language=None,
        add_blank=True,
        phonemize=True,
        is_uroman=False,
        **kwargs,
    ) -> None:
        super().__init__(
            pad_token=pad_token,
            unk_token=unk_token,
            language=language,
            add_blank=add_blank,
            phonemize=phonemize,
            is_uroman=is_uroman,
            **kwargs,
        )

        with open(vocab_file, encoding="utf-8") as vocab_handle:
            self.encoder = json.load(vocab_handle)

        self.decoder = {v: k for k, v in self.encoder.items()}
        self.language = language
        self.add_blank = add_blank
        self.phonemize = phonemize

        self.is_uroman = is_uroman

    @property
    def vocab_size(self):
        return len(self.encoder)

    def get_vocab(self):
        vocab = {self.convert_ids_to_tokens(i): i for i in range(self.vocab_size)}
        return vocab

    def normalize_text(self, input_string):
        """Lowercase the input string, respecting any special token ids that may be part or entirely upper-cased."""
        all_vocabulary = list(self.encoder.keys()) + list(self.added_tokens_encoder.keys())
        filtered_text = ""

        i = 0
        while i < len(input_string):
            found_match = False
            for word in all_vocabulary:
                if input_string[i : i + len(word)] == word:
                    filtered_text += word
                    i += len(word)
                    found_match = True
                    break

            if not found_match:
                filtered_text += input_string[i].lower()
                i += 1

        return filtered_text

    def _preprocess_char(self, text):
        """Special treatment of characters in certain languages"""
        if self.language == "ron":
            text = text.replace("ț", "ţ")
        return text

    def prepare_for_tokenization(
        self, text: str, is_split_into_words: bool = False, normalize: bool = False, uroman_path: str = None, **kwargs
    ) -> Tuple[str, Dict[str, Any]]:
        if normalize:
            # normalise for casing
            text = self.normalize_text(text)

        filtered_text = self._preprocess_char(text)

        if self.is_uroman and uroman_path is not None:
            filtered_text = uromanize(filtered_text, uroman_path)

        if has_non_roman_characters(filtered_text) and self.is_uroman:
            logger.warning(
                "Text to the tokenizer contains non-Roman characters. Ensure the `uroman` Romanizer is "
                "applied to the text prior to passing it to the tokenizer. First clone the uroman package: "
                "`git clone https://github.com/isi-nlp/uroman.git`. Then, pass the argument `uroman_path` to the tokenizer, "
                "which specifies the path where the `uroman` package is located."
            )

        if self.phonemize:
            if not is_phonemizer_available():
                raise ImportError("Please install the `phonemizer` Python package to use this tokenizer.")

            filtered_text = phonemizer.phonemize(
                filtered_text,
                language="en-us",
                backend="espeak",
                strip=True,
                preserve_punctuation=True,
                with_stress=True,
            )
            filtered_text = re.sub(r"\s+", " ", filtered_text)
        elif normalize:
            # strip any chars outside of the vocab (punctuation)
            filtered_text = "".join(list(filter(lambda char: char in self.encoder, filtered_text))).strip()

        return filtered_text, kwargs

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize a string by inserting the `<pad>` token at the boundary between adjacent characters."""
        tokens = list(text)

        if self.add_blank:
            interspersed = [self._convert_id_to_token(0)] * (len(tokens) * 2 + 1)
            interspersed[1::2] = tokens
            tokens = interspersed

        return tokens

    def convert_tokens_to_string(self, tokens: List[str]) -> str:
        if self.add_blank and len(tokens) > 1:
            tokens = tokens[1::2]
        return "".join(tokens)

    def _convert_token_to_id(self, token):
        """Converts a token (str) in an id using the vocab."""
        return self.encoder.get(token, self.encoder.get(self.unk_token))

    def _convert_id_to_token(self, index):
        """Converts an index (integer) in a token (str) using the vocab."""
        return self.decoder.get(index)

    def save_vocabulary(self, save_directory: str, filename_prefix: Optional[str] = None) -> Union[Tuple[str], None]:
        if not os.path.isdir(save_directory):
            logger.error(f"Vocabulary path ({save_directory}) should be a directory")
            return

        vocab_file = os.path.join(
            save_directory, (filename_prefix + "-" if filename_prefix else "") + VOCAB_FILES_NAMES["vocab_file"]
        )

        with open(vocab_file, "w", encoding="utf-8") as f:
            f.write(json.dumps(self.encoder, indent=2, sort_keys=True, ensure_ascii=False) + "\n")

        return (vocab_file,)
