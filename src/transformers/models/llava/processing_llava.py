# coding=utf-8
# Copyright 2023 The HuggingFace Inc. team.
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
"""
Processor class for LlavaLlama. Largely copy of Blip2Processor with addition of CLIPVisionModel.
"""

from typing import List, Optional, Union

import torch

from ...image_processing_utils import BatchFeature
from ...image_utils import ImageInput
from ...processing_utils import ProcessorMixin
from ...tokenization_utils_base import PaddingStrategy, TextInput, TruncationStrategy
from ...utils import TensorType
from ..clip import CLIPVisionModel


class LlavaProcessor(ProcessorMixin):
    r"""
    Constructs an LLava processor which wraps a CLIP image processor, CLIP vision model  and a LLaMa/T5 tokenizer into a single
    processor.

    [`LlavaProcessor`] offers all the functionalities of [`CLIPImageProcessor`] and [`AutoTokenizer`]. See the
    docstring of [`~BlipProcessor.__call__`] and [`~BlipProcessor.decode`] for more information.

    Args:
        image_processor (`CLIPProcessor`):
            An instance of [`CLIPProcessor`]. The image processor is a required input.
        tokenizer (`AutoTokenizer`):
            An instance of ['PreTrainedTokenizer`]. The tokenizer is a required input.
        vision_model (`CLIPVisionModel`):
            An instance of ['CLIPVisionModel`]. The Vision Model is a required input.
    """
    attributes = ["image_processor", "tokenizer"]
    tokenizer_class = "AutoTokenizer"
    image_processor_class = "CLIPImageProcessor"

    def __init__(self, image_processor, tokenizer, vision_model):
        super().__init__(image_processor, tokenizer)

        self.vision_model = vision_model

    def __call__(
        self,
        images: ImageInput = None,
        text: Union[TextInput, List[TextInput]] = None,
        add_special_tokens: bool = True,
        padding: Union[bool, str, PaddingStrategy] = False,
        truncation: Union[bool, str, TruncationStrategy] = None,
        max_length: Optional[int] = None,
        stride: int = 0,
        pad_to_multiple_of: Optional[int] = None,
        return_attention_mask: Optional[bool] = None,
        return_overflowing_tokens: bool = False,
        return_special_tokens_mask: bool = False,
        return_offsets_mapping: bool = False,
        return_token_type_ids: bool = False,
        return_length: bool = False,
        verbose: bool = True,
        return_tensors: Optional[Union[str, TensorType]] = None,
        **kwargs,
    ) -> BatchFeature:
        """
        This method uses [`CLIPProcessor.__call__`] method to prepare image(s) for the model, and
        [`LlamaTokenizer.__call__`] to prepare text for the model.

        Please refer to the docstring of the above two methods for more information.
        """
        # Model Constants
        IMAGE_TOKEN_INDEX = 200
        DEFAULT_IMAGE_TOKEN = "<image>"

        if images is None and text is None:
            raise ValueError("You have to specify at least images or text.")

        encoding = BatchFeature()
        dummy = {}
        if text is not None:
            text = DEFAULT_IMAGE_TOKEN + "\n" + text
            prompt_chunks = [
                self.tokenizer(
                    chunk,
                    add_special_tokens=add_special_tokens,
                    padding=padding,
                    truncation=truncation,
                    max_length=max_length,
                    stride=stride,
                    pad_to_multiple_of=pad_to_multiple_of,
                    return_attention_mask=return_attention_mask,
                    return_overflowing_tokens=return_overflowing_tokens,
                    return_special_tokens_mask=return_special_tokens_mask,
                    return_offsets_mapping=return_offsets_mapping,
                    return_token_type_ids=return_token_type_ids,
                    return_length=return_length,
                    verbose=verbose,
                    # return_tensors=return_tensors,
                ).input_ids
                for chunk in text.split("<image>")
            ]

            def insert_separator(X, sep):
                return [ele for sublist in zip(X, [sep] * len(X)) for ele in sublist][:-1]

            input_ids = []
            offset = 0
            if (
                len(prompt_chunks) > 0
                and len(prompt_chunks[0]) > 0
                and prompt_chunks[0][0] == self.tokenizer.bos_token_id
            ):
                offset = 1
                input_ids.append(prompt_chunks[0][0])

            for x in insert_separator(prompt_chunks, [IMAGE_TOKEN_INDEX] * (offset + 1)):
                input_ids.extend(x[offset:])

            if return_tensors == "pt":
                input_ids = torch.tensor(input_ids, dtype=torch.long)
            dummy["input_ids"] = input_ids.unsqueeze(0)
            encoding.update(dummy)

        if images is not None:
            image_encoding = self.image_processor.preprocess(images, return_tensors=return_tensors)
            vision_encoding = self.vision_model(image_encoding["pixel_values"], output_hidden_states=True)
            image_features = vision_encoding.hidden_states[-2]
            image_features = image_features[:, 1:]

            dummy["pixel_values"] = image_features
            encoding.update(dummy)
        return encoding

    def feature_select(image_forward_outs):
        image_features = image_forward_outs.hidden_states[-2]
        image_features = image_features[:, 1:]
        return image_features

    # Copied from transformers.models.blip.processing_blip.BlipProcessor.batch_decode with LlamaTokenizerFast->PreTrainedTokenizer
    def batch_decode(self, *args, **kwargs):
        """
        This method forwards all its arguments to BertTokenizerFast's [`~PreTrainedTokenizer.batch_decode`]. Please
        refer to the docstring of this method for more information.
        """
        return self.tokenizer.batch_decode(*args, **kwargs)

    # Copied from transformers.models.blip.processing_blip.BlipProcessor.decode with LlamaTokenizerFast->PreTrainedTokenizer
    def decode(self, *args, **kwargs):
        """
        This method forwards all its arguments to BertTokenizerFast's [`~PreTrainedTokenizer.decode`]. Please refer to
        the docstring of this method for more information.
        """
        return self.tokenizer.decode(*args, **kwargs)

    @property
    # Copied from transformers.models.blip.processing_blip.BlipProcessor.model_input_names
    def model_input_names(self):
        tokenizer_input_names = self.tokenizer.model_input_names
        image_processor_input_names = self.image_processor.model_input_names
        return list(dict.fromkeys(tokenizer_input_names + image_processor_input_names))

    # overwrite to load the Q-Former tokenizer from a separate folder
    @classmethod
    def from_pretrained(cls, pretrained_model_name_or_path, **kwargs):
        vision_model = CLIPVisionModel.from_pretrained("openai/clip-vit-large-patch14")
        args = cls._get_arguments_from_pretrained(pretrained_model_name_or_path, **kwargs)
        args.append(vision_model)
        return cls(*args)
