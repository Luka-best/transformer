# coding=utf-8
# Copyright 2023 The HuggingFace Inc. team. All rights reserved.
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
""" Testing suite for the PyTorch PVT model. """


import inspect
import unittest

from transformers import is_torch_available
from transformers.models.auto import get_values
from transformers.testing_utils import (
    require_accelerate,
    require_torch,
    require_torch_gpu,
    slow,
    torch_device,
)

from ...test_modeling_common import floats_tensor, ids_tensor


if is_torch_available():
    import torch

    from transformers import MODEL_MAPPING, PvtConfig, PvtForImageClassification, PvtImageProcessor, PvtModel
    from transformers.models.pvt.modeling_pvt import (
        PVT_PRETRAINED_MODEL_ARCHIVE_LIST,
    )


if is_vision_available():
    from PIL import Image


class PvtModelTester:
    def __init__(
        self,
        parent,
        batch_size=13,
        image_size=64,
        num_channels=3,
        num_encoder_blocks=4,
        depths=[2, 2, 2, 2],
        sr_ratios=[8, 4, 2, 1],
        hidden_sizes=[16, 32, 64, 128],
        downsampling_rates=[1, 4, 8, 16],
        num_attention_heads=[1, 2, 4, 8],
        is_training=True,
        use_labels=True,
        hidden_act="gelu",
        hidden_dropout_prob=0.1,
        attention_probs_dropout_prob=0.1,
        initializer_range=1.0,
        num_labels=3,
        scope=None,
    ):
        self.parent = parent
        self.batch_size = batch_size
        self.image_size = image_size
        self.num_channels = num_channels
        self.num_encoder_blocks = num_encoder_blocks
        self.sr_ratios = sr_ratios
        self.depths = depths
        self.hidden_sizes = hidden_sizes
        self.downsampling_rates = downsampling_rates
        self.num_attention_heads = num_attention_heads
        self.is_training = is_training
        self.use_labels = use_labels
        self.hidden_act = hidden_act
        self.hidden_dropout_prob = hidden_dropout_prob
        self.attention_probs_dropout_prob = attention_probs_dropout_prob
        self.initializer_range = initializer_range
        self.num_labels = num_labels
        self.scope = scope

    def prepare_config_and_inputs(self):
        pixel_values = floats_tensor([self.batch_size, self.num_channels, self.image_size, self.image_size])

        labels = None
        if self.use_labels:
            labels = ids_tensor([self.batch_size, self.image_size, self.image_size], self.num_labels)

        config = self.get_config()
        return config, pixel_values, labels

    def get_config(self):
        return PvtConfig(
            image_size=self.image_size,
            num_channels=self.num_channels,
            num_encoder_blocks=self.num_encoder_blocks,
            depths=self.depths,
            hidden_sizes=self.hidden_sizes,
            num_attention_heads=self.num_attention_heads,
            hidden_act=self.hidden_act,
            hidden_dropout_prob=self.hidden_dropout_prob,
            attention_probs_dropout_prob=self.attention_probs_dropout_prob,
            initializer_range=self.initializer_range,
        )

    def create_and_check_model(self, config, pixel_values):
        model = PvtForImageClassification(config=config)
        model.to(torch_device)
        model.eval()
        result = model(pixel_values)
        expected_height = expected_width = self.image_size // (self.downsampling_rates[-1] * 2)
        self.parent.assertEqual(
            result.last_hidden_state.shape, (self.batch_size, self.hidden_sizes[-1], expected_height, expected_width)
        )

    def create_and_check_for_image_classification(self, config, pixel_values, labels):
        config.num_labels = self.type_sequence_label_size
        model = PvtForImageClassification(config)
        model.to(torch_device)
        model.eval()
        result = model(pixel_values, labels=labels)
        self.parent.assertEqual(result.logits.shape, (self.batch_size, self.type_sequence_label_size))

        # test greyscale images
        config.num_channels = 1
        model = PvtForImageClassification(config)
        model.to(torch_device)
        model.eval()

        pixel_values = floats_tensor([self.batch_size, 1, self.image_size, self.image_size])
        result = model(pixel_values)
        self.parent.assertEqual(result.logits.shape, (self.batch_size, self.type_sequence_label_size))

    def prepare_config_and_inputs_for_common(self):
        config_and_inputs = self.prepare_config_and_inputs()
        config, pixel_values, labels = config_and_inputs
        inputs_dict = {"pixel_values": pixel_values}
        return config, inputs_dict

    fx_compatible = True

    test_pruning = False
    test_resize_embeddings = False
    test_head_masking = False

    all_model_classes = (PvtForImageClassification, PvtModel) if is_torch_available() else ()

    def setUp(self):
        self.model_tester = PvtModelTester(self)
        self.config_tester = PvtModelTester(self)

    def test_config(self):
        self.config_tester.run_common_tests()

    def test_model(self):
        config_and_inputs = self.model_tester.prepare_config_and_inputs()
        self.model_tester.create_and_check_model(*config_and_inputs)

    @unittest.skip("PVT does not use inputs_embeds")
    def test_inputs_embeds(self):
        pass

    @unittest.skip("PVT does not have get_input_embeddings method and get_output_embeddings methods")
    def test_model_common_attributes(self):
        pass

    def test_forward_signature(self):
        config, _ = self.model_tester.prepare_config_and_inputs_for_common()

        for model_class in self.all_model_classes:
            model = model_class(config)
            signature = inspect.signature(model.forward)
            # signature.parameters is an OrderedDict => so arg_names order is deterministic
            arg_names = [*signature.parameters.keys()]

            expected_arg_names = ["pixel_values"]
            self.assertListEqual(arg_names[:1], expected_arg_names)

    def test_attention_outputs(self):
        config, inputs_dict = self.model_tester.prepare_config_and_inputs_for_common()
        config.return_dict = True

        for model_class in self.all_model_classes:
            inputs_dict["output_attentions"] = True
            inputs_dict["output_hidden_states"] = False
            config.return_dict = True
            model = model_class(config)
            model.to(torch_device)
            model.eval()
            with torch.no_grad():
                outputs = model(**self._prepare_for_class(inputs_dict, model_class))
            attentions = outputs.attentions

            expected_num_attentions = sum(self.model_tester.depths)
            self.assertEqual(len(attentions), expected_num_attentions)

            # check that output_attentions also work using config
            del inputs_dict["output_attentions"]
            config.output_attentions = True
            model = model_class(config)
            model.to(torch_device)
            model.eval()
            with torch.no_grad():
                outputs = model(**self._prepare_for_class(inputs_dict, model_class))
            attentions = outputs.attentions

            self.assertEqual(len(attentions), expected_num_attentions)

            # verify the first attentions (first block, first layer)
            expected_seq_len = (self.model_tester.image_size // 4) ** 2
            expected_reduced_seq_len = (self.model_tester.image_size // (4 * self.model_tester.sr_ratios[0])) ** 2
            self.assertListEqual(
                list(attentions[0].shape[-3:]),
                [self.model_tester.num_attention_heads[0], expected_seq_len, expected_reduced_seq_len],
            )

            # verify the last attentions (last block, last layer)
            expected_seq_len = (self.model_tester.image_size // 32) ** 2
            expected_reduced_seq_len = (self.model_tester.image_size // (32 * self.model_tester.sr_ratios[-1])) ** 2
            self.assertListEqual(
                list(attentions[-1].shape[-3:]),
                [self.model_tester.num_attention_heads[-1], expected_seq_len, expected_reduced_seq_len],
            )
            out_len = len(outputs)

            # Check attention is always last and order is fine
            inputs_dict["output_attentions"] = True
            inputs_dict["output_hidden_states"] = True
            model = model_class(config)
            model.to(torch_device)
            model.eval()
            with torch.no_grad():
                outputs = model(**self._prepare_for_class(inputs_dict, model_class))

            self.assertEqual(out_len + 1, len(outputs))

            self_attentions = outputs.attentions

            self.assertEqual(len(self_attentions), expected_num_attentions)
            # verify the first attentions (first block, first layer)
            expected_seq_len = (self.model_tester.image_size // 4) ** 2
            expected_reduced_seq_len = (self.model_tester.image_size // (4 * self.model_tester.sr_ratios[0])) ** 2
            self.assertListEqual(
                list(self_attentions[0].shape[-3:]),
                [self.model_tester.num_attention_heads[0], expected_seq_len, expected_reduced_seq_len],
            )

    def test_hidden_states_output(self):
        def check_hidden_states_output(inputs_dict, config, model_class):
            model = model_class(config)
            model.to(torch_device)
            model.eval()

            with torch.no_grad():
                outputs = model(**self._prepare_for_class(inputs_dict, model_class))

            hidden_states = outputs.hidden_states

            expected_num_layers = self.model_tester.num_encoder_blocks
            self.assertEqual(len(hidden_states), expected_num_layers)

            # verify the first hidden states (first block)
            self.assertListEqual(
                list(hidden_states[0].shape[-3:]),
                [
                    self.model_tester.hidden_sizes[0],
                    self.model_tester.image_size // 4,
                    self.model_tester.image_size // 4,
                ],
            )

        config, inputs_dict = self.model_tester.prepare_config_and_inputs_for_common()

        for model_class in self.all_model_classes:
            inputs_dict["output_hidden_states"] = True
            check_hidden_states_output(inputs_dict, config, model_class)

            # check that output_hidden_states also work using config
            del inputs_dict["output_hidden_states"]
            config.output_hidden_states = True

            check_hidden_states_output(inputs_dict, config, model_class)

    def test_training(self):
        if not self.model_tester.is_training:
            return

        config, inputs_dict = self.model_tester.prepare_config_and_inputs_for_common()
        config.return_dict = True

        for model_class in self.all_model_classes:
            if model_class in get_values(MODEL_MAPPING):
                continue

            model = model_class(config)
            model.to(torch_device)
            model.train()
            inputs = self._prepare_for_class(inputs_dict, model_class, return_labels=True)
            loss = model(**inputs).loss
            loss.backward()

    def test_for_image_classification(self):
        config_and_inputs = self.model_tester.prepare_config_and_inputs()
        self.model_tester.create_and_check_for_image_classification(*config_and_inputs)

    @slow
    def test_model_from_pretrained(self):
        for model_name in PVT_PRETRAINED_MODEL_ARCHIVE_LIST[:1]:
            model = PvtForImageClassification.from_pretrained(model_name)
            self.assertIsNotNone(model)


# We will verify our results on an image of cute cats
def prepare_img():
    image = Image.open("./tests/fixtures/tests_samples/COCO/000000039769.png")
    return image


@require_torch
class PvtModelIntegrationTest(unittest.TestCase):
    @slow
    def test_inference_image_classification(self):
        # only resize + normalize
        feature_extractor = PvtImageProcessor.from_pretrained("Xrenya/pvt-tiny-224")
        model = PvtForImageClassification.from_pretrained("Xrenya/pvt-medium-224").to(torch_device).eval()

        image = prepare_img()
        encoded_inputs = feature_extractor(images=image, return_tensors="pt")
        pixel_values = encoded_inputs.pixel_values.to(torch_device)

        with torch.no_grad():
            outputs = model(pixel_values)

        expected_shape = torch.Size((1, model.config.num_labels))
        self.assertEqual(outputs.logits.shape, expected_shape)

        expected_slice = torch.tensor([-0.2910, -0.2229, 0.0321]).to(torch_device)

        self.assertTrue(torch.allclose(outputs.logits[0, :3], expected_slice, atol=1e-4))

    @slow
    def test_inference_model(self):
        model = PvtModel.from_pretrained("Xrenya/pvt-medium-224").to(torch_device).eval()

        feature_extractor = PvtImageProcessor.from_pretrained("Xrenya/pvt-tiny-224")
        image = prepare_img()
        inputs = feature_extractor(images=image, return_tensors="pt")
        pixel_values = inputs.pixel_values.to(torch_device)

        # forward pass
        with torch.no_grad():
            outputs = model(pixel_values)

        # verify the logits
        expected_shape = torch.Size((1, 50, 512))
        self.assertEqual(outputs.last_hidden_state.shape, expected_shape)

        expected_slice = torch.tensor(
            [[-0.3641, -0.6515, 1.4248], [0.5005, 0.2392, -0.6012], [0.6238, 0.0133, -0.3935]]
        ).to(torch_device)

        self.assertTrue(torch.allclose(outputs.last_hidden_state[0, :3, :3], expected_slice, atol=1e-4))

    @slow
    @require_accelerate
    @require_torch_gpu
    def test_inference_fp16(self):
        r"""
        A small test to make sure that inference work in half precision without any problem.
        """
        model = PvtForImageClassification.from_pretrained(
            "Xrenya/pvt-medium-224", torch_dtype=torch.float16, device_map="auto"
        )
        feature_extractor = PvtImageProcessor(size=224)

        image = prepare_img()
        inputs = feature_extractor(images=image, return_tensors="pt")
        pixel_values = inputs.pixel_values.to(torch_device).astype(torch.float16)

        # forward pass to make sure inference works in fp16
        with torch.no_grad():
            _ = model(pixel_values)
