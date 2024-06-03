# coding=utf-8
# Copyright 2022 WenXiang ZhongzhiCheng LedellWu LiuGuang BoWenZhang The HuggingFace Inc. team. All rights reserved.
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
Image/Text processor class for AltCLIP
"""

import warnings
from typing import List, Union

from ...image_utils import ChannelDimension, ImageInput
from ...processing_utils import (
    CommonKwargs,
    ImagesKwargs,
    ProcessingKwargs,
    ProcessorMixin,
    TextKwargs,
)
from ...tokenization_utils_base import BatchEncoding, PreTokenizedInput, TextInput
from ...utils import is_torch_available, is_vision_available


# TODO (@molbap) This is a bother, forward references from TypedDict are resolved and need this to work
if is_vision_available():
    import PIL  # noqa: F401
if is_torch_available():
    import torch  # noqa: F401


class AltClipProcessorKwargs(ProcessingKwargs, total=False):
    """
    Inherits from `ProcessingKwargs` to provide:
        1) Additional keys that this model requires to process inputs.
        2) Default values for extra keys.
    New keys have to be defined as follows to ensure type hinting is done correctly.

    ```python
    common_kwargs: CommonKwargs = {
            **CommonKwargs.__annotations__,
        }
        text_kwargs: TextKwargs = {
            **TextKwargs.__annotations__,
            "a_new_text_boolean_key": Optional[bool],
        }
        images_kwargs: ImagesKwargs = {
            **ImagesKwargs.__annotations__,
            "a_new_image_processing_key": Optional[int]
        }
    ```

    """

    common_kwargs: CommonKwargs = {
        **CommonKwargs.__annotations__,
    }
    text_kwargs: TextKwargs = {
        **TextKwargs.__annotations__,
    }
    images_kwargs: ImagesKwargs = {
        **ImagesKwargs.__annotations__,
    }

    _defaults = {
        "text_kwargs": {
            "add_special_tokens": True,
            "padding": False,
            "stride": 0,
            "is_split_into_words": False,
            "return_overflowing_tokens": False,
            "return_special_tokens_mask": False,
            "return_offsets_mapping": False,
            "return_length": False,
            "verbose": True,
        },
        "images_kwargs": {
            "data_format": ChannelDimension.FIRST,
        },
    }


class AltCLIPProcessor(ProcessorMixin):
    r"""
    Constructs a AltCLIP processor which wraps a CLIP image processor and a XLM-Roberta tokenizer into a single
    processor.

    [`AltCLIPProcessor`] offers all the functionalities of [`CLIPImageProcessor`] and [`XLMRobertaTokenizerFast`]. See
    the [`~AltCLIPProcessor.__call__`] and [`~AltCLIPProcessor.decode`] for more information.

    Args:
        image_processor ([`CLIPImageProcessor`], *optional*):
            The image processor is a required input.
        tokenizer ([`XLMRobertaTokenizerFast`], *optional*):
            The tokenizer is a required input.
        feature_extractor ([`CLIPFeatureExtractor`], *optional*):
            The feature extractor is a deprecated input.
    """

    attributes = ["image_processor", "tokenizer"]
    image_processor_class = "CLIPImageProcessor"
    tokenizer_class = ("XLMRobertaTokenizer", "XLMRobertaTokenizerFast")

    def __init__(self, image_processor=None, tokenizer=None, feature_extractor=None):
        if "feature_extractor":
            warnings.warn(
                "The `feature_extractor` argument is deprecated and will be removed in v5, use `image_processor`"
                " instead.",
                FutureWarning,
            )
        image_processor = image_processor if image_processor is not None else feature_extractor
        if image_processor is None:
            raise ValueError("You need to specify an `image_processor`.")
        if tokenizer is None:
            raise ValueError("You need to specify a `tokenizer`.")

        super().__init__(image_processor, tokenizer)

    def __call__(
        self,
        images: ImageInput = None,
        text: Union[TextInput, PreTokenizedInput, List[TextInput], List[PreTokenizedInput]] = None,
        audio=None,
        videos=None,
        text_kwargs: AltClipProcessorKwargs.text_kwargs = None,
        images_kwargs: AltClipProcessorKwargs.images_kwargs = None,
        common_kwargs: AltClipProcessorKwargs.common_kwargs = None,
        **kwargs: AltClipProcessorKwargs,
    ) -> BatchEncoding:
        """
        Main method to prepare for the model one or several sequences(s) and image(s). This method forwards the `text`
        and `kwargs` arguments to XLMRobertaTokenizerFast's [`~XLMRobertaTokenizerFast.__call__`] if `text` is not
        `None` to encode the text. To prepare the image(s), this method forwards the `images` and `kwrags` arguments to
        CLIPImageProcessor's [`~CLIPImageProcessor.__call__`] if `images` is not `None`. Please refer to the doctsring
        of the above two methods for more information.

        Args:

            images (`ImageInput`):
                The image or batch of images to be prepared. Each image can be a PIL image, NumPy array or PyTorch
                tensor. Both channels-first and channels-last formats are supported.
            text (`TextInput`, `PreTokenizedInput`, `List[TextInput]`, `List[PreTokenizedInput]`):
                The sequence or batch of sequences to be encoded. Each sequence can be a string or a list of strings
                (pretokenized string). If the sequences are provided as list of strings (pretokenized), you must set
                `is_split_into_words=True` (to lift the ambiguity with a batch of sequences).
            return_tensors (`str` or [`~utils.TensorType`], *optional*):
                If set, will return tensors of a particular framework. Acceptable values are:
                    - `'tf'`: Return TensorFlow `tf.constant` objects.
                    - `'pt'`: Return PyTorch `torch.Tensor` objects.
                    - `'np'`: Return NumPy `np.ndarray` objects.
                    - `'jax'`: Return JAX `jnp.ndarray` objects.
        Returns:
            [`BatchEncoding`]: A [`BatchEncoding`] with the following fields:

            - **input_ids** -- List of token ids to be fed to a model. Returned when `text` is not `None`.
            - **attention_mask** -- List of indices specifying which tokens should be attended to by the model (when
              `return_attention_mask=True` or if *"attention_mask"* is in `self.model_input_names` and if `text` is not
              `None`).
            - **pixel_values** -- Pixel values to be fed to a model. Returned when `images` is not `None`.
        """

        if text is None and images is None:
            raise ValueError("You must specify either text or images.")

        # set kwargs as empty dicts to avoid default mutable
        if text_kwargs is None:
            text_kwargs = {}
        if images_kwargs is None:
            images_kwargs = {}
        if common_kwargs is None:
            common_kwargs = {}
        # Init with default values if they exist
        default_text_kwargs = AltClipProcessorKwargs._defaults.get("text_kwargs", {}).copy()
        default_images_kwargs = AltClipProcessorKwargs._defaults.get("images_kwargs", {}).copy()

        # then override with tokenizer-level arguments passed
        default_text_kwargs.update(
            {k: v for k, v in self.tokenizer.init_kwargs.items() if k in AltClipProcessorKwargs.text_kwargs}
        )
        # then get passed per-modality dictionaries if they exist
        text_kwargs = {**default_text_kwargs, **text_kwargs, **kwargs.pop("text_kwargs", {})}
        images_kwargs = {**default_images_kwargs, **images_kwargs, **kwargs.pop("images_kwargs", {})}
        common_kwargs.update(kwargs.pop("common_kwargs", {}))

        # then merge kwargs by name
        for text_key in AltClipProcessorKwargs.text_kwargs.keys():
            text_kwarg_value = kwargs.pop(text_key, None)
            if text_kwarg_value is not None:
                text_kwargs[text_key] = text_kwarg_value

        for images_key in AltClipProcessorKwargs.images_kwargs.keys():
            images_kwarg_value = kwargs.pop(images_key, None)
            if images_kwarg_value is not None:
                images_kwargs[images_key] = images_kwarg_value
        # if something remains in kwargs, it belongs to common
        common_kwargs.update(kwargs)

        # all modality-specific kwargs are updated with common kwargs
        text_kwargs.update(common_kwargs)
        images_kwargs.update(common_kwargs)

        if text is not None:
            encoding = self.tokenizer(text, **text_kwargs)
        if images is not None:
            image_features = self.image_processor(images, **images_kwargs)

        # BC for explicit return_tensors
        if "return_tensors" in common_kwargs:
            return_tensors = common_kwargs.pop("return_tensors", None)

        if text is not None and images is not None:
            encoding["pixel_values"] = image_features.pixel_values
            return encoding
        elif text is not None:
            return encoding
        else:
            return BatchEncoding(data=dict(**image_features), tensor_type=return_tensors)

    def batch_decode(self, *args, **kwargs):
        """
        This method forwards all its arguments to XLMRobertaTokenizerFast's [`~PreTrainedTokenizer.batch_decode`].
        Please refer to the docstring of this method for more information.
        """
        return self.tokenizer.batch_decode(*args, **kwargs)

    def decode(self, *args, **kwargs):
        """
        This method forwards all its arguments to XLMRobertaTokenizerFast's [`~PreTrainedTokenizer.decode`]. Please
        refer to the docstring of this method for more information.
        """
        return self.tokenizer.decode(*args, **kwargs)

    @property
    def model_input_names(self):
        tokenizer_input_names = self.tokenizer.model_input_names
        image_processor_input_names = self.image_processor.model_input_names
        return list(dict.fromkeys(tokenizer_input_names + image_processor_input_names))
