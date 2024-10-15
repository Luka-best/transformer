# Copyright 2024 The HuggingFace Team. All rights reserved.
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

import unittest

from transformers import MODEL_FOR_IMAGE_TEXT_TO_TEXT_MAPPING, is_vision_available
from transformers.pipelines import ImageTextToTextPipeline, pipeline
from transformers.testing_utils import (
    is_pipeline_test,
    require_torch,
    require_vision,
    slow,
)

from .test_pipelines_common import ANY


if is_vision_available():
    from PIL import Image
else:

    class Image:
        @staticmethod
        def open(*args, **kwargs):
            pass


@is_pipeline_test
@require_vision
class ImageTextToTextPipelineTests(unittest.TestCase):
    model_mapping = MODEL_FOR_IMAGE_TEXT_TO_TEXT_MAPPING

    def get_test_pipeline(self, model, tokenizer, processor, torch_dtype="float32"):
        pipe = ImageTextToTextPipeline(
            model=model, tokenizer=tokenizer, image_processor=processor, torch_dtype=torch_dtype
        )
        image_token = processor.image_token if hasattr(processor, "image_token") else "<image>"
        examples = {
            "images": [
                Image.open("./tests/fixtures/tests_samples/COCO/000000039769.png"),
                "./tests/fixtures/tests_samples/COCO/000000039769.png",
            ],
            "text": [f"{image_token} This is a ", f"{image_token} Here I see a "],
        }
        return pipe, examples

    def run_pipeline_test(self, pipe, examples):
        outputs = pipe(examples.get("images"), text=examples.get("text"), max_new_tokens=20)
        self.assertEqual(
            outputs,
            [
                [{"input_text": ANY(str), "generated_text": ANY(str)}],
                [{"input_text": ANY(str), "generated_text": ANY(str)}],
            ],
        )

    @require_torch
    def test_small_model_pt_token(self):
        pipe = pipeline("image-text-to-text", model="llava-hf/llava-interleave-qwen-0.5b-hf")
        image = "./tests/fixtures/tests_samples/COCO/000000039769.png"
        text = "<image> What this is? Assistant: This is"

        outputs = pipe(image, text=text, max_new_tokens=20)
        self.assertEqual(
            outputs,
            [
                [
                    {
                        "input_text": "<image> What this is? Assistant: This is",
                        "generated_text": "<image> What this is? Assistant: This is a photo of two cats lying on a pink blanket. The cats are sleeping and appear to be comfortable",
                    }
                ]
            ],
        )

        outputs = pipe([image, image], text=[text, text], max_new_tokens=20)
        self.assertEqual(
            outputs,
            [
                [
                    {
                        "input_text": "<image> What this is? Assistant: This is",
                        "generated_text": "<image> What this is? Assistant: This is a photo of two cats lying on a pink blanket. The cats are sleeping and appear to be comfortable",
                    }
                ],
                [
                    {
                        "input_text": "<image> What this is? Assistant: This is",
                        "generated_text": "<image> What this is? Assistant: This is a photo of two cats lying on a pink blanket. The cats are sleeping and appear to be comfortable",
                    }
                ],
            ],
        )

    @require_torch
    def test_consistent_batching_behaviour(self):
        pipe = pipeline("image-text-to-text", model="microsoft/kosmos-2-patch14-224")
        image = "./tests/fixtures/tests_samples/COCO/000000039769.png"
        prompt = "a photo of"

        outputs = pipe([image, image], text=[prompt, prompt], max_new_tokens=20)
        outputs_batched = pipe([image, image], text=[prompt, prompt], max_new_tokens=20, batch_size=2)
        self.assertEqual(outputs, outputs_batched)

    @slow
    @require_torch
    def test_model_pt_chat_template(self):
        pipe = pipeline("image-text-to-text", model="llava-hf/llava-interleave-qwen-0.5b-hf")
        image_ny = "https://cdn.britannica.com/61/93061-050-99147DCE/Statue-of-Liberty-Island-New-York-Bay.jpg"
        image_chicago = "https://cdn.britannica.com/59/94459-050-DBA42467/Skyline-Chicago.jpg"
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What’s the difference between these two images?"},
                    {"type": "image"},
                    {"type": "image"},
                ],
            }
        ]
        outputs = pipe([image_ny, image_chicago], text=messages, max_new_tokens=20)
        self.assertEqual(
            outputs,
            [
                {
                    "input_text": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "What’s the difference between these two images?"},
                                {"type": "image"},
                                {"type": "image"},
                            ],
                        }
                    ],
                    "generated_text": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "What’s the difference between these two images?"},
                                {"type": "image"},
                                {"type": "image"},
                            ],
                        },
                        {
                            "role": "assistant",
                            "content": "The first image shows a statue of the Statue of Liberty in the foreground, while the second image shows",
                        },
                    ],
                }
            ],
        )

    @slow
    @require_torch
    def test_model_pt_chat_template_continue_final_message(self):
        pipe = pipeline("image-text-to-text", model="llava-hf/llava-interleave-qwen-0.5b-hf")
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "image": "https://qianwen-res.oss-cn-beijing.aliyuncs.com/Qwen-VL/assets/demo.jpeg",
                    },
                    {"type": "text", "text": "Describe this image."},
                ],
            },
            {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": "There is a dog and"},
                ],
            },
        ]
        outputs = pipe(text=messages, max_new_tokens=20)
        self.assertEqual(
            outputs,
            [
                {
                    "input_text": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "image": "https://qianwen-res.oss-cn-beijing.aliyuncs.com/Qwen-VL/assets/demo.jpeg",
                                },
                                {"type": "text", "text": "Describe this image."},
                            ],
                        },
                        {"role": "assistant", "content": [{"type": "text", "text": "There is a dog and"}]},
                    ],
                    "generated_text": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "image": "https://qianwen-res.oss-cn-beijing.aliyuncs.com/Qwen-VL/assets/demo.jpeg",
                                },
                                {"type": "text", "text": "Describe this image."},
                            ],
                        },
                        {
                            "role": "assistant",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "There is a dog and a person in the image. The dog is sitting on the sand, and the person is sitting on",
                                }
                            ],
                        },
                    ],
                }
            ],
        )

    @slow
    @require_torch
    def test_model_pt_chat_template_new_text(self):
        pipe = pipeline("image-text-to-text", model="llava-hf/llava-interleave-qwen-0.5b-hf")
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "image": "https://qianwen-res.oss-cn-beijing.aliyuncs.com/Qwen-VL/assets/demo.jpeg",
                    },
                    {"type": "text", "text": "Describe this image."},
                ],
            }
        ]
        outputs = pipe(text=messages, max_new_tokens=20, return_full_text=False)
        self.assertEqual(
            outputs,
            [
                {
                    "input_text": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "image": "https://qianwen-res.oss-cn-beijing.aliyuncs.com/Qwen-VL/assets/demo.jpeg",
                                },
                                {"type": "text", "text": "Describe this image."},
                            ],
                        }
                    ],
                    "generated_text": "In the image, a woman is sitting on the sandy beach, her legs crossed in a relaxed manner",
                }
            ],
        )