# coding=utf-8
# Copyright 2023 IBM and HuggingFace Inc. team. All rights reserved.
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
""" Testing suite for the PyTorch PatchTSMixer model. """

import inspect
import random
import tempfile
import unittest
from typing import Optional, Union

from huggingface_hub import hf_hub_download

from transformers import is_torch_available
from transformers.models.auto import get_values
from transformers.testing_utils import is_flaky, require_torch, slow, torch_device

from ...test_configuration_common import ConfigTester
from ...test_modeling_common import ModelTesterMixin, floats_tensor, ids_tensor
from ...test_pipeline_mixin import PipelineTesterMixin


TOLERANCE = 1e-4

if is_torch_available():
    import torch

    from transformers import (
        MODEL_FOR_TIME_SERIES_CLASSIFICATION_MAPPING,
        MODEL_FOR_TIME_SERIES_REGRESSION_MAPPING,
        PatchTSMixerConfig,
        PatchTSMixerForClassification,
        PatchTSMixerForForecasting,
        PatchTSMixerForMaskPretraining,
        PatchTSMixerForRegression,
        PatchTSMixerModel,
    )
    from transformers.models.patchtsmixer.modeling_patchtsmixer import (
        ForecastHead,
        LinearHead,
        PatchTSMixerEncoder,
        PretrainHead,
    )


@require_torch
class PatchTSMixerModelTester:
    def __init__(
        self,
        seq_len: int = 32,
        patch_len: int = 8,
        input_size: int = 3,
        stride: int = 8,
        # num_features: int = 128,
        hidden_size: int = 8,
        # num_layers: int = 8,
        num_hidden_layers: int = 2,
        expansion_factor: int = 2,
        dropout: float = 0.5,
        mode: str = "common_channel",
        gated_attn: bool = True,
        norm_mlp="LayerNorm",
        swin_hier: int = 0,
        # masking related
        mask_type: str = "random",
        mask_ratio=0.5,
        mask_patches: list = [2, 3],
        mask_patch_ratios: list = [1, 1],
        mask_value=0,
        masked_loss: bool = False,
        mask_mode: str = "mask_before_encoder",
        channel_consistent_masking: bool = True,
        scaling: Optional[Union[str, bool]] = "std",
        # Head related
        head_dropout: float = 0.2,
        # forecast related
        forecast_len: int = 16,
        out_channels: int = None,
        # Classification/regression related
        n_classes: int = 3,
        n_targets: int = 3,
        output_range: list = None,
        head_agg: str = None,
        # Trainer related
        batch_size=13,
        is_training=True,
        seed_number=42,
        post_init=True,
    ):
        self.input_size = input_size
        self.seq_len = seq_len
        self.patch_len = patch_len
        self.stride = stride
        # self.num_features = num_features
        self.hidden_size = hidden_size
        self.expansion_factor = expansion_factor
        # self.num_layers = num_layers
        self.num_hidden_layers = num_hidden_layers
        self.dropout = dropout
        self.mode = mode
        self.gated_attn = gated_attn
        self.norm_mlp = norm_mlp
        self.swin_hier = swin_hier
        self.scaling = scaling
        self.head_dropout = head_dropout
        # masking related
        self.mask_type = mask_type
        self.mask_ratio = mask_ratio
        self.mask_patches = mask_patches
        self.mask_patch_ratios = mask_patch_ratios
        self.mask_value = mask_value
        self.channel_consistent_masking = channel_consistent_masking
        self.mask_mode = mask_mode
        self.masked_loss = masked_loss
        # patching related
        self.patch_last = True
        # forecast related
        self.forecast_len = forecast_len
        self.out_channels = out_channels
        # classification/regression related
        self.n_classes = n_classes
        self.n_targets = n_targets
        self.output_range = output_range
        self.head_agg = head_agg
        # Trainer related
        self.batch_size = batch_size
        self.is_training = is_training
        self.seed_number = seed_number
        self.post_init = post_init

    def get_config(self):
        config_ = PatchTSMixerConfig(
            input_size=self.input_size,
            seq_len=self.seq_len,
            patch_len=self.patch_len,
            stride=self.stride,
            # num_features = self.num_features,
            num_features=self.hidden_size,
            expansion_factor=self.expansion_factor,
            # num_layers = self.num_layers,
            num_layers=self.num_hidden_layers,
            dropout=self.dropout,
            mode=self.mode,
            gated_attn=self.gated_attn,
            norm_mlp=self.norm_mlp,
            swin_hier=self.swin_hier,
            scaling=self.scaling,
            head_dropout=self.head_dropout,
            mask_type=self.mask_type,
            mask_ratio=self.mask_ratio,
            mask_patches=self.mask_patches,
            mask_patch_ratios=self.mask_patch_ratios,
            mask_value=self.mask_value,
            channel_consistent_masking=self.channel_consistent_masking,
            mask_mode=self.mask_mode,
            masked_loss=self.masked_loss,
            forecast_len=self.forecast_len,
            out_channels=self.out_channels,
            n_classes=self.n_classes,
            n_targets=self.n_targets,
            output_range=self.output_range,
            head_agg=self.head_agg,
            post_init=self.post_init,
        )
        self.num_patches = config_.num_patches
        return config_

    def prepare_patchtsmixer_inputs_dict(self, config):
        _past_length = config.seq_len
        # bs, n_vars, num_patch, patch_len

        # [bs x seq_len x n_vars]
        context_values = floats_tensor([self.batch_size, _past_length, self.input_size])

        target_values = floats_tensor([self.batch_size, config.forecast_len, self.input_size])

        inputs_dict = {
            "context_values": context_values,
            "target_values": target_values,
        }
        return inputs_dict

    def prepare_config_and_inputs(self):
        config = self.get_config()
        inputs_dict = self.prepare_patchtsmixer_inputs_dict(config)
        return config, inputs_dict

    def prepare_config_and_inputs_for_common(self):
        config, inputs_dict = self.prepare_config_and_inputs()
        return config, inputs_dict


@require_torch
class PatchTSMixerModelTest(ModelTesterMixin, PipelineTesterMixin, unittest.TestCase):
    all_model_classes = (
        (
            PatchTSMixerModel,
            PatchTSMixerForForecasting,
            PatchTSMixerForMaskPretraining,
            PatchTSMixerForClassification,
            PatchTSMixerForRegression,
        )
        if is_torch_available()
        else ()
    )
    all_generative_model_classes = (
        (PatchTSMixerForForecasting, PatchTSMixerForMaskPretraining) if is_torch_available() else ()
    )
    pipeline_model_mapping = {"feature-extraction": PatchTSMixerModel} if is_torch_available() else {}
    is_encoder_decoder = False
    test_pruning = False
    test_head_masking = False
    test_missing_keys = False
    test_torchscript = False
    test_inputs_embeds = False
    test_model_common_attributes = False

    test_resize_embeddings = True
    test_resize_position_embeddings = False
    test_mismatched_shapes = True
    test_model_parallel = False
    has_attentions = False

    def setUp(self):
        self.model_tester = PatchTSMixerModelTester()
        self.config_tester = ConfigTester(
            self,
            config_class=PatchTSMixerConfig,
            has_text_modality=False,
            forecast_len=self.model_tester.forecast_len,
            common_properties=["hidden_size", "expansion_factor", "num_hidden_layers"],
        )

    def test_config(self):
        self.config_tester.run_common_tests()

    def _prepare_for_class(self, inputs_dict, model_class, return_labels=False):
        inputs_dict = super()._prepare_for_class(inputs_dict, model_class, return_labels=return_labels)

        # if classification model:
        if model_class in get_values(MODEL_FOR_TIME_SERIES_CLASSIFICATION_MAPPING):
            rng = random.Random(self.model_tester.seed_number)
            labels = ids_tensor([self.model_tester.batch_size], self.model_tester.n_classes, rng=rng)
            # inputs_dict["labels"] = labels
            inputs_dict["target_values"] = labels
            # inputs_dict.pop("target_values")
        elif model_class in get_values(MODEL_FOR_TIME_SERIES_REGRESSION_MAPPING):
            rng = random.Random(self.model_tester.seed_number)
            labels = floats_tensor([self.model_tester.batch_size, self.model_tester.n_targets], rng=rng)
            # inputs_dict["labels"] = labels
            inputs_dict["target_values"] = labels
            # inputs_dict.pop("target_values")
        elif model_class in [PatchTSMixerModel, PatchTSMixerForMaskPretraining]:
            inputs_dict.pop("target_values")

        inputs_dict["output_hidden_states"] = True
        return inputs_dict

    def test_save_load_strict(self):
        config, _ = self.model_tester.prepare_config_and_inputs()
        for model_class in self.all_model_classes:
            model = model_class(config)

            with tempfile.TemporaryDirectory() as tmpdirname:
                model.save_pretrained(tmpdirname)
                model2, info = model_class.from_pretrained(tmpdirname, output_loading_info=True)
            self.assertEqual(info["missing_keys"], [])

    def test_hidden_states_output(self):
        def check_hidden_states_output(inputs_dict, config, model_class):
            model = model_class(config)
            model.to(torch_device)
            model.eval()

            with torch.no_grad():
                outputs = model(**self._prepare_for_class(inputs_dict, model_class))

            hidden_states = outputs.encoder_hidden_states if config.is_encoder_decoder else outputs.hidden_states

            expected_num_layers = getattr(
                self.model_tester, "expected_num_hidden_layers", self.model_tester.num_hidden_layers
            )
            self.assertEqual(len(hidden_states), expected_num_layers)

            expected_hidden_size = self.model_tester.hidden_size
            self.assertEqual(hidden_states[0].shape[-1], expected_hidden_size)

            num_patch = self.model_tester.num_patches
            self.assertListEqual(
                list(hidden_states[0].shape[-2:]),
                [num_patch, self.model_tester.hidden_size],
            )

        config, inputs_dict = self.model_tester.prepare_config_and_inputs_for_common()

        for model_class in self.all_model_classes:
            # inputs_dict["output_hidden_states"] = True
            print("model_class: ", model_class)

            check_hidden_states_output(inputs_dict, config, model_class)

            # check that output_hidden_states also work using config
            # del inputs_dict["output_hidden_states"]
            # config.output_hidden_states = True

            # check_hidden_states_output(inputs_dict, config, model_class)

    @unittest.skip("No tokens embeddings")
    def test_resize_tokens_embeddings(self):
        pass

    def test_model_outputs_equivalence(self):
        pass

    def test_model_main_input_name(self):
        model_signature = inspect.signature(getattr(PatchTSMixerModel, "forward"))
        # The main input is the name of the argument after `self`
        observed_main_input_name = list(model_signature.parameters.keys())[1]
        self.assertEqual(PatchTSMixerModel.main_input_name, observed_main_input_name)

    def test_forward_signature(self):
        config, _ = self.model_tester.prepare_config_and_inputs_for_common()

        for model_class in self.all_model_classes:
            model = model_class(config)
            signature = inspect.signature(model.forward)
            # signature.parameters is an OrderedDict => so arg_names order is deterministic
            arg_names = [*signature.parameters.keys()]

            expected_arg_names = [
                "context_values",
                "observed_mask",
                "target_values",
            ]
            # if model_class in get_values(MODEL_FOR_TIME_SERIES_CLASSIFICATION_MAPPING) or \
            #         model_class in get_values(MODEL_FOR_TIME_SERIES_REGRESSION_MAPPING):
            #     expected_arg_names.remove("target_values")
            #     expected_arg_names.append("labels")
            if model_class in [PatchTSMixerModel, PatchTSMixerForMaskPretraining]:
                expected_arg_names.remove("target_values")

            # expected_arg_names.extend(
            #     [
            #         "output_hidden_states",
            #     ]
            # )

            self.assertListEqual(arg_names[: len(expected_arg_names)], expected_arg_names)

    @is_flaky()
    def test_retain_grad_hidden_states_attentions(self):
        super().test_retain_grad_hidden_states_attentions()


def prepare_batch(repo_id="ibm/patchtsmixer-etth1-test-data", file="pretrain_batch.pt"):
    # TODO: Make repo public
    file = hf_hub_download(repo_id=repo_id, filename=file, repo_type="dataset")
    batch = torch.load(file, map_location=torch_device)
    return batch


@require_torch
@slow
class PatchTSMixerModelIntegrationTests(unittest.TestCase):
    def test_pretrain_head(self):
        # TODO: Make repo public
        model = PatchTSMixerForMaskPretraining.from_pretrained("ibm/patchtsmixer-etth1-pretrain").to(torch_device)
        batch = prepare_batch()

        torch.manual_seed(0)
        with torch.no_grad():
            output = model(context_values=batch["context_values"].to(torch_device)).prediction_logits
        num_patch = (
            max(model.config.seq_len, model.config.patch_len) - model.config.patch_len
        ) // model.config.stride + 1
        expected_shape = torch.Size([1024, model.config.input_size, num_patch, model.config.patch_len])
        self.assertEqual(output.shape, expected_shape)

        expected_slice = torch.tensor(
            [[[-0.3580]], [[2.9853]], [[-0.0456]], [[-1.8141]], [[-0.5844]], [[11.0132]], [[-0.1548]]],
            device=torch_device,
        )
        self.assertTrue(torch.allclose(output[0, :7, :1, :1], expected_slice, atol=TOLERANCE))

    def test_forecasting_head(self):
        # TODO: Make repo public
        model = PatchTSMixerForForecasting.from_pretrained("ibm/patchtsmixer-etth1-forecasting").to(torch_device)
        batch = prepare_batch(file="forecast_batch.pt")

        torch.manual_seed(0)
        with torch.no_grad():
            output = model(
                context_values=batch["context_values"].to(torch_device),
                target_values=batch["target_values"].to(torch_device),
            ).prediction_logits

        print(output[0, :1, :7])
        expected_shape = torch.Size([1024, model.config.forecast_len, model.config.input_size])
        self.assertEqual(output.shape, expected_shape)

        expected_slice = torch.tensor(
            [[0.5071, -0.0901, 0.5348, 0.6649, -0.2680, -2.0142, 0.2994]],
            device=torch_device,
        )
        self.assertTrue(torch.allclose(output[0, :1, :7], expected_slice, atol=TOLERANCE))


class PatchTSMixerFunctionalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Setup method: Called once before test-cases execution"""
        cls.params = {}
        cls.params.update(
            seq_len=32,
            patch_len=8,
            input_size=3,
            stride=8,
            num_features=4,
            expansion_factor=2,
            num_layers=3,
            dropout=0.2,
            mode="common_channel",  # common_channel, flatten, mix_channel
            gated_attn=True,
            norm_mlp="LayerNorm",
            mask_type="random",
            mask_ratio=0.5,
            mask_patches=[2, 3],
            mask_patch_ratios=[1, 1],
            mask_value=0,
            masked_loss=True,
            channel_consistent_masking=True,
            head_dropout=0.2,
            forecast_len=64,
            out_channels=None,
            n_classes=3,
            n_targets=3,
            output_range=None,
            head_agg=None,
            scaling="std",
            use_pe=False,
            pe="sincos",
            learn_pe=True,
            self_attn=False,
            self_attn_heads=1,
        )

        cls.num_patches = (
            max(cls.params["seq_len"], cls.params["patch_len"]) - cls.params["patch_len"]
        ) // cls.params["stride"] + 1

        # batch_size = 32
        batch_size = 2

        int(cls.params["forecast_len"] / cls.params["patch_len"])

        cls.data = torch.rand(
            batch_size,
            cls.params["seq_len"],
            cls.params["input_size"],
        )

        cls.enc_data = torch.rand(
            batch_size,
            cls.params["input_size"],
            cls.num_patches,
            cls.params["patch_len"],
        )

        cls.enc_output = torch.rand(
            batch_size,
            cls.params["input_size"],
            cls.num_patches,
            cls.params["num_features"],
        )

        cls.flat_enc_output = torch.rand(
            batch_size,
            cls.num_patches,
            cls.params["num_features"],
        )

        cls.correct_pred_output = torch.rand(batch_size, cls.params["forecast_len"], cls.params["input_size"])
        cls.correct_regression_output = torch.rand(batch_size, cls.params["n_targets"])

        cls.correct_pretrain_output = torch.rand(
            batch_size,
            cls.params["input_size"],
            cls.num_patches,
            cls.params["patch_len"],
        )

        cls.correct_forecast_output = torch.rand(
            batch_size,
            cls.params["forecast_len"],
            cls.params["input_size"],
        )

        cls.correct_sel_forecast_output = torch.rand(batch_size, cls.params["forecast_len"], 2)

        cls.correct_classification_output = torch.rand(
            batch_size,
            cls.params["n_classes"],
        )

        cls.correct_classification_classes = torch.randint(0, cls.params["n_classes"], (batch_size,))

    def test_patchtsmixer_encoder(self):
        config = PatchTSMixerConfig(**self.__class__.params)
        enc = PatchTSMixerEncoder(config)
        output = enc(self.__class__.enc_data)
        self.assertEqual(output.last_hidden_state.shape, self.__class__.enc_output.shape)

    def test_patchmodel(self):
        config = PatchTSMixerConfig(**self.__class__.params)
        mdl = PatchTSMixerModel(config)
        output = mdl(self.__class__.data)
        self.assertEqual(output.last_hidden_state.shape, self.__class__.enc_output.shape)
        self.assertEqual(output.last_hidden_state.shape, output[0].shape)
        self.assertEqual(output.patched_input.shape, self.__class__.enc_data.shape)

    def test_pretrainhead(self):
        config = PatchTSMixerConfig(**self.__class__.params)
        head = PretrainHead(
            num_patches=config.num_patches,
            num_features=config.num_features,
            input_size=config.input_size,
            patch_size=config.patch_len,
            head_dropout=config.head_dropout,
            mode=config.mode,
        )
        output = head(self.__class__.enc_output)

        self.assertEqual(output.shape, self.__class__.correct_pretrain_output.shape)

    def test_pretrain_full(self):
        config = PatchTSMixerConfig(**self.__class__.params)
        mdl = PatchTSMixerForMaskPretraining(config)
        output = mdl(self.__class__.data)
        self.assertEqual(output.prediction_logits.shape, self.__class__.correct_pretrain_output.shape)
        self.assertEqual(output.last_hidden_state.shape, self.__class__.enc_output.shape)
        self.assertEqual(output.loss.item() < 100, True)

        # print("loss shape", output.loss, output.loss.shape)

    def test_forecast_head(self):
        config = PatchTSMixerConfig(**self.__class__.params)
        head = ForecastHead(
            num_patches=config.num_patches,
            in_channels=config.input_size,
            patch_size=config.patch_len,
            num_features=config.num_features,
            forecast_len=config.forecast_len,
            head_dropout=config.head_dropout,
            mode=config.mode,
            forecast_channel_indices=config.forecast_channel_indices,
        )
        # output = head(self.__class__.enc_output, raw_data = self.__class__.correct_pretrain_output)
        output = head(self.__class__.enc_output)

        self.assertEqual(output.shape, self.__class__.correct_forecast_output.shape)

    def check_module(
        self,
        task,
        params=None,
        output_hidden_states=True,
    ):
        config = PatchTSMixerConfig(**params)
        if task == "forecast":
            mdl = PatchTSMixerForForecasting(config)
            target_input = self.__class__.correct_forecast_output
            if config.forecast_channel_indices is not None:
                target_output = self.__class__.correct_sel_forecast_output
            else:
                target_output = target_input

        elif task == "classification":
            mdl = PatchTSMixerForClassification(config)
            target_input = self.__class__.correct_classification_classes
            target_output = self.__class__.correct_classification_output
        elif task == "regression":
            mdl = PatchTSMixerForRegression(config)
            target_input = self.__class__.correct_regression_output
            target_output = self.__class__.correct_regression_output
        elif task == "pretrain":
            mdl = PatchTSMixerForMaskPretraining(config)
            target_input = None
            target_output = self.__class__.correct_pretrain_output
        else:
            print("invalid task")

        if config.mode == "flatten":
            enc_output = self.__class__.flat_enc_output
        else:
            enc_output = self.__class__.enc_output

        if target_input is None:
            output = mdl(self.__class__.data, output_hidden_states=output_hidden_states)
        else:
            output = mdl(self.__class__.data, target_values=target_input, output_hidden_states=output_hidden_states)

        self.assertEqual(output.prediction_logits.shape, target_output.shape)

        self.assertEqual(output.last_hidden_state.shape, enc_output.shape)

        if output_hidden_states is True:
            self.assertEqual(len(output.hidden_states), params["num_layers"])

        else:
            self.assertEqual(output.hidden_states, None)

        self.assertEqual(output.loss.item() < 100, True)

    def test_forecast(self):
        for mode in ["flatten", "common_channel", "mix_channel"]:
            for self_attn in [True, False]:
                for scaling in [True, False, "mean", "std"]:
                    for gated_attn in [True, False]:
                        for forecast_channel_indices in [None, [0, 2]]:
                            params = self.__class__.params.copy()
                            params.update(
                                mode=mode,
                                self_attn=self_attn,
                                scaling=scaling,
                                forecast_channel_indices=forecast_channel_indices,
                                gated_attn=gated_attn,
                            )

                            self.check_module(task="forecast", params=params)

    def test_classification(self):
        for mode in ["common_channel", "mix_channel", "flatten"]:
            for self_attn in [True, False]:
                for scaling in [True, False, "mean", "std"]:
                    for gated_attn in [True, False]:
                        for head_agg in ["max_pool", "avg_pool"]:
                            if mode == "flatten" and scaling in ["mean", "std", True]:
                                continue
                            params = self.__class__.params.copy()
                            params.update(
                                mode=mode,
                                self_attn=self_attn,
                                scaling=scaling,
                                head_agg=head_agg,
                                gated_attn=gated_attn,
                            )
                            # print(mode,self_attn,revin,gated_attn,head_agg)

                            self.check_module(task="classification", params=params)

    def test_regression(self):
        for mode in ["common_channel", "mix_channel", "flatten"]:
            for self_attn in [True, False]:
                for scaling in [True, False, "mean", "std"]:
                    for gated_attn in [True, False]:
                        for head_agg in ["max_pool", "avg_pool"]:
                            if mode == "flatten" and scaling in ["mean", "std", True]:
                                continue
                            params = self.__class__.params.copy()
                            params.update(
                                mode=mode,
                                self_attn=self_attn,
                                scaling=scaling,
                                head_agg=head_agg,
                                gated_attn=gated_attn,
                            )
                            # print(mode,self_attn,revin,gated_attn,head_agg)

                            self.check_module(task="regression", params=params)

    def test_pretrain(self):
        for mode in ["common_channel", "mix_channel", "flatten"]:
            for self_attn in [True, False]:
                for scaling in [True, False, "mean", "std"]:
                    for gated_attn in [True, False]:
                        for mask_type in ["random", "forecast"]:
                            for masked_loss in [True, False]:
                                for channel_consistent_masking in [True, False]:
                                    params = self.__class__.params.copy()
                                    params.update(
                                        mode=mode,
                                        self_attn=self_attn,
                                        scaling=scaling,
                                        gated_attn=gated_attn,
                                        mask_type=mask_type,
                                        masked_loss=masked_loss,
                                        channel_consistent_masking=channel_consistent_masking,
                                    )
                                    # print(mode,self_attn,revin,gated_attn,head_agg)

                                    self.check_module(task="pretrain", params=params)

        # for mode in ["flatten","common_channel","mix_channel"]:
        #     for task in ["forecast","classification","regression","pretrain"]:
        #         for self_attn in [True,False]:
        #             for head_agg in ["max_pool","avg_pool"]:
        #                 for mask_type in ["random","forecast"]:
        #                     for masked_loss in [True, False]:
        #                         for channel_consistent_masking in [True, False]:
        #                             for revin in [True, False]:
        #                                 for forecast_channel_indices in [None, [0,2]]:

    def forecast_full_module(self, params=None, output_hidden_states=False):
        config = PatchTSMixerConfig(**params)
        mdl = PatchTSMixerForForecasting(config)

        target_val = self.__class__.correct_forecast_output

        if config.forecast_channel_indices is not None:
            target_val = self.__class__.correct_sel_forecast_output

        if config.mode == "flatten":
            enc_output = self.__class__.flat_enc_output
        else:
            enc_output = self.__class__.enc_output

        output = mdl(
            self.__class__.data,
            target_values=self.__class__.correct_forecast_output,
            output_hidden_states=output_hidden_states,
        )

        self.assertEqual(output.prediction_logits.shape, target_val.shape)

        self.assertEqual(output.last_hidden_state.shape, enc_output.shape)

        if output_hidden_states is True:
            self.assertEqual(len(output.hidden_states), params["num_layers"])

        else:
            self.assertEqual(output.hidden_states, None)

        self.assertEqual(output.loss.item() < 100, True)
        # print("loss shape", output.loss, output.loss.shape)

    def test_forecast_full(self):
        self.check_module(task="forecast", params=self.__class__.params, output_hidden_states=True)
        # self.forecast_full_module(self.__class__.params, output_hidden_states = True)

    def test_forecast_full_2(self):
        params = self.__class__.params.copy()
        params.update(
            mode="mix_channel",
        )
        self.forecast_full_module(params, output_hidden_states=True)

    def test_forecast_full_3(self):
        params = self.__class__.params.copy()
        params.update(
            mode="flatten",
        )
        self.forecast_full_module(params, output_hidden_states=True)

    def test_forecast_full_5(self):
        params = self.__class__.params.copy()
        params.update(
            self_attn=True,
            use_pe=True,
            pe="sincos",
            learn_pe=True,
        )
        self.forecast_full_module(params, output_hidden_states=True)

    def test_forecast_full_4(self):
        params = self.__class__.params.copy()
        params.update(
            mode="mix_channel",
            forecast_channel_indices=[0, 2],
        )
        self.forecast_full_module(params)

    # def test_forecast_full(self):
    #     config = PatchTSMixerConfig(**self.__class__.params)
    #     mdl = PatchTSMixerForForecasting(config)
    #     output = mdl(self.__class__.data, target_values=self.__class__.correct_forecast_output)
    #     self.assertEqual(
    #         output.prediction_logits.shape, self.__class__.correct_forecast_output.shape
    #     )
    #     self.assertEqual(
    #         output.last_hidden_state.shape, self.__class__.enc_output.shape
    #     )
    #     self.assertEqual(output.loss.item()<100,True)
    #     # print("loss shape", output.loss, output.loss.shape)

    def test_classification_head(self):
        config = PatchTSMixerConfig(**self.__class__.params)
        head = LinearHead(
            num_patches=config.num_patches,
            in_channels=config.input_size,
            num_features=config.num_features,
            head_dropout=config.head_dropout,
            output_dim=config.n_classes,
            output_range=config.output_range,
            head_agg=config.head_agg,
            mode=config.mode,
        )
        # output = head(self.__class__.enc_output, raw_data = self.__class__.correct_pretrain_output)
        output = head(self.__class__.enc_output)

        self.assertEqual(output.shape, self.__class__.correct_classification_output.shape)

    def test_classification_full(self):
        config = PatchTSMixerConfig(**self.__class__.params)
        mdl = PatchTSMixerForClassification(config)
        output = mdl(self.__class__.data, target_values=self.__class__.correct_classification_classes)
        self.assertEqual(
            output.prediction_logits.shape,
            self.__class__.correct_classification_output.shape,
        )
        self.assertEqual(output.last_hidden_state.shape, self.__class__.enc_output.shape)
        self.assertEqual(output.loss.item() < 100, True)
        # print("loss shape", output.loss, output.loss.shape)

    def test_regression_head(self):
        config = PatchTSMixerConfig(**self.__class__.params)
        head = LinearHead(
            num_patches=config.num_patches,
            in_channels=config.input_size,
            num_features=config.num_features,
            head_dropout=config.head_dropout,
            output_dim=config.n_targets,
            output_range=config.output_range,
            head_agg=config.head_agg,
            mode=config.mode,
        )
        # output = head(self.__class__.enc_output, raw_data = self.__class__.correct_pretrain_output)
        output = head(self.__class__.enc_output)
        # print(output.shape)
        self.assertEqual(output.shape, self.__class__.correct_regression_output.shape)

    def test_regression_full(self):
        config = PatchTSMixerConfig(**self.__class__.params)
        mdl = PatchTSMixerForRegression(config)
        output = mdl(self.__class__.data, target_values=self.__class__.correct_regression_output)
        self.assertEqual(
            output.prediction_logits.shape,
            self.__class__.correct_regression_output.shape,
        )
        self.assertEqual(output.last_hidden_state.shape, self.__class__.enc_output.shape)
        self.assertEqual(output.loss.item() < 100, True)

        # print("loss shape", output.loss, output.loss.shape)
