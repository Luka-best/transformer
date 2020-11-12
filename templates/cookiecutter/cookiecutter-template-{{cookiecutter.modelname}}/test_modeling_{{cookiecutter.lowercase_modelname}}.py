# coding=utf-8
# Copyright 2018 The Google AI Language Team Authors.
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
""" Testing suite for the PyTorch {{cookiecutter.modelname}} model. """


{% if cookiecutter.is_encoder_decoder_model == "False" -%}
import unittest

from transformers import is_torch_available
from transformers.testing_utils import require_torch, slow, torch_device

from .test_configuration_common import ConfigTester
from .test_modeling_common import ModelTesterMixin, floats_tensor, ids_tensor, random_attention_mask


if is_torch_available():
    from transformers import (
        {{cookiecutter.camelcase_modelname}}Config,
        {{cookiecutter.camelcase_modelname}}ForMaskedLM,
        {{cookiecutter.camelcase_modelname}}ForMultipleChoice,
        {{cookiecutter.camelcase_modelname}}ForQuestionAnswering,
        {{cookiecutter.camelcase_modelname}}ForSequenceClassification,
        {{cookiecutter.camelcase_modelname}}ForTokenClassification,
        {{cookiecutter.camelcase_modelname}}Model,
    )
    from transformers.modeling_{{cookiecutter.lowercase_modelname}} import {{cookiecutter.uppercase_modelname}}_PRETRAINED_MODEL_ARCHIVE_LIST


class {{cookiecutter.camelcase_modelname}}ModelTester:
    def __init__(
            self,
            parent,
            batch_size=13,
            seq_length=7,
            is_training=True,
            use_input_mask=True,
            use_token_type_ids=True,
            use_labels=True,
            vocab_size=99,
            hidden_size=32,
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
    ):
        self.parent = parent
        self.batch_size = batch_size
        self.seq_length = seq_length
        self.is_training = is_training
        self.use_input_mask = use_input_mask
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

    def prepare_config_and_inputs(self):
        input_ids = ids_tensor([self.batch_size, self.seq_length], self.vocab_size)

        input_mask = None
        if self.use_input_mask:
            input_mask = random_attention_mask([self.batch_size, self.seq_length])

        token_type_ids = None
        if self.use_token_type_ids:
            token_type_ids = ids_tensor([self.batch_size, self.seq_length], self.type_vocab_size)

        sequence_labels = None
        token_labels = None
        choice_labels = None
        if self.use_labels:
            sequence_labels = ids_tensor([self.batch_size], self.type_sequence_label_size)
            token_labels = ids_tensor([self.batch_size, self.seq_length], self.num_labels)
            choice_labels = ids_tensor([self.batch_size], self.num_choices)

        config = {{cookiecutter.camelcase_modelname}}Config(
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
            return_dict=True,
        )

        return config, input_ids, token_type_ids, input_mask, sequence_labels, token_labels, choice_labels

    def create_and_check_model(
            self, config, input_ids, token_type_ids, input_mask, sequence_labels, token_labels, choice_labels
    ):
        model = {{cookiecutter.camelcase_modelname}}Model(config=config)
        model.to(torch_device)
        model.eval()
        result = model(input_ids, attention_mask=input_mask, token_type_ids=token_type_ids)
        result = model(input_ids, token_type_ids=token_type_ids)
        result = model(input_ids)
        self.parent.assertEqual(result.last_hidden_state.shape, (self.batch_size, self.seq_length, self.hidden_size))

    def create_and_check_for_masked_lm(
            self, config, input_ids, token_type_ids, input_mask, sequence_labels, token_labels, choice_labels
    ):
        model = {{cookiecutter.camelcase_modelname}}ForMaskedLM(config=config)
        model.to(torch_device)
        model.eval()
        result = model(input_ids, attention_mask=input_mask, token_type_ids=token_type_ids, labels=token_labels)
        self.parent.assertEqual(result.logits.shape, (self.batch_size, self.seq_length, self.vocab_size))

    def create_and_check_for_question_answering(
            self, config, input_ids, token_type_ids, input_mask, sequence_labels, token_labels, choice_labels
    ):
        model = {{cookiecutter.camelcase_modelname}}ForQuestionAnswering(config=config)
        model.to(torch_device)
        model.eval()
        result = model(
            input_ids,
            attention_mask=input_mask,
            token_type_ids=token_type_ids,
            start_positions=sequence_labels,
            end_positions=sequence_labels,
        )
        self.parent.assertEqual(result.start_logits.shape, (self.batch_size, self.seq_length))
        self.parent.assertEqual(result.end_logits.shape, (self.batch_size, self.seq_length))

    def create_and_check_for_sequence_classification(
            self, config, input_ids, token_type_ids, input_mask, sequence_labels, token_labels, choice_labels
    ):
        config.num_labels = self.num_labels
        model = {{cookiecutter.camelcase_modelname}}ForSequenceClassification(config)
        model.to(torch_device)
        model.eval()
        result = model(input_ids, attention_mask=input_mask, token_type_ids=token_type_ids, labels=sequence_labels)
        self.parent.assertEqual(result.logits.shape, (self.batch_size, self.num_labels))

    def create_and_check_for_token_classification(
            self, config, input_ids, token_type_ids, input_mask, sequence_labels, token_labels, choice_labels
    ):
        config.num_labels = self.num_labels
        model = {{cookiecutter.camelcase_modelname}}ForTokenClassification(config=config)
        model.to(torch_device)
        model.eval()
        result = model(input_ids, attention_mask=input_mask, token_type_ids=token_type_ids, labels=token_labels)
        self.parent.assertEqual(result.logits.shape, (self.batch_size, self.seq_length, self.num_labels))

    def create_and_check_for_multiple_choice(
            self, config, input_ids, token_type_ids, input_mask, sequence_labels, token_labels, choice_labels
    ):
        config.num_choices = self.num_choices
        model = {{cookiecutter.camelcase_modelname}}ForMultipleChoice(config=config)
        model.to(torch_device)
        model.eval()
        multiple_choice_inputs_ids = input_ids.unsqueeze(1).expand(-1, self.num_choices, -1).contiguous()
        multiple_choice_token_type_ids = token_type_ids.unsqueeze(1).expand(-1, self.num_choices, -1).contiguous()
        multiple_choice_input_mask = input_mask.unsqueeze(1).expand(-1, self.num_choices, -1).contiguous()
        result = model(
            multiple_choice_inputs_ids,
            attention_mask=multiple_choice_input_mask,
            token_type_ids=multiple_choice_token_type_ids,
            labels=choice_labels,
        )
        self.parent.assertEqual(result.logits.shape, (self.batch_size, self.num_choices))

    def prepare_config_and_inputs_for_common(self):
        config_and_inputs = self.prepare_config_and_inputs()
        (
            config,
            input_ids,
            token_type_ids,
            input_mask,
            sequence_labels,
            token_labels,
            choice_labels,
        ) = config_and_inputs
        inputs_dict = {"input_ids": input_ids, "token_type_ids": token_type_ids, "attention_mask": input_mask}
        return config, inputs_dict


@require_torch
class {{cookiecutter.camelcase_modelname}}ModelTest(ModelTesterMixin, unittest.TestCase):

    all_model_classes = (
        (
            {{cookiecutter.camelcase_modelname}}Model,
            {{cookiecutter.camelcase_modelname}}ForMaskedLM,
            {{cookiecutter.camelcase_modelname}}ForMultipleChoice,
            {{cookiecutter.camelcase_modelname}}ForQuestionAnswering,
            {{cookiecutter.camelcase_modelname}}ForSequenceClassification,
            {{cookiecutter.camelcase_modelname}}ForTokenClassification,
        )
        if is_torch_available()
        else ()
    )

    def setUp(self):
        self.model_tester = {{cookiecutter.camelcase_modelname}}ModelTester(self)
        self.config_tester = ConfigTester(self, config_class={{cookiecutter.camelcase_modelname}}Config, hidden_size=37)

    def test_config(self):
        self.config_tester.run_common_tests()

    def test_model(self):
        config_and_inputs = self.model_tester.prepare_config_and_inputs()
        self.model_tester.create_and_check_model(*config_and_inputs)

    def test_for_masked_lm(self):
        config_and_inputs = self.model_tester.prepare_config_and_inputs()
        self.model_tester.create_and_check_for_masked_lm(*config_and_inputs)

    def test_for_multiple_choice(self):
        config_and_inputs = self.model_tester.prepare_config_and_inputs()
        self.model_tester.create_and_check_for_multiple_choice(*config_and_inputs)

    def test_for_question_answering(self):
        config_and_inputs = self.model_tester.prepare_config_and_inputs()
        self.model_tester.create_and_check_for_question_answering(*config_and_inputs)

    def test_for_sequence_classification(self):
        config_and_inputs = self.model_tester.prepare_config_and_inputs()
        self.model_tester.create_and_check_for_sequence_classification(*config_and_inputs)

    def test_for_token_classification(self):
        config_and_inputs = self.model_tester.prepare_config_and_inputs()
        self.model_tester.create_and_check_for_token_classification(*config_and_inputs)

    @slow
    def test_model_from_pretrained(self):
        for model_name in {{cookiecutter.uppercase_modelname}}_PRETRAINED_MODEL_ARCHIVE_LIST[:1]:
            model = {{cookiecutter.camelcase_modelname}}Model.from_pretrained(model_name)
            self.assertIsNotNone(model)


{% else -%}
import tempfile
import unittest

import timeout_decorator  # noqa

from transformers import is_torch_available
from transformers.testing_utils import require_torch, slow, torch_device

from .test_configuration_common import ConfigTester
from .test_modeling_common import ModelTesterMixin, ids_tensor


if is_torch_available():
    import torch

    from transformers import (
        {{cookiecutter.camelcase_modelname}}Config,
        {{cookiecutter.camelcase_modelname}}ForConditionalGeneration,
        {{cookiecutter.camelcase_modelname}}ForQuestionAnswering,
        {{cookiecutter.camelcase_modelname}}ForSequenceClassification,
        {{cookiecutter.camelcase_modelname}}Model,
    )
    from transformers.modeling_{{cookiecutter.lowercase_modelname}} import (
        _prepare_{{cookiecutter.lowercase_modelname}}_decoder_inputs,
        invert_mask,
        shift_tokens_right,
    )
PGE_ARTICLE = """ PG&E stated it scheduled the blackouts in response to forecasts for high winds amid dry conditions. The aim is to reduce the risk of wildfires. Nearly 800 thousand customers were scheduled to be affected by the shutoffs which were expected to last through at least midday tomorrow."""


@require_torch
class ModelTester:
    def __init__(
        self,
        parent,
    ):
        self.parent = parent
        self.batch_size = 13
        self.seq_length = 7
        self.is_training = True
        self.use_labels = False
        self.vocab_size = 99
        self.hidden_size = 16
        self.num_hidden_layers = 2
        self.num_attention_heads = 4
        self.intermediate_size = 4
        self.hidden_act = "gelu"
        self.hidden_dropout_prob = 0.1
        self.attention_probs_dropout_prob = 0.1
        self.max_position_embeddings = 20
        self.eos_token_id = 2
        self.pad_token_id = 1
        self.bos_token_id = 0
        torch.manual_seed(0)

    def prepare_config_and_inputs(self):
        input_ids = ids_tensor([self.batch_size, self.seq_length], self.vocab_size).clamp(
            3,
        )
        input_ids[:, -1] = 2  # Eos Token

        config = {{cookiecutter.camelcase_modelname}}Config(
            vocab_size=self.vocab_size,
            hidden_size=self.hidden_size,
            encoder_layers=self.num_hidden_layers,
            decoder_layers=self.num_hidden_layers,
            encoder_attention_heads=self.num_attention_heads,
            decoder_attention_heads=self.num_attention_heads,
            encoder_ffn_dim=self.intermediate_size,
            decoder_ffn_dim=self.intermediate_size,
            dropout=self.hidden_dropout_prob,
            attention_dropout=self.attention_probs_dropout_prob,
            max_position_embeddings=self.max_position_embeddings,
            eos_token_id=self.eos_token_id,
            bos_token_id=self.bos_token_id,
            pad_token_id=self.pad_token_id,
        )
        inputs_dict = prepare_{{cookiecutter.lowercase_modelname}}_inputs_dict(config, input_ids)
        return config, inputs_dict

    def prepare_config_and_inputs_for_common(self):
        config, inputs_dict = self.prepare_config_and_inputs()
        inputs_dict["decoder_input_ids"] = inputs_dict["input_ids"]
        inputs_dict["decoder_attention_mask"] = inputs_dict["attention_mask"]
        inputs_dict["use_cache"] = False
        return config, inputs_dict


def prepare_{{cookiecutter.lowercase_modelname}}_inputs_dict(
    config,
    input_ids,
    attention_mask=None,
):
    if attention_mask is None:
        attention_mask = input_ids.ne(config.pad_token_id)
    return {
        "input_ids": input_ids,
        "attention_mask": attention_mask,
    }


@require_torch
class {{cookiecutter.uppercase_modelname}}ModelTest(ModelTesterMixin, unittest.TestCase):
    all_model_classes = (
        ({{cookiecutter.camelcase_modelname}}Model, {{cookiecutter.camelcase_modelname}}ForConditionalGeneration, {{cookiecutter.camelcase_modelname}}ForSequenceClassification, {{cookiecutter.camelcase_modelname}}ForQuestionAnswering)
        if is_torch_available()
        else ()
    )
    all_generative_model_classes = ({{cookiecutter.camelcase_modelname}}ForConditionalGeneration,) if is_torch_available() else ()
    is_encoder_decoder = True
    test_pruning = False
    test_head_masking = False
    test_missing_keys = False

    def setUp(self):
        self.model_tester = ModelTester(self)
        self.config_tester = ConfigTester(self, config_class={{cookiecutter.camelcase_modelname}}Config)

    def test_config(self):
        self.config_tester.run_common_tests()

    def test_initialization_more(self):
        config, inputs_dict = self.model_tester.prepare_config_and_inputs()
        model = {{cookiecutter.camelcase_modelname}}Model(config)
        model.to(torch_device)
        model.eval()
        # test init
        self.assertTrue((model.encoder.embed_tokens.weight == model.shared.weight).all().item())

        def _check_var(module):
            """Check that we initialized various parameters from N(0, config.initializer_range)."""
            self.assertAlmostEqual(torch.std(module.weight).item(), config.initializer_range, 2)

        _check_var(model.encoder.embed_tokens)
        _check_var(model.encoder.layers[0].self_attn.k_proj)
        _check_var(model.encoder.layers[0].fc1)
        _check_var(model.encoder.embed_positions)

    def test_advanced_inputs(self):
        config, inputs_dict = self.model_tester.prepare_config_and_inputs()
        config.use_cache = False
        inputs_dict["input_ids"][:, -2:] = config.pad_token_id
        decoder_input_ids, decoder_attn_mask, causal_mask = _prepare_{{cookiecutter.lowercase_modelname}}_decoder_inputs(
            config, inputs_dict["input_ids"]
        )
        model = {{cookiecutter.camelcase_modelname}}Model(config).to(torch_device).eval()

        decoder_features_with_created_mask = model(**inputs_dict)[0]
        decoder_features_with_passed_mask = model(
            decoder_attention_mask=invert_mask(decoder_attn_mask), decoder_input_ids=decoder_input_ids, **inputs_dict
        )[0]
        assert_tensors_close(decoder_features_with_passed_mask, decoder_features_with_created_mask)
        useless_mask = torch.zeros_like(decoder_attn_mask)
        decoder_features = model(decoder_attention_mask=useless_mask, **inputs_dict)[0]
        self.assertTrue(isinstance(decoder_features, torch.Tensor))  # no hidden states or attentions
        self.assertEqual(
            decoder_features.size(), (self.model_tester.batch_size, self.model_tester.seq_length, config.hidden_size)
        )
        if decoder_attn_mask.min().item() < -1e3:  # some tokens were masked
            self.assertFalse((decoder_features_with_created_mask == decoder_features).all().item())

        # Test different encoder attention masks
        decoder_features_with_long_encoder_mask = model(
            inputs_dict["input_ids"], attention_mask=inputs_dict["attention_mask"].long()
        )[0]
        assert_tensors_close(decoder_features_with_long_encoder_mask, decoder_features_with_created_mask)

    def test_save_load_strict(self):
        config, inputs_dict = self.model_tester.prepare_config_and_inputs()
        for model_class in self.all_model_classes:
            model = model_class(config)

            with tempfile.TemporaryDirectory() as tmpdirname:
                model.save_pretrained(tmpdirname)
                model2, info = model_class.from_pretrained(tmpdirname, output_loading_info=True)
            self.assertEqual(info["missing_keys"], [])

    @unittest.skip("Passing inputs_embeds not implemented for {{cookiecutter.camelcase_modelname}}.")
    def test_inputs_embeds(self):
        pass


@require_torch
class {{cookiecutter.camelcase_modelname}}HeadTests(unittest.TestCase):
    vocab_size = 99

    def _get_config_and_data(self):
        input_ids = torch.tensor(
            [
                [71, 82, 18, 33, 46, 91, 2],
                [68, 34, 26, 58, 30, 82, 2],
                [5, 97, 17, 39, 94, 40, 2],
                [76, 83, 94, 25, 70, 78, 2],
                [87, 59, 41, 35, 48, 66, 2],
                [55, 13, 16, 58, 5, 2, 1],  # note padding
                [64, 27, 31, 51, 12, 75, 2],
                [52, 64, 86, 17, 83, 39, 2],
                [48, 61, 9, 24, 71, 82, 2],
                [26, 1, 60, 48, 22, 13, 2],
                [21, 5, 62, 28, 14, 76, 2],
                [45, 98, 37, 86, 59, 48, 2],
                [70, 70, 50, 9, 28, 0, 2],
            ],
            dtype=torch.long,
            device=torch_device,
        )

        batch_size = input_ids.shape[0]
        config = {{cookiecutter.camelcase_modelname}}Config(
            vocab_size=self.vocab_size,
            hidden_size=24,
            encoder_layers=2,
            decoder_layers=2,
            encoder_attention_heads=2,
            decoder_attention_heads=2,
            encoder_ffn_dim=32,
            decoder_ffn_dim=32,
            max_position_embeddings=48,
            eos_token_id=2,
            pad_token_id=1,
            bos_token_id=0,
            return_dict=True,
        )
        return config, input_ids, batch_size

    def test_sequence_classification_forward(self):
        config, input_ids, batch_size = self._get_config_and_data()
        labels = _long_tensor([2] * batch_size).to(torch_device)
        config.num_labels = 3
        model = {{cookiecutter.camelcase_modelname}}ForSequenceClassification(config)
        model.to(torch_device)
        outputs = model(input_ids=input_ids, decoder_input_ids=input_ids, labels=labels)
        expected_shape = torch.Size((batch_size, config.num_labels))
        self.assertEqual(outputs["logits"].shape, expected_shape)
        self.assertIsInstance(outputs["loss"].item(), float)

    def test_question_answering_forward(self):
        config, input_ids, batch_size = self._get_config_and_data()
        sequence_labels = ids_tensor([batch_size], 2).to(torch_device)
        model = {{cookiecutter.camelcase_modelname}}ForQuestionAnswering(config)
        model.to(torch_device)
        outputs = model(
            input_ids=input_ids,
            start_positions=sequence_labels,
            end_positions=sequence_labels,
        )

        self.assertEqual(outputs["start_logits"].shape, input_ids.shape)
        self.assertEqual(outputs["end_logits"].shape, input_ids.shape)
        self.assertIsInstance(outputs["loss"].item(), float)

    @timeout_decorator.timeout(1)
    def test_lm_forward(self):
        config, input_ids, batch_size = self._get_config_and_data()
        lm_labels = ids_tensor([batch_size, input_ids.shape[1]], self.vocab_size).to(torch_device)
        lm_model = {{cookiecutter.camelcase_modelname}}ForConditionalGeneration(config)
        lm_model.to(torch_device)
        outputs = lm_model(input_ids=input_ids, labels=lm_labels)
        expected_shape = (batch_size, input_ids.shape[1], config.vocab_size)
        self.assertEqual(outputs["logits"].shape, expected_shape)
        self.assertIsInstance(outputs["loss"].item(), float)

    def test_lm_uneven_forward(self):
        config = {{cookiecutter.camelcase_modelname}}Config(
            vocab_size=self.vocab_size,
            hidden_size=14,
            encoder_layers=2,
            decoder_layers=2,
            encoder_attention_heads=2,
            decoder_attention_heads=2,
            encoder_ffn_dim=8,
            decoder_ffn_dim=8,
            max_position_embeddings=48,
            return_dict=True,
        )
        lm_model = {{cookiecutter.camelcase_modelname}}ForConditionalGeneration(config).to(torch_device)
        context = torch.Tensor([[71, 82, 18, 33, 46, 91, 2], [68, 34, 26, 58, 30, 2, 1]]).long().to(torch_device)
        summary = torch.Tensor([[82, 71, 82, 18, 2], [58, 68, 2, 1, 1]]).long().to(torch_device)
        outputs = lm_model(input_ids=context, decoder_input_ids=summary, labels=summary)
        expected_shape = (*summary.shape, config.vocab_size)
        self.assertEqual(outputs["logits"].shape, expected_shape)

    def test_generate_beam_search(self):
        input_ids = torch.Tensor([[71, 82, 2], [68, 34, 2]]).long().to(torch_device)
        config = {{cookiecutter.camelcase_modelname}}Config(
            vocab_size=self.vocab_size,
            hidden_size=24,
            encoder_layers=2,
            decoder_layers=2,
            encoder_attention_heads=2,
            decoder_attention_heads=2,
            encoder_ffn_dim=32,
            decoder_ffn_dim=32,
            max_position_embeddings=48,
            eos_token_id=2,
            pad_token_id=1,
            bos_token_id=0,
        )
        lm_model = {{cookiecutter.camelcase_modelname}}ForConditionalGeneration(config).to(torch_device)
        lm_model.eval()

        max_length = 5
        generated_ids = lm_model.generate(
            input_ids.clone(),
            do_sample=True,
            num_return_sequences=1,
            num_beams=2,
            no_repeat_ngram_size=3,
            max_length=max_length,
        )
        self.assertEqual(generated_ids.shape, (input_ids.shape[0], max_length))

    def test_shift_tokens_right(self):
        input_ids = torch.Tensor([[71, 82, 18, 33, 2, 1, 1], [68, 34, 26, 58, 30, 82, 2]]).long()
        shifted = shift_tokens_right(input_ids, 1)
        n_pad_before = input_ids.eq(1).float().sum()
        n_pad_after = shifted.eq(1).float().sum()
        self.assertEqual(shifted.shape, input_ids.shape)
        self.assertEqual(n_pad_after, n_pad_before - 1)
        self.assertTrue(torch.eq(shifted[:, 0], 2).all())

    def test_generate_fp16(self):
        config, input_ids, batch_size = self._get_config_and_data()
        attention_mask = input_ids.ne(1).to(torch_device)
        model = {{cookiecutter.camelcase_modelname}}ForConditionalGeneration(config).eval().to(torch_device)
        if torch_device == "cuda":
            model.half()
        model.generate(input_ids, attention_mask=attention_mask)
        model.generate(num_beams=4, do_sample=True, early_stopping=False, num_return_sequences=3)

    def test_dummy_inputs(self):
        config, *_ = self._get_config_and_data()
        model = {{cookiecutter.camelcase_modelname}}ForConditionalGeneration(config).eval().to(torch_device)
        model(**model.dummy_inputs)

    def test_prepare_{{cookiecutter.lowercase_modelname}}_decoder_inputs(self):
        config, *_ = self._get_config_and_data()
        input_ids = _long_tensor(([4, 4, 2]))
        decoder_input_ids = _long_tensor([[26388, 2, config.pad_token_id]])
        ignore = float("-inf")
        decoder_input_ids, decoder_attn_mask, causal_mask = _prepare_{{cookiecutter.lowercase_modelname}}_decoder_inputs(
            config, input_ids, decoder_input_ids
        )
        expected_causal_mask = torch.tensor(
            [[0, ignore, ignore], [0, 0, ignore], [0, 0, 0]]  # never attend to the final token, because its pad
        ).to(input_ids.device)
        self.assertEqual(decoder_attn_mask.size(), decoder_input_ids.size())
        self.assertTrue(torch.eq(expected_causal_mask, causal_mask).all())

    def test_resize_tokens_embeddings_more(self):
        config, input_ids, _ = self._get_config_and_data()

        def _get_embs(m):
            return (m.get_input_embeddings().weight.data.clone(), m.get_output_embeddings().weight.data.clone())

        model = {{cookiecutter.camelcase_modelname}}ForConditionalGeneration(config).eval().to(torch_device)
        input, output = _get_embs(model)
        self.assertTrue(torch.eq(input, output).all())
        new_vocab_size = 45
        model.resize_token_embeddings(new_vocab_size)
        input_new, output_new = _get_embs(model)
        self.assertEqual(input_new.shape, (new_vocab_size, config.hidden_size))
        self.assertEqual(output_new.shape, (new_vocab_size, config.hidden_size))
        self.assertTrue(torch.eq(input_new, output_new).all())


def assert_tensors_close(a, b, atol=1e-12, prefix=""):
    """If tensors have different shapes, different values or a and b are not both tensors, raise a nice Assertion error."""
    if a is None and b is None:
        return True
    try:
        if torch.allclose(a, b, atol=atol):
            return True
        raise
    except Exception:
        pct_different = (torch.gt((a - b).abs(), atol)).float().mean().item()
        if a.numel() > 100:
            msg = f"tensor values are {pct_different:.1%} percent different."
        else:
            msg = f"{a} != {b}"
        if prefix:
            msg = prefix + ": " + msg
        raise AssertionError(msg)


def _long_tensor(tok_lst):
    return torch.tensor(tok_lst, dtype=torch.long, device=torch_device)

{% endif -%}
