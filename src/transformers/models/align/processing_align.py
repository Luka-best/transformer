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
Image/Text processor class for ALIGN
"""

from typing import List, Union

from ...image_utils import ImageInput
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


class AlignProcessorKwargs(ProcessingKwargs, total=False):
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
            "padding": "max_length",
            "max_length": 64,
        },
    }


class AlignProcessor(ProcessorMixin):
    r"""
    Constructs an ALIGN processor which wraps [`EfficientNetImageProcessor`] and
    [`BertTokenizer`]/[`BertTokenizerFast`] into a single processor that interits both the image processor and
    tokenizer functionalities. See the [`~AlignProcessor.__call__`] and [`~OwlViTProcessor.decode`] for more
    information.
    The preferred way of passing kwargs is as a dictionary per modality, see usage example below.
        ```python
        from transformers import AlignProcessor
        from PIL import Image
        model_id = "kakaobrain/align-base"
        processor = AlignProcessor.from_pretrained(model_id)

        # Define the kwargs for each modality
        common_kwargs = {"return_tensors": "pt"}
        images_kwargs = {"crop_size": {"height": 224, "width": 224}}
        text_kwargs = {"padding": "do_not_pad"}

        # Combine them into a single dictionary

        all_kwargs = {
        "images_kwargs": images_kwargs,
        "text_kwargs": text_kwargs,
        "common_kwargs": common_kwargs
        }

        processor(images=your_pil_image, text=["What is that?"], **all_kwargs)

        # passing directly any number of kwargs is also supported, but not recommended

        processor(images=your_pil_image, text=["What is that?"], padding="do_not_pad)
        ```

    Args:
        image_processor ([`EfficientNetImageProcessor`]):
            The image processor is a required input.
        tokenizer ([`BertTokenizer`, `BertTokenizerFast`]):
            The tokenizer is a required input.

    """

    attributes = ["image_processor", "tokenizer"]
    image_processor_class = "EfficientNetImageProcessor"
    tokenizer_class = ("BertTokenizer", "BertTokenizerFast")

    def __init__(self, image_processor, tokenizer):
        super().__init__(image_processor, tokenizer)

    def __call__(
        self,
        text: Union[TextInput, PreTokenizedInput, List[TextInput], List[PreTokenizedInput]] = None,
        images: ImageInput = None,
        audio=None,
        videos=None,
        text_kwargs: AlignProcessorKwargs.text_kwargs = None,
        images_kwargs: AlignProcessorKwargs.images_kwargs = None,
        common_kwargs: AlignProcessorKwargs.common_kwargs = None,
        **kwargs: AlignProcessorKwargs,
    ) -> BatchEncoding:
        """
        Main method to prepare text(s) and image(s) to be fed as input to the model. This method forwards the `text`
        arguments to BertTokenizerFast's [`~BertTokenizerFast.__call__`] if `text` is not `None` to encode
        the text. To prepare the image(s), this method forwards the `images` arguments to
        EfficientNetImageProcessor's [`~EfficientNetImageProcessor.__call__`] if `images` is not `None`. Please refer
        to the doctsring of the above two methods for more information.

        Args:
            text (`str`, `List[str]`):
                The sequence or batch of sequences to be encoded. Each sequence can be a string or a list of strings
                (pretokenized string). If the sequences are provided as list of strings (pretokenized), you must set
                `is_split_into_words=True` (to lift the ambiguity with a batch of sequences).
            images (`PIL.Image.Image`, `np.ndarray`, `torch.Tensor`, `List[PIL.Image.Image]`, `List[np.ndarray]`, `List[torch.Tensor]`):
                The image or batch of images to be prepared. Each image can be a PIL image, NumPy array or PyTorch
                tensor. Both channels-first and channels-last formats are supported.
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
        default_text_kwargs = AlignProcessorKwargs._defaults.get("text_kwargs", {}).copy()

        # then override with tokenizer-level arguments passed
        default_text_kwargs.update(
            {k: v for k, v in self.tokenizer.init_kwargs.items() if k in AlignProcessorKwargs.text_kwargs}
        )
        # then get passed per-modality dictionaries if they exist
        text_kwargs = {**default_text_kwargs, **text_kwargs, **kwargs.pop("text_kwargs", {})}
        images_kwargs.update(kwargs.pop("images_kwargs", {}))
        common_kwargs.update(kwargs.pop("common_kwargs", {}))

        # then merge kwargs by name
        for text_key in AlignProcessorKwargs.text_kwargs.keys():
            text_kwarg_value = kwargs.pop(text_key, None)
            if text_kwarg_value is not None:
                text_kwargs[text_key] = text_kwarg_value

        for images_key in AlignProcessorKwargs.images_kwargs.keys():
            images_kwarg_value = kwargs.pop(images_key, None)
            if images_kwarg_value is not None:
                images_kwargs[images_key] = images_kwarg_value
        # if something remains in kwargs, it belongs to common
        common_kwargs.update(kwargs)

        # all modality-specific kwargs are updated with common kwargs
        text_kwargs.update(common_kwargs)
        images_kwargs.update(common_kwargs)

        # then, we can pass correct kwargs to each processor
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
        This method forwards all its arguments to BertTokenizerFast's [`~PreTrainedTokenizer.batch_decode`]. Please
        refer to the docstring of this method for more information.
        """
        return self.tokenizer.batch_decode(*args, **kwargs)

    def decode(self, *args, **kwargs):
        """
        This method forwards all its arguments to BertTokenizerFast's [`~PreTrainedTokenizer.decode`]. Please refer to
        the docstring of this method for more information.
        """
        return self.tokenizer.decode(*args, **kwargs)

    @property
    def model_input_names(self):
        tokenizer_input_names = self.tokenizer.model_input_names
        image_processor_input_names = self.image_processor.model_input_names
        return list(dict.fromkeys(tokenizer_input_names + image_processor_input_names))
