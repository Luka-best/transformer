#                🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨
#           This file was automatically generated from src/transformers/models/got_ocr2/modular_got_ocr2.py.
#               Do NOT edit this file manually as any edits will be overwritten by the generation of
#             the file from the modular. If any change should be done, please apply the change to the
#                          modular_got_ocr2.py file directly. One of our CI enforces this.
#                🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨
# coding=utf-8
# Copyright 2024 HuggingFace Inc. team. All rights reserved.
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


from typing import List, Optional, Tuple, Union

from transformers.processing_utils import ImagesKwargs, ProcessingKwargs, ProcessorMixin, TextKwargs, Unpack
from transformers.tokenization_utils_base import PreTokenizedInput, TextInput

from ...image_processing_utils import BatchFeature
from ...image_utils import ImageInput
from ...utils import is_vision_available, logging


if is_vision_available():
    from ...image_utils import load_images


if is_vision_available():
    from ...image_utils import load_images

logger = logging.get_logger(__name__)


class GotOcr2TextKwargs(TextKwargs, total=False):
    format: Optional[bool]


class GotOcr2ImagesKwargs(ImagesKwargs, total=False):
    box: Optional[Union[List, Tuple[float, float], Tuple[float, float, float, float]]]
    color: Optional[str]
    num_image_tokens: Optional[int]
    multi_page: Optional[bool]
    crop_to_patches: Optional[bool]


class GotOcr2ProcessorKwargs(ProcessingKwargs, total=False):
    text_kwargs: GotOcr2TextKwargs
    images_kwargs: GotOcr2ImagesKwargs
    _defaults = {
        "text_kwargs": {
            "padding": False,
            "format": False,
        },
        "images_kwargs": {
            "num_image_tokens": 256,
        },
    }


def load_box_annotation(box, image_size):
    width, height = image_size
    if len(box) == 2:
        box[0] = int(box[0] / width * 1000)
        box[1] = int(box[1] / height * 1000)
    if len(box) == 4:
        box[0] = int(box[0] / width * 1000)
        box[1] = int(box[1] / height * 1000)
        box[2] = int(box[2] / width * 1000)
        box[3] = int(box[3] / height * 1000)

    return box


class GotOcr2Processor(ProcessorMixin):
    r"""
    Constructs a GotOcr2 processor which wraps a [`GotOcr2ImageProcessor`] and
    [`PretrainedTokenizerFast`] tokenizer into a single processor that inherits both the image processor and
    tokenizer functionalities. See the [`~GotOcr2Processor.__call__`] and [`~GotOcr2Processor.decode`] for more information.
    Args:
        image_processor ([`GotOcr2ImageProcessor`], *optional*):
            The image processor is a required input.
        tokenizer ([`PreTrainedTokenizer`, `PreTrainedTokenizerFast`], *optional*):
            The tokenizer is a required input.
        chat_template (`str`, *optional*): A Jinja template which will be used to convert lists of messages
            in a chat into a tokenizable string.
    """

    attributes = ["image_processor", "tokenizer"]
    valid_kwargs = ["chat_template"]
    image_processor_class = "GotOcr2ImageProcessor"
    tokenizer_class = "PreTrainedTokenizerFast"

    def __init__(self, image_processor=None, tokenizer=None, chat_template=None, **kwargs):
        super().__init__(image_processor, tokenizer, chat_template=chat_template)

        self.img_start_token = "<img>"
        self.img_end_token = "</img>"
        self.img_pad_token = "<imgpad>"
        self.system_query = "system\nYou should follow the instructions carefully and explain your answers in detail."

    def __call__(
        self,
        images: Optional[ImageInput] = None,
        text: Optional[Union[TextInput, PreTokenizedInput, List[TextInput], List[PreTokenizedInput]]] = None,
        audio=None,
        videos=None,
        **kwargs: Unpack[GotOcr2ProcessorKwargs],
    ) -> BatchFeature:
        """
        Main method to prepare for the model one or several sequences(s) and image(s). This method forwards the `text`
        and `kwargs` arguments to Qwen2TokenizerFast's [`~Qwen2TokenizerFast.__call__`] if `text` is not `None` to encode
        the text. To prepare the vision inputs, this method forwards the `vision_infos` and `kwrags` arguments to
        Qwen2VLImageProcessor's [`~Qwen2VLImageProcessor.__call__`] if `vision_infos` is not `None`.

        Args:
            images (`PIL.Image.Image`, `np.ndarray`, `torch.Tensor`, `List[PIL.Image.Image]`, `List[np.ndarray]`, `List[torch.Tensor]`):
                The image or batch of images to be prepared. Each image can be a PIL image, NumPy array or PyTorch
                tensor. Both channels-first and channels-last formats are supported.
            text (`str`, `List[str]`, `List[List[str]]`):
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
            [`BatchFeature`]: A [`BatchFeature`] with the following fields:

            - **input_ids** -- List of token ids to be fed to a model. Returned when `text` is not `None`.
            - **attention_mask** -- List of indices specifying which tokens should be attended to by the model (when
              `return_attention_mask=True` or if *"attention_mask"* is in `self.model_input_names` and if `text` is not
              `None`).
            - **pixel_values** -- Pixel values to be fed to a model. Returned when `images` is not `None`.
        """
        if images is None:
            raise ValueError("Images are required to be passed to the processor.")

        output_kwargs = self._merge_kwargs(
            GotOcr2ProcessorKwargs,
            tokenizer_init_kwargs=self.tokenizer.init_kwargs,
            **kwargs,
        )
        format = output_kwargs["text_kwargs"].pop("format", False)
        num_image_tokens = output_kwargs["images_kwargs"].pop("num_image_tokens", 256)
        box = output_kwargs["images_kwargs"].pop("box", [None])
        color = output_kwargs["images_kwargs"].pop("color", None)
        multi_page = output_kwargs["images_kwargs"].pop("multi_page", False)
        crop_to_patches = output_kwargs["images_kwargs"].pop("crop_to_patches", False)

        if not isinstance(box, (list, tuple)):
            raise ValueError("`box` must be a list or tuple in the form [x1, y1, x2, y2].")

        if multi_page or crop_to_patches:
            if multi_page and crop_to_patches:
                raise ValueError("Cannot set both `multi_page` and `crop_to_patches` to `True`.")
            if box[0] is not None or color is not None:
                raise ValueError("Cannot pass `box` or `color` with multi-page inference.")

        if box[0] is not None and color is not None:
            raise ValueError("Both `box` and `color` cannot be set at the same time.")

        if not isinstance(images, (list, tuple)):
            if multi_page:
                logger.warning("Multi-page inference is enabled but only one image is passed.")
            images = [images]
        elif isinstance(images[0], (list, tuple)) and not multi_page:
            raise ValueError("Nested images are only supported with `multi_page` set to `True`.")
        elif not isinstance(images[0], (list, tuple)) and multi_page:
            images = [images]

        if not isinstance(box[0], (list, tuple)):
            box = [box for _ in range(len(images))]
        if not isinstance(color, (list, tuple)):
            color = [color for _ in range(len(images))]
        if len(box) != len(images):
            raise ValueError("The number of `box` must match the number of images.")
        if len(color) != len(images):
            raise ValueError("The number of `color` must match the number of images.")

        # Load images as we need to know the image size
        images = load_images(images)

        if text is None:
            text = []
            for index, (image_group, box_single, color_single) in enumerate(zip(images, box, color)):
                if crop_to_patches:
                    image_group = self.image_processor.crop_image_to_patches(
                        image_group, size=output_kwargs["images_kwargs"].get("size", None)
                    )
                    images[index] = image_group
                num_images = len(image_group) if (multi_page or crop_to_patches) else 1
                if box_single[0] is not None:
                    box_single = load_box_annotation(box_single, image_group.size)
                query = (
                    f"{f'[{color_single}] ' if color_single is not None else ''}"
                    f"{str(box_single) if box_single[0] is not None else ''} "
                    "OCR"
                    f"{' with format' if format else ''}"
                    f"{' across multi pages' if multi_page else ''}"
                    f"{' upon the patch reference' if crop_to_patches else ''}"
                    ": "
                )
                prompt = (
                    "<|im_start|>"
                    + self.system_query
                    + "<|im_end|>"
                    + "<|im_start|>user\n"
                    + self.img_start_token
                    + self.img_pad_token * num_image_tokens * num_images
                    + self.img_end_token
                    + "\n"
                    + query
                    + "<|im_end|><|im_start|>assistant\n"
                )
                text.append(prompt)

        text_inputs = self.tokenizer(text, **output_kwargs["text_kwargs"])
        if multi_page or crop_to_patches:
            # flatten images
            images = [image for image_group in images for image in image_group]
        image_inputs = self.image_processor(images=images, **output_kwargs["images_kwargs"])

        return BatchFeature(data={**text_inputs, **image_inputs})

    def batch_decode(self, *args, **kwargs):
        """
        This method forwards all its arguments to Qwen2TokenizerFast's [`~PreTrainedTokenizer.batch_decode`]. Please
        refer to the docstring of this method for more information.
        """
        return self.tokenizer.batch_decode(*args, **kwargs)

    def decode(self, *args, **kwargs):
        """
        This method forwards all its arguments to Qwen2TokenizerFast's [`~PreTrainedTokenizer.decode`]. Please refer to
        the docstring of this method for more information.
        """
        return self.tokenizer.decode(*args, **kwargs)

    @property
    def model_input_names(self):
        tokenizer_input_names = self.tokenizer.model_input_names
        image_processor_input_names = self.image_processor.model_input_names
        return list(dict.fromkeys(tokenizer_input_names + image_processor_input_names))
