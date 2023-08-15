# coding=utf-8
# Copyright 2022 The HuggingFace Inc. team. All rights reserved.
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
""" Testing suite for the PyTorch Bros model. """

import copy
import unittest

from transformers.models.auto import get_values
from transformers.testing_utils import require_torch, slow, torch_device

from transformers.utils import is_torch_available
from ...test_configuration_common import ConfigTester
from ...test_modeling_common import ModelTesterMixin, ids_tensor, random_attention_mask


if is_torch_available():
    import torch

    from transformers import (
        MODEL_FOR_TOKEN_CLASSIFICATION_MAPPING,
        BrosConfig,
        BrosForTokenClassification,
        BrosSpadeEEForTokenClassification,
        BrosSpadeELForTokenClassification,
        BrosModel,
    )
    from transformers.models.bros.modeling_bros import (
        BROS_PRETRAINED_MODEL_ARCHIVE_LIST,
    )


class BrosModelTester:
    def __init__(
        self,
        parent,
        batch_size=13,
        seq_length=7,
        is_training=True,
        use_input_mask=True,
        use_token_type_ids=True,
        use_box_first_token_mask=True,
        use_labels=True,
        vocab_size=99,
        hidden_size=64,
        num_hidden_layers=5,
        num_attention_heads=4,
        intermediate_size=37,
        hidden_act="gelu",
        hidden_dropout_prob=0.1,
        attention_probs_dropout_prob=0.1,
        max_position_embeddings=512,
        type_vocab_size=16,
        type_sequence_label_size=2,
        initializer_range=0.02,
        num_labels=3,
        num_choices=4,
        scope=None,
        range_bbox=1000,
    ):
        self.parent = parent
        self.batch_size = batch_size
        self.seq_length = seq_length
        self.is_training = is_training
        self.use_input_mask = use_input_mask
        self.use_box_first_token_mask = use_box_first_token_mask
        self.use_token_type_ids = use_token_type_ids
        self.use_labels = use_labels
        self.vocab_size = vocab_size
        self.hidden_size = hidden_size
        self.num_hidden_layers = num_hidden_layers
        self.num_attention_heads = num_attention_heads
        self.intermediate_size = intermediate_size
        self.hidden_act = hidden_act
        self.hidden_dropout_prob = hidden_dropout_prob
        self.attention_probs_dropout_prob = attention_probs_dropout_prob
        self.max_position_embeddings = max_position_embeddings
        self.type_vocab_size = type_vocab_size
        self.type_sequence_label_size = type_sequence_label_size
        self.initializer_range = initializer_range
        self.num_labels = num_labels
        self.num_choices = num_choices
        self.scope = scope
        self.range_bbox = range_bbox

    def prepare_config_and_inputs(self):
        input_ids = ids_tensor([self.batch_size, self.seq_length], self.vocab_size)

        bbox = ids_tensor([self.batch_size, self.seq_length, 8], 1)
        # Ensure that bbox is legal
        for i in range(bbox.shape[0]):
            for j in range(bbox.shape[1]):
                if bbox[i, j, 3] < bbox[i, j, 1]:
                    t = bbox[i, j, 3]
                    bbox[i, j, 3] = bbox[i, j, 1]
                    bbox[i, j, 1] = t
                if bbox[i, j, 2] < bbox[i, j, 0]:
                    t = bbox[i, j, 2]
                    bbox[i, j, 2] = bbox[i, j, 0]
                    bbox[i, j, 0] = t

        input_mask = None
        if self.use_input_mask:
            input_mask = random_attention_mask([self.batch_size, self.seq_length])

        box_first_token_mask = None
        if self.use_box_first_token_mask:
            box_first_token_mask = random_attention_mask([self.batch_size, self.seq_length])

        token_type_ids = None
        if self.use_token_type_ids:
            token_type_ids = ids_tensor([self.batch_size, self.seq_length], self.type_vocab_size)

        sequence_labels = None
        token_labels = None
        choice_labels = None
        if self.use_labels:
            token_labels = ids_tensor([self.batch_size, self.seq_length], self.num_labels)
            itc_labels = ids_tensor([self.batch_size, self.seq_length], self.num_labels)
            stc_labels = ids_tensor([self.batch_size, self.seq_length], self.num_labels)

        config = self.get_config()

        return (
            config,
            input_ids,
            bbox,
            token_type_ids,
            input_mask,
            box_first_token_mask,
            token_labels,
            itc_labels,
            stc_labels,
        )

    def get_config(self):
        return BrosConfig(
            vocab_size=self.vocab_size,
            hidden_size=self.hidden_size,
            num_hidden_layers=self.num_hidden_layers,
            num_attention_heads=self.num_attention_heads,
            intermediate_size=self.intermediate_size,
            hidden_act=self.hidden_act,
            hidden_dropout_prob=self.hidden_dropout_prob,
            attention_probs_dropout_prob=self.attention_probs_dropout_prob,
            max_position_embeddings=self.max_position_embeddings,
            type_vocab_size=self.type_vocab_size,
            is_decoder=False,
            initializer_range=self.initializer_range,
        )

    def create_and_check_model(
        self,
        config,
        input_ids,
        bbox,
        token_type_ids,
        input_mask,
        box_first_token_mask,
        token_labels,
        itc_labels,
        stc_labels,
    ):
        model = BrosModel(config=config)
        model.to(torch_device)
        model.eval()
        result = model(input_ids, bbox=bbox, attention_mask=input_mask, token_type_ids=token_type_ids)
        result = model(input_ids, bbox=bbox, token_type_ids=token_type_ids)
        result = model(input_ids, bbox=bbox)
        self.parent.assertEqual(result.last_hidden_state.shape, (self.batch_size, self.seq_length, self.hidden_size))

    def create_and_check_for_token_classification(
        self,
        config,
        input_ids,
        bbox,
        token_type_ids,
        input_mask,
        box_first_token_mask,
        token_labels,
        itc_labels,
        stc_labels,
    ):
        config.num_labels = self.num_labels
        model = BrosForTokenClassification(config=config)
        model.to(torch_device)
        model.eval()
        result = model(
            input_ids, bbox=bbox, attention_mask=input_mask, token_type_ids=token_type_ids, labels=token_labels
        )
        self.parent.assertEqual(result.logits.shape, (self.batch_size, self.seq_length, self.num_labels))

    def create_and_check_for_spade_ee_token_classification(
        self,
        config,
        input_ids,
        bbox,
        token_type_ids,
        input_mask,
        box_first_token_mask,
        token_labels,
        itc_labels,
        stc_labels,
    ):
        config.num_labels = self.num_labels
        model = BrosSpadeEEForTokenClassification(config=config)
        model.to(torch_device)
        model.eval()
        result = model(
            input_ids,
            bbox=bbox,
            attention_mask=input_mask,
            box_first_token_mask=box_first_token_mask,
            token_type_ids=token_type_ids,
            itc_labels=token_labels,
            stc_labels=token_labels,
        )
        self.parent.assertEqual(result.itc_logits.shape, (self.batch_size, self.seq_length, self.num_labels))
        self.parent.assertEqual(result.stc_logits.shape, (self.batch_size, self.seq_length, self.seq_length + 1))

    def create_and_check_for_spade_el_token_classification(
        self,
        config,
        input_ids,
        bbox,
        token_type_ids,
        input_mask,
        box_first_token_mask,
        token_labels,
        itc_labels,
        stc_labels,
    ):
        config.num_labels = self.num_labels
        model = BrosSpadeELForTokenClassification(config=config)
        model.to(torch_device)
        model.eval()
        result = model(
            input_ids,
            bbox=bbox,
            attention_mask=input_mask,
            box_first_token_mask=box_first_token_mask,
            token_type_ids=token_type_ids,
            labels=token_labels,
        )
        self.parent.assertEqual(result.logits.shape, (self.batch_size, self.seq_length, self.seq_length + 1))

    def prepare_config_and_inputs_for_common(self):
        config_and_inputs = self.prepare_config_and_inputs()
        (
            config,
            input_ids,
            bbox,
            token_type_ids,
            input_mask,
            box_first_token_mask,
            token_labels,
            itc_labels,
            stc_labels,
        ) = config_and_inputs
        inputs_dict = {
            "input_ids": input_ids,
            "bbox": bbox,
            "token_type_ids": token_type_ids,
            "attention_mask": input_mask,
        }
        return config, inputs_dict


@require_torch
class BrosModelTest(ModelTesterMixin, unittest.TestCase):
    test_pruning = False
    test_torchscript = False
    test_mismatched_shapes = False

    all_model_classes = (
        (
            BrosForTokenClassification,
            BrosSpadeEEForTokenClassification,
            BrosSpadeELForTokenClassification,
            BrosModel,
        )
        if is_torch_available()
        else ()
    )
    all_generative_model_classes = () if is_torch_available() else ()

    def setUp(self):
        self.model_tester = BrosModelTester(self)
        self.config_tester = ConfigTester(self, config_class=BrosConfig, hidden_size=37)

    def _prepare_for_class(self, inputs_dict, model_class, return_labels=False):
        inputs_dict = copy.deepcopy(inputs_dict)

        if return_labels:
            if model_class.__name__ in ["BrosForTokenClassification", "BrosSpadeELForTokenClassification"]:
                inputs_dict["labels"] = torch.zeros(
                    (self.model_tester.batch_size, self.model_tester.seq_length),
                    dtype=torch.long,
                    device=torch_device,
                )
                inputs_dict["box_first_token_mask"] = torch.ones(
                    [self.model_tester.batch_size, self.model_tester.seq_length],
                    dtype=torch.long,
                    device=torch_device,
                )
            elif model_class.__name__ in ["BrosSpadeEEForTokenClassification"]:
                inputs_dict["itc_labels"] = torch.zeros(
                    (self.model_tester.batch_size, self.model_tester.seq_length),
                    dtype=torch.long,
                    device=torch_device,
                )
                inputs_dict["stc_labels"] = torch.zeros(
                    (self.model_tester.batch_size, self.model_tester.seq_length),
                    dtype=torch.long,
                    device=torch_device,
                )
                inputs_dict["box_first_token_mask"] = torch.ones(
                    [self.model_tester.batch_size, self.model_tester.seq_length],
                    dtype=torch.long,
                    device=torch_device,
                )

        return inputs_dict

    def test_config(self):
        self.config_tester.run_common_tests()

    def test_model(self):
        config_and_inputs = self.model_tester.prepare_config_and_inputs()
        self.model_tester.create_and_check_model(*config_and_inputs)

    def test_multi_gpu_data_parallel_forward(self):
        pass

    def test_model_various_embeddings(self):
        config_and_inputs = self.model_tester.prepare_config_and_inputs()
        for type in ["absolute", "relative_key", "relative_key_query"]:
            config_and_inputs[0].position_embedding_type = type
            self.model_tester.create_and_check_model(*config_and_inputs)

    def test_for_token_classification(self):
        config_and_inputs = self.model_tester.prepare_config_and_inputs()
        self.model_tester.create_and_check_for_token_classification(*config_and_inputs)

    def test_for_spade_ee_token_classification(self):
        config_and_inputs = self.model_tester.prepare_config_and_inputs()
        self.model_tester.create_and_check_for_spade_ee_token_classification(*config_and_inputs)

    def test_for_spade_el_token_classification(self):
        config_and_inputs = self.model_tester.prepare_config_and_inputs()
        self.model_tester.create_and_check_for_spade_el_token_classification(*config_and_inputs)

    @slow
    def test_model_from_pretrained(self):
        for model_name in BROS_PRETRAINED_MODEL_ARCHIVE_LIST[:1]:
            model = BrosModel.from_pretrained(model_name)
            self.assertIsNotNone(model)


def prepare_bros_batch_inputs():
    attention_mask = torch.tensor([[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]])

    bbox = torch.tensor(
        [
            [
                [
                    0.0000000000,
                    0.0000000000,
                    0.0000000000,
                    0.0000000000,
                    0.0000000000,
                    0.0000000000,
                    0.0000000000,
                    0.0000000000,
                ],
                [
                    0.5223097205,
                    0.5590000153,
                    0.5787401795,
                    0.5590000153,
                    0.5787401795,
                    0.5720000267,
                    0.5223097205,
                    0.5720000267,
                ],
                [
                    0.5853018165,
                    0.5590000153,
                    0.6863517165,
                    0.5590000153,
                    0.6863517165,
                    0.5720000267,
                    0.5853018165,
                    0.5720000267,
                ],
                [
                    0.5853018165,
                    0.5590000153,
                    0.6863517165,
                    0.5590000153,
                    0.6863517165,
                    0.5720000267,
                    0.5853018165,
                    0.5720000267,
                ],
                [
                    0.1233595833,
                    0.5699999928,
                    0.2191601098,
                    0.5699999928,
                    0.2191601098,
                    0.5839999914,
                    0.1233595833,
                    0.5839999914,
                ],
                [
                    0.2230971158,
                    0.5680000186,
                    0.2782152295,
                    0.5680000186,
                    0.2782152295,
                    0.5780000091,
                    0.2230971158,
                    0.5780000091,
                ],
                [
                    0.2874015868,
                    0.5669999719,
                    0.3333333433,
                    0.5669999719,
                    0.3333333433,
                    0.5780000091,
                    0.2874015868,
                    0.5780000091,
                ],
                [
                    0.3425196707,
                    0.5640000105,
                    0.4343832135,
                    0.5640000105,
                    0.4343832135,
                    0.5749999881,
                    0.3425196707,
                    0.5749999881,
                ],
                [
                    0.0866141766,
                    0.7770000100,
                    0.1181102395,
                    0.7770000100,
                    0.1181102395,
                    0.7870000005,
                    0.0866141766,
                    0.7870000005,
                ],
                [
                    0.1167979017,
                    0.7770000100,
                    0.1522309780,
                    0.7770000100,
                    0.1522309780,
                    0.7850000262,
                    0.1167979017,
                    0.7850000262,
                ],
                [
                    0.1535433084,
                    0.7749999762,
                    0.1863517016,
                    0.7749999762,
                    0.1863517016,
                    0.7850000262,
                    0.1535433084,
                    0.7850000262,
                ],
                [
                    0.1889763772,
                    0.7749999762,
                    0.2572178543,
                    0.7749999762,
                    0.2572178543,
                    0.7850000262,
                    0.1889763772,
                    0.7850000262,
                ],
                [
                    1.0000000000,
                    1.0000000000,
                    1.0000000000,
                    1.0000000000,
                    1.0000000000,
                    1.0000000000,
                    1.0000000000,
                    1.0000000000,
                ],
            ],
            [
                [
                    0.0000000000,
                    0.0000000000,
                    0.0000000000,
                    0.0000000000,
                    0.0000000000,
                    0.0000000000,
                    0.0000000000,
                    0.0000000000,
                ],
                [
                    0.4396325350,
                    0.6719999909,
                    0.4658792615,
                    0.6719999909,
                    0.4658792615,
                    0.6850000024,
                    0.4396325350,
                    0.6850000024,
                ],
                [
                    0.4698162675,
                    0.6719999909,
                    0.4842519760,
                    0.6719999909,
                    0.4842519760,
                    0.6850000024,
                    0.4698162675,
                    0.6850000024,
                ],
                [
                    0.1574803144,
                    0.6869999766,
                    0.2020997405,
                    0.6869999766,
                    0.2020997405,
                    0.6980000138,
                    0.1574803144,
                    0.6980000138,
                ],
                [
                    0.2047244161,
                    0.6869999766,
                    0.2729658782,
                    0.6869999766,
                    0.2729658782,
                    0.6999999881,
                    0.2047244161,
                    0.6999999881,
                ],
                [
                    0.1299212575,
                    0.7009999752,
                    0.1430446208,
                    0.7009999752,
                    0.1430446208,
                    0.7139999866,
                    0.1299212575,
                    0.7139999866,
                ],
                [
                    0.1299212575,
                    0.7009999752,
                    0.1430446208,
                    0.7009999752,
                    0.1430446208,
                    0.7139999866,
                    0.1299212575,
                    0.7139999866,
                ],
                [
                    0.1561679840,
                    0.7009999752,
                    0.2440944910,
                    0.7009999752,
                    0.2440944910,
                    0.7120000124,
                    0.1561679840,
                    0.7120000124,
                ],
                [
                    0.1561679840,
                    0.7009999752,
                    0.2440944910,
                    0.7009999752,
                    0.2440944910,
                    0.7120000124,
                    0.1561679840,
                    0.7120000124,
                ],
                [
                    0.2454068214,
                    0.7009999752,
                    0.3149606287,
                    0.7009999752,
                    0.3149606287,
                    0.7120000124,
                    0.2454068214,
                    0.7120000124,
                ],
                [
                    0.3175852895,
                    0.7009999752,
                    0.3320209980,
                    0.7009999752,
                    0.3320209980,
                    0.7110000253,
                    0.3175852895,
                    0.7110000253,
                ],
                [
                    0.3333333433,
                    0.6999999881,
                    0.4028871357,
                    0.6999999881,
                    0.4028871357,
                    0.7139999866,
                    0.3333333433,
                    0.7139999866,
                ],
                [
                    1.0000000000,
                    1.0000000000,
                    1.0000000000,
                    1.0000000000,
                    1.0000000000,
                    1.0000000000,
                    1.0000000000,
                    1.0000000000,
                ],
            ],
        ]
    )
    input_ids = torch.tensor(
        [
            [101, 1055, 8910, 1012, 5719, 3296, 5366, 3378, 2146, 2846, 10807, 13494, 102],
            [101, 2112, 1997, 3671, 6364, 1019, 1012, 5057, 1011, 4646, 2030, 2974, 102],
        ]
    )

    return input_ids, bbox, attention_mask


@require_torch
class BrosModelIntegrationTest(unittest.TestCase):
    @slow
    def test_inference_no_head(self):
        model = BrosModel.from_pretrained("naver-clova-ocr/bros-base-uncased").to(torch_device)
        input_ids, bbox, attention_mask = prepare_bros_batch_inputs()

        with torch.no_grad():
            outputs = model(
                input_ids.to(torch_device),
                bbox.to(torch_device),
                attention_mask=attention_mask.to(torch_device),
                return_dict=True,
            )

        # verify the logits
        expected_shape = torch.Size((2, 13, 768))
        self.assertEqual(outputs.last_hidden_state.shape, expected_shape)

        expected_slice = torch.tensor(
            [[-0.3062, 0.1368, 0.3154], [0.0928, -0.1156, 0.1050], [0.0224, 0.0008, 0.1282]]
        ).to(torch_device)

        self.assertTrue(torch.allclose(outputs.last_hidden_state[0, :3, :3], expected_slice, atol=1e-4))
