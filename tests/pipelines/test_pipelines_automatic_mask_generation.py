# Copyright 2023 The HuggingFace Team. All rights reserved.
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

import hashlib
import unittest
from typing import Dict

import numpy as np

from transformers import (
    MODEL_FOR_AUTOMATIC_MASK_GENERATION_MAPPING,
    AutoImageProcessor,
    SamForMaskGeneration,
    is_vision_available,
    pipeline,
)
from transformers.pipelines import AutomaticMaskGenerationPipeline
from transformers.testing_utils import (
    is_pipeline_test,
    nested_simplify,
    require_tf,
    require_torch,
    require_vision,
    slow,
)


if is_vision_available():
    from PIL import Image
else:

    class Image:
        @staticmethod
        def open(*args, **kwargs):
            pass


def hashimage(image: Image) -> str:
    m = hashlib.md5(image.tobytes())
    return m.hexdigest()[:10]


def mask_to_test_readable(mask: Image) -> Dict:
    npimg = np.array(mask)
    white_pixels = (npimg == 255).sum()
    shape = npimg.shape
    return {"hash": hashimage(mask), "white_pixels": white_pixels, "shape": shape}


def mask_to_test_readable_only_shape(mask: Image) -> Dict:
    npimg = np.array(mask)
    shape = npimg.shape
    return {"shape": shape}


@is_pipeline_test
@require_vision
@require_torch
class AutomaticMaskGenerationPipelineTests(unittest.TestCase):
    model_mapping = dict(
        (
            list(MODEL_FOR_AUTOMATIC_MASK_GENERATION_MAPPING.items())
            if MODEL_FOR_AUTOMATIC_MASK_GENERATION_MAPPING
            else []
        )
    )

    def get_test_pipeline(self, model, tokenizer, processor):
        image_segmenter = AutomaticMaskGenerationPipeline(model=model, image_processor=processor)
        return image_segmenter, [
            "./tests/fixtures/tests_samples/COCO/000000039769.png",
            "./tests/fixtures/tests_samples/COCO/000000039769.png",
        ]

    @require_tf
    @unittest.skip("Image segmentation not implemented in TF")
    def test_small_model_tf(self):
        pass

    @require_torch
    def test_small_model_pt(self):
        image_segmenter = pipeline(model="ybelkada/sam-vit-h")

        outputs = image_segmenter("http://images.cocodataset.org/val2017/000000039769.jpg", points_per_batch=256)

        # Shortening by hashing
        new_outupt = []
        for i, o in enumerate(outputs["masks"]):
            new_outupt += [{"mask": mask_to_test_readable(o), "scores": outputs["scores"][i]}]

        # fmt: off
        self.assertEqual(
            nested_simplify(new_outupt, decimals=4),
            [
                {'mask': {'hash': '115ad19f5f', 'white_pixels': 0, 'shape': (480, 640)}, 'scores': 1.0444},
                {'mask': {'hash': '6affa964c6', 'white_pixels': 0, 'shape': (480, 640)}, 'scores': 1.021},
                {'mask': {'hash': 'dfe28a0388', 'white_pixels': 0, 'shape': (480, 640)}, 'scores': 1.0167},
                {'mask': {'hash': 'c0a5f4a318', 'white_pixels': 0, 'shape': (480, 640)}, 'scores': 1.0132},
                {'mask': {'hash': 'fe8065c197', 'white_pixels': 0, 'shape': (480, 640)}, 'scores': 1.0053},
                {'mask': {'hash': 'e2d0b7a0b7', 'white_pixels': 0, 'shape': (480, 640)}, 'scores': 0.9967},
                {'mask': {'hash': '453c7844bd', 'white_pixels': 0, 'shape': (480, 640)}, 'scores': 0.993},
                {'mask': {'hash': '3d44f2926d', 'white_pixels': 0, 'shape': (480, 640)}, 'scores': 0.9909},
                {'mask': {'hash': '64033ddc3f', 'white_pixels': 0, 'shape': (480, 640)}, 'scores': 0.9879},
                {'mask': {'hash': '801064ff79', 'white_pixels': 0, 'shape': (480, 640)}, 'scores': 0.9834},
                {'mask': {'hash': '6172f276ef', 'white_pixels': 0, 'shape': (480, 640)}, 'scores': 0.9716},
                {'mask': {'hash': 'b49e60e084', 'white_pixels': 0, 'shape': (480, 640)}, 'scores': 0.9612},
                {'mask': {'hash': 'a811e775fd', 'white_pixels': 0, 'shape': (480, 640)}, 'scores': 0.9599},
                {'mask': {'hash': 'a6a8ebcf4b', 'white_pixels': 0, 'shape': (480, 640)}, 'scores': 0.9552},
                {'mask': {'hash': '9d8257e080', 'white_pixels': 0, 'shape': (480, 640)}, 'scores': 0.9532},
                {'mask': {'hash': '32de6454a8', 'white_pixels': 0, 'shape': (480, 640)}, 'scores': 0.9516},
                {'mask': {'hash': 'af3d4af2c8', 'white_pixels': 0, 'shape': (480, 640)}, 'scores': 0.9499},
                {'mask': {'hash': '3c6db475fb', 'white_pixels': 0, 'shape': (480, 640)}, 'scores': 0.9483},
                {'mask': {'hash': 'c290813fb9', 'white_pixels': 0, 'shape': (480, 640)}, 'scores': 0.9464},
                {'mask': {'hash': 'b6f0b8f606', 'white_pixels': 0, 'shape': (480, 640)}, 'scores': 0.943},
                {'mask': {'hash': '92ce16bfdf', 'white_pixels': 0, 'shape': (480, 640)}, 'scores': 0.943},
                {'mask': {'hash': 'c749b25868', 'white_pixels': 0, 'shape': (480, 640)}, 'scores': 0.9408},
                {'mask': {'hash': 'efb6cab859', 'white_pixels': 0, 'shape': (480, 640)}, 'scores': 0.9335},
                {'mask': {'hash': '1ff2eafb30', 'white_pixels': 0, 'shape': (480, 640)}, 'scores': 0.9326},
                {'mask': {'hash': '788b798e24', 'white_pixels': 0, 'shape': (480, 640)}, 'scores': 0.9262},
                {'mask': {'hash': 'abea804f0e', 'white_pixels': 0, 'shape': (480, 640)}, 'scores': 0.8999},
                {'mask': {'hash': '7b9e8ddb73', 'white_pixels': 0, 'shape': (480, 640)}, 'scores': 0.8986},
                {'mask': {'hash': 'cd24047c8a', 'white_pixels': 0, 'shape': (480, 640)}, 'scores': 0.8984},
                {'mask': {'hash': '6943e6bcbd', 'white_pixels': 0, 'shape': (480, 640)}, 'scores': 0.8873},
                {'mask': {'hash': 'b5f47c9191', 'white_pixels': 0, 'shape': (480, 640)}, 'scores': 0.8871}
            ],
        )
        # fmt: on

    @require_torch
    @slow
    def test_threshold(self):
        model_id = "ybelkada/sam-vit-s"
        image_segmenter = pipeline("automatic-mask-generation", model=model_id)

        outputs = image_segmenter(
            "http://images.cocodataset.org/val2017/000000039769.jpg", pred_iou_thresh=1, points_per_batch=256
        )

        # Shortening by hashing
        new_outupt = []
        for i, o in enumerate(outputs["masks"]):
            new_outupt += [{"mask": mask_to_test_readable(o), "scores": outputs["scores"][i]}]

        self.assertEqual(
            nested_simplify(new_outupt, decimals=4),
            [
                {"mask": {"hash": "115ad19f5f", "white_pixels": 0, "shape": (480, 640)}, "scores": 1.0444},
                {"mask": {"hash": "6affa964c6", "white_pixels": 0, "shape": (480, 640)}, "scores": 1.0210},
                {"mask": {"hash": "dfe28a0388", "white_pixels": 0, "shape": (480, 640)}, "scores": 1.0167},
                {"mask": {"hash": "c0a5f4a318", "white_pixels": 0, "shape": (480, 640)}, "scores": 1.0132},
                {"mask": {"hash": "fe8065c197", "white_pixels": 0, "shape": (480, 640)}, "scores": 1.0053},
            ],
        )

    @require_torch
    @slow
    def test_other_args(self):
        model_id = "ybelkada/sam-vit-s"
        image_segmenter = pipeline("automatic-mask-generation", model=model_id)

        # n_layers to test more than 1 crop boxes.
        image_segmenter("http://images.cocodataset.org/val2017/000000039769.jpg", n_layers=3, points_per_batch=256)
