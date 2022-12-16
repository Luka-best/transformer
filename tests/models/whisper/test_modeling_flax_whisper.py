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


import inspect
import unittest

from transformers import WhisperConfig, is_flax_available
from transformers.testing_utils import require_flax, slow
from transformers.utils import cached_property
from transformers.utils.import_utils import is_datasets_available

from ...test_configuration_common import ConfigTester
from ...test_modeling_flax_common import FlaxModelTesterMixin, floats_tensor


if is_datasets_available():
    import datasets
    from datasets import load_dataset

if is_flax_available():
    import numpy as np

    import jax
    from transformers import (
        FlaxWhisperForConditionalGeneration,
        FlaxWhisperModel,
        WhisperFeatureExtractor,
        WhisperProcessor,
    )


@require_flax
class FlaxWhisperModelTester:
    config_cls = WhisperConfig
    config_updates = {}
    hidden_act = "gelu"

    def __init__(
        self,
        parent,
        batch_size=1,
        seq_length=3000,
        is_training=True,
        use_labels=False,
        vocab_size=99,
        d_model=384,
        decoder_attention_heads=6,
        decoder_ffn_dim=1536,
        decoder_layers=4,
        encoder_attention_heads=6,
        encoder_ffn_dim=1536,
        encoder_layers=4,
        input_channels=1,
        hidden_act="gelu",
        hidden_dropout_prob=0.1,
        attention_probs_dropout_prob=0.1,
        max_position_embeddings=20,
        max_source_positions=1500,
        max_target_positions=448,
        bos_token_id=98,
        eos_token_id=98,
        pad_token_id=0,
        num_mel_bins=80,
        decoder_start_token_id=85,
        num_conv_layers=1,
        suppress_tokens=None,
        begin_suppress_tokens=None,
    ):
        self.parent = parent
        self.batch_size = batch_size
        self.seq_length = seq_length
        self.is_training = is_training
        self.use_labels = use_labels
        self.vocab_size = vocab_size
        self.d_model = d_model
        self.hidden_size = d_model
        self.num_hidden_layers = encoder_layers
        self.num_attention_heads = encoder_attention_heads
        self.decoder_attention_heads = decoder_attention_heads
        self.decoder_ffn_dim = decoder_ffn_dim
        self.decoder_layers = decoder_layers
        self.encoder_attention_heads = encoder_attention_heads
        self.encoder_ffn_dim = encoder_ffn_dim
        self.encoder_layers = encoder_layers
        self.encoder_seq_length = seq_length // 2
        self.decoder_seq_length = 1
        self.input_channels = input_channels
        self.hidden_act = hidden_act
        self.hidden_dropout_prob = hidden_dropout_prob
        self.attention_probs_dropout_prob = attention_probs_dropout_prob
        self.num_mel_bins = num_mel_bins
        self.max_position_embeddings = max_position_embeddings
        self.max_source_positions = max_source_positions
        self.max_target_positions = max_target_positions
        self.eos_token_id = eos_token_id
        self.pad_token_id = pad_token_id
        self.bos_token_id = bos_token_id
        self.decoder_start_token_id = decoder_start_token_id
        self.num_conv_layers = num_conv_layers
        self.suppress_tokens = suppress_tokens
        self.begin_suppress_tokens = begin_suppress_tokens

    def prepare_config_and_inputs_for_common(self):
        input_features = floats_tensor([self.batch_size, self.num_mel_bins, self.seq_length], self.vocab_size)

        decoder_input_ids = np.array(self.batch_size * [[self.decoder_start_token_id]])

        config = WhisperConfig(
            vocab_size=self.vocab_size,
            num_mel_bins=self.num_mel_bins,
            decoder_start_token_id=self.decoder_start_token_id,
            is_encoder_decoder=True,
            activation_function=self.hidden_act,
            dropout=self.hidden_dropout_prob,
            attention_dropout=self.attention_probs_dropout_prob,
            max_source_positions=self.max_source_positions,
            max_target_positions=self.max_target_positions,
            pad_token_id=self.pad_token_id,
            bos_token_id=self.bos_token_id,
            eos_token_id=self.eos_token_id,
            tie_word_embeddings=True,
            d_model=self.d_model,
            decoder_attention_heads=self.decoder_attention_heads,
            decoder_ffn_dim=self.decoder_ffn_dim,
            decoder_layers=self.decoder_layers,
            encoder_attention_heads=self.encoder_attention_heads,
            encoder_ffn_dim=self.encoder_ffn_dim,
            encoder_layers=self.encoder_layers,
            suppress_tokens=self.suppress_tokens,
            begin_suppress_tokens=self.begin_suppress_tokens,
        )
        inputs_dict = prepare_whisper_inputs_dict(config, input_features, decoder_input_ids)
        return config, inputs_dict


def prepare_whisper_inputs_dict(
    config,
    input_ids,
    decoder_input_ids,
    attention_mask=None,
    decoder_attention_mask=None,
):
    if attention_mask is None:
        attention_mask = np.not_equal(input_ids, config.pad_token_id).astype(np.int8)
    if decoder_attention_mask is None:
        decoder_attention_mask = np.concatenate(
            [
                np.ones(decoder_input_ids[:, :1].shape, dtype=np.int8),
                np.not_equal(decoder_input_ids[:, 1:], config.pad_token_id).astype(np.int8),
            ],
            axis=-1,
        )
    return {
        "input_features": input_ids,
        "decoder_input_ids": decoder_input_ids,
        "attention_mask": attention_mask,
        "decoder_attention_mask": decoder_attention_mask,
    }


@require_flax
class FlaxWhisperModelTest(FlaxModelTesterMixin, unittest.TestCase):
    all_model_classes = (
        (
            FlaxWhisperForConditionalGeneration,
            FlaxWhisperModel,
        )
        if is_flax_available()
        else ()
    )
    all_generative_model_classes = (FlaxWhisperForConditionalGeneration,) if is_flax_available() else ()
    is_encoder_decoder = True
    test_pruning = False
    test_head_masking = False
    test_onnx = False

    def setUp(self):
        self.model_tester = FlaxWhisperModelTester(self)
        self.config_tester = ConfigTester(self, config_class=WhisperConfig)

    def test_config(self):
        self.config_tester.run_common_tests()

    # overwrite because of `input_features`
    def test_forward_signature(self):
        config, _ = self.model_tester.prepare_config_and_inputs_for_common()

        for model_class in self.all_model_classes:
            model = model_class(config)
            signature = inspect.signature(model.__call__)
            # signature.parameters is an OrderedDict => so arg_names order is deterministic
            arg_names = [*signature.parameters.keys()]

            expected_arg_names = ["input_features", "decoder_input_ids"]
            self.assertListEqual(arg_names[:2], expected_arg_names)

    # overwrite because of `input_features`
    def test_jit_compilation(self):
        config, inputs_dict = self.model_tester.prepare_config_and_inputs_for_common()

        for model_class in self.all_model_classes:
            with self.subTest(model_class.__name__):
                prepared_inputs_dict = self._prepare_for_class(inputs_dict, model_class)
                model = model_class(config)

                @jax.jit
                def model_jitted(input_features, decoder_input_ids, **kwargs):
                    return model(input_features=input_features, decoder_input_ids=decoder_input_ids, **kwargs)

                with self.subTest("JIT Enabled"):
                    jitted_outputs = model_jitted(**prepared_inputs_dict).to_tuple()

                with self.subTest("JIT Disabled"):
                    with jax.disable_jit():
                        outputs = model_jitted(**prepared_inputs_dict).to_tuple()

                self.assertEqual(len(outputs), len(jitted_outputs))
                for jitted_output, output in zip(jitted_outputs, outputs):
                    self.assertEqual(jitted_output.shape, output.shape)


def _assert_tensors_equal(a, b, atol=1e-12, prefix=""):
    """If tensors not close, or a and b arent both tensors, raise a nice Assertion error."""
    if a is None and b is None:
        return True
    try:
        if _assert_tensors_equal(a, b, atol=atol):
            return True
        raise
    except Exception:
        if len(prefix) > 0:
            prefix = f"{prefix}: "
        raise AssertionError(f"{prefix}{a} != {b}")


def _long_tensor(tok_lst):
    return np.array(tok_lst, dtype=np.int32)


@slow
@require_flax
class FlaxWhisperModelIntegrationTest(unittest.TestCase):
    @cached_property
    def default_processor(self):
        return WhisperProcessor.from_pretrained("openai/whisper-base")

    def _load_datasamples(self, num_samples):
        ds = load_dataset("hf-internal-testing/librispeech_asr_dummy", "clean", split="validation")
        # automatic decoding with librispeech
        speech_samples = ds.sort("id").select(range(num_samples))[:num_samples]["audio"]

        return [x["array"] for x in speech_samples]

    def test_tiny_logits_librispeech(self):
        model = FlaxWhisperModel.from_pretrained("openai/whisper-tiny", from_pt=True)
        input_speech = self._load_datasamples(1)
        feature_extractor = WhisperFeatureExtractor()
        input_features = feature_extractor(input_speech, return_tensors="np").input_features

        logits = model(
            input_features,
            decoder_input_ids=np.array([[50258, 50259, 50359]]),
            output_hidden_states=False,
            output_attentions=False,
            return_dict=False,
        )

        # fmt: off
        EXPECTED_LOGITS = np.array(
            [
                2.9892, -6.7607, 5.7348, 3.6096, 0.2152, -5.7321, 4.8855, -1.6407,
                0.2823, -1.5718, 10.4269, 3.4427, 0.0219, -8.0612, 3.4784, 8.4246,
                4.0575, -2.2864, 11.1084, 0.9963, 0.9884, -8.5154, -3.5469, -9.3713,
                0.9786, 3.5435, 7.4850, -5.2579, -1.4366, 10.4841
            ]
        )
        # fmt: on
        self.assertTrue(np.allclose(logits[0][0, 0, :30], EXPECTED_LOGITS, atol=1e-4))

    def test_small_en_logits_librispeech(self):
        model = FlaxWhisperModel.from_pretrained("openai/whisper-small.en", from_pt=True)
        input_speech = self._load_datasamples(1)
        feature_extractor = WhisperFeatureExtractor()
        input_features = feature_extractor(input_speech, return_tensors="np").input_features

        logits = model(
            input_features,
            decoder_input_ids=np.array([model.config.decoder_start_token_id]),
            output_hidden_states=False,
            output_attentions=False,
            return_dict=False,
        )

        logits = logits[0] @ model.params["model"]["decoder"]["embed_tokens"]["embedding"].T

        # fmt: off
        EXPECTED_LOGITS = np.array(
            [
                -3.6784, -7.7211, -9.5070, -11.9286, -7.6489, -9.7026, -5.6188,
                -8.0104, -4.6238, -5.1833, -9.0485, -3.4079, -5.4874, -2.6935,
                -6.3479, -7.3398, -6.9558, -7.6867, -7.4748, -8.3463, -9.9781,
                -10.8389, -10.3105, -11.7201, -9.7261, -7.1590, -5.9272, -12.4509,
                -11.1146, -8.1918
            ]
        )
        # fmt: on
        self.assertTrue(np.allclose(logits[0, 0, :30], EXPECTED_LOGITS, atol=1e-4))

    def test_large_logits_librispeech(self):
        model = FlaxWhisperModel.from_pretrained("openai/whisper-large", from_pt=True)
        input_speech = self._load_datasamples(1)
        processor = WhisperProcessor.from_pretrained("openai/whisper-large")
        processed_inputs = processor(
            audio=input_speech, text="This part of the speech", add_special_tokens=False, return_tensors="np"
        )
        input_features = processed_inputs.input_features
        decoder_input_ids = processed_inputs.labels

        logits = model(
            input_features,
            decoder_input_ids=decoder_input_ids,
            output_hidden_states=False,
            output_attentions=False,
            return_dict=False,
        )

        logits = logits[0] @ model.params["model"]["decoder"]["embed_tokens"]["embedding"].T

        # fmt: off
        EXPECTED_LOGITS = np.array(
            [
                2.1382, 0.9381, 4.4671, 3.5589, 2.4022, 3.8576, -0.6521, 2.5472,
                1.8301, 1.9957, 2.3432, 1.4678, 0.5459, 2.2597, 1.5179, 2.5357,
                1.1624, 0.6194, 1.0757, 1.8259, 2.4076, 1.6601, 2.3503, 1.3376,
                1.9891, 1.8635, 3.8931, 5.3699, 4.4772, 3.9184
            ]
        )
        # fmt: on
        self.assertTrue(np.allclose(logits[0, 0, :30], EXPECTED_LOGITS, atol=1e-4))

    def test_tiny_en_generation(self):
        processor = WhisperProcessor.from_pretrained("openai/whisper-tiny.en")
        model = FlaxWhisperForConditionalGeneration.from_pretrained("openai/whisper-tiny.en", from_pt=True)
        model.config.decoder_start_token_id = 50257

        input_speech = self._load_datasamples(1)
        input_features = processor.feature_extractor(
            raw_speech=input_speech, sampling_rate=processor.feature_extractor.sampling_rate, return_tensors="jax"
        ).input_features

        generated_ids = model.generate(input_features, num_beams=5, max_length=20).sequences
        transcript = processor.tokenizer.decode(generated_ids[0])

        EXPECTED_TRANSCRIPT = (
            "<|startoftranscript|><|en|><|transcribe|><|notimestamps|> Mr. Quilter is the apostle of the middle"
            " classes and we are glad"
        )
        self.assertEqual(transcript, EXPECTED_TRANSCRIPT)

    def test_tiny_generation(self):
        processor = WhisperProcessor.from_pretrained("openai/whisper-tiny")
        model = FlaxWhisperForConditionalGeneration.from_pretrained("openai/whisper-tiny", from_pt=True)

        input_speech = self._load_datasamples(1)
        input_features = processor.feature_extractor(
            raw_speech=input_speech, sampling_rate=processor.feature_extractor.sampling_rate, return_tensors="jax"
        ).input_features

        generated_ids = model.generate(input_features, num_beams=5, max_length=20).sequences
        transcript = processor.tokenizer.decode(generated_ids[0])

        EXPECTED_TRANSCRIPT = (
            "<|startoftranscript|><|en|><|transcribe|><|notimestamps|> Mr. Quilter is the apostle of the middle"
            " classes and we are glad"
        )
        self.assertEqual(transcript, EXPECTED_TRANSCRIPT)

    def test_large_generation(self):
        processor = WhisperProcessor.from_pretrained("openai/whisper-large")
        model = FlaxWhisperForConditionalGeneration.from_pretrained("openai/whisper-large", from_pt=True)

        input_speech = self._load_datasamples(1)
        input_features = processor.feature_extractor(
            raw_speech=input_speech, sampling_rate=processor.feature_extractor.sampling_rate, return_tensors="jax"
        ).input_features

        prompt_ids = processor.get_decoder_prompt_ids(language="en", task="transcribe")
        model.config.forced_decoder_ids = [[i[0] - 1, i[1]] for i in prompt_ids[1:]]

        generated_ids = model.generate(input_features, num_beams=5, max_length=20).sequences
        transcript = processor.tokenizer.decode(generated_ids[0], skip_special_tokens=True)

        EXPECTED_TRANSCRIPT = " Mr. Quilter is the apostle of the middle classes and we are glad"
        self.assertEqual(transcript, EXPECTED_TRANSCRIPT)

    def test_large_generation_multilingual(self):
        processor = WhisperProcessor.from_pretrained("openai/whisper-large")
        model = FlaxWhisperForConditionalGeneration.from_pretrained("openai/whisper-large", from_pt=True)

        ds = load_dataset("common_voice", "ja", split="test", streaming=True)
        ds = ds.cast_column("audio", datasets.Audio(sampling_rate=16_000))
        input_speech = next(iter(ds))["audio"]["array"]
        input_features = processor.feature_extractor(raw_speech=input_speech, return_tensors="np")

        prompt_ids = processor.get_decoder_prompt_ids(language="ja", task="transcribe")
        model.config.forced_decoder_ids = [[i[0] - 1, i[1]] for i in prompt_ids[1:]]
        generated_ids = model.generate(input_features, do_sample=False, max_length=20).sequences
        transcript = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

        EXPECTED_TRANSCRIPT = "木村さんに電話を貸してもらいました"
        self.assertEqual(transcript, EXPECTED_TRANSCRIPT)

        prompt_ids = processor.get_decoder_prompt_ids(language="en", task="transcribe")
        model.config.forced_decoder_ids = [[i[0] - 1, i[1]] for i in prompt_ids[1:]]
        generated_ids = model.generate(
            input_features,
            do_sample=False,
            max_length=20,
        ).sequences
        transcript = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

        EXPECTED_TRANSCRIPT = " Kimura-san called me."
        self.assertEqual(transcript, EXPECTED_TRANSCRIPT)

        prompt_ids = processor.get_decoder_prompt_ids(language="ja", task="translate")
        model.config.forced_decoder_ids = [[i[0] - 1, i[1]] for i in prompt_ids[1:]]
        generated_ids = model.generate(input_features, do_sample=False, max_length=20).sequences
        transcript = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

        EXPECTED_TRANSCRIPT = " I borrowed a phone from Kimura san"
        self.assertEqual(transcript, EXPECTED_TRANSCRIPT)

    def test_large_batched_generation(self):
        processor = WhisperProcessor.from_pretrained("openai/whisper-large")
        model = FlaxWhisperForConditionalGeneration.from_pretrained("openai/whisper-large", from_pt=True)

        input_speech = self._load_datasamples(4)
        input_features = processor.feature_extractor(raw_speech=input_speech, return_tensors="np").input_features
        generated_ids = model.generate(input_features, max_length=20).sequences

        # fmt: off
        EXPECTED_LOGITS = np.array(
            [
                [50258, 50358, 50363, 2221, 13, 2326, 388, 391, 307, 264, 50244, 295, 264, 2808, 5359, 293, 321, 366, 5404, 281],
                [50258, 50358, 50363, 6966, 307, 2221, 13, 2326, 388, 391, 311, 9060, 1570, 1880, 813, 702, 1871, 13, 50257, 50257],
                [50258, 50358, 50363, 634, 5112, 505, 300, 412, 341, 42729, 3196, 295, 264, 1064, 11, 365, 5272, 293, 12904, 9256],
                [50258, 50358, 50363, 634, 575, 12525, 22618, 1968, 6144, 35617, 20084, 1756, 311, 589, 307, 534, 10281, 934, 439, 11]
            ]
        )
        # fmt: on

        self.assertTrue(np.allclose(generated_ids, EXPECTED_LOGITS))

        # fmt: off
        EXPECTED_TRANSCRIPT = [
            " Mr. Quilter is the apostle of the middle classes and we are glad to",
            " Nor is Mr. Quilter's manner less interesting than his matter.",
            " He tells us that at this festive season of the year, with Christmas and roast beef",
            " He has grave doubts whether Sir Frederick Layton's work is really Greek after all,",
        ]
        # fmt: on

        transcript = processor.batch_decode(generated_ids, skip_special_tokens=True)
        self.assertListEqual(transcript, EXPECTED_TRANSCRIPT)

    def test_tiny_en_batched_generation(self):
        processor = WhisperProcessor.from_pretrained("openai/whisper-tiny.en")
        model = FlaxWhisperForConditionalGeneration.from_pretrained("openai/whisper-tiny.en", from_pt=True)

        input_speech = self._load_datasamples(4)
        input_features = processor.feature_extractor(raw_speech=input_speech, return_tensors="np").input_features
        generated_ids = model.generate(input_features, max_length=20).sequences

        # fmt: off
        EXPECTED_LOGITS = np.array(
            [
                [50257, 50362, 1770, 13, 2264, 346, 353, 318, 262, 46329, 286, 262, 3504, 6097, 11, 290, 356, 389, 9675, 284],
                [50257, 50362, 5414, 318, 1770, 13, 2264, 346, 353, 338, 5642, 1342, 3499, 621, 465, 2300, 13, 50256, 50256, 50256],
                [50257, 50362, 679, 4952, 514, 326, 379, 428, 43856, 1622, 286, 262, 614, 11, 351, 6786, 290, 32595, 12023, 28236],
                [50257, 50362, 679, 468, 12296, 17188, 1771, 7361, 26113, 18881, 1122, 338, 670, 318, 1107, 8312, 706, 477, 290, 460]
            ]

        )
        # fmt: on

        self.assertTrue(np.allclose(generated_ids, EXPECTED_LOGITS))

        # fmt: off
        EXPECTED_TRANSCRIPT = [
            " Mr. Quilter is the apostle of the middle classes, and we are glad to",
            " Nor is Mr. Quilter's manner less interesting than his matter.",
            " He tells us that at this festive season of the year, with Christmas and roast beef looming",
            " He has grave doubts whether Sir Frederick Layton's work is really Greek after all and can",
        ]
        # fmt: on

        transcript = processor.batch_decode(generated_ids, skip_special_tokens=True)
        self.assertListEqual(transcript, EXPECTED_TRANSCRIPT)
