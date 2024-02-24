# coding = utf-8
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
""" Testing suite for the PyTorch RT_DETR model. """


import inspect
import unittest

from transformers import RTDetrConfig, RTDetrImageProcessor, is_torch_available, is_vision_available
from transformers.testing_utils import require_torch, require_vision, torch_device
from transformers.utils import cached_property

from ...test_configuration_common import ConfigTester
from ...test_modeling_common import ModelTesterMixin, _config_zero_init, floats_tensor
from ...test_pipeline_mixin import PipelineTesterMixin


if is_torch_available():
    import torch

    from transformers import RTDetrForObjectDetection, RTDetrModel
    from transformers.models.rt_detr.modeling_rt_detr import RTDETR_PRETRAINED_MODEL_ARCHIVE_LIST

if is_vision_available():
    from PIL import Image


CHECKPOINT = "sbchoi/rtdetr_r50vd"  # TODO: replace


class RTDetrModelTester:
    def __init__(
        self,
        parent,
        batch_size=8,
        is_training=True,
        use_labels=True,
        n_targets=8,
        num_labels=80,
        initializer_range=0.02,
        layer_norm_eps=1e-5,
        batch_norm_eps=1e-5,
        # backbone
        use_timm_backbone=True,
        backbone_config=None,
        num_channels=3,
        backbone="resnet50d",
        use_pretrained_backbone=True,
        dilation=False,
        # encoder HybridEncoder
        d_model=256,
        encoder_in_channels=[512, 1024, 2048],
        feat_strides=[8, 16, 32],
        encoder_layers=1,
        encoder_ffn_dim=1024,
        encoder_attention_heads=8,
        dropout=0.0,
        activation_dropout=0.0,
        encode_proj_layers=[2],
        pe_temperature=10000,
        encoder_activation_function="gelu",
        activation_function="silu",
        eval_size=None,
        normalize_before=False,
        # decoder RTDetrTransformer
        num_queries=300,
        decoder_in_channels=[256, 256, 256],
        decoder_ffn_dim=1024,
        num_feature_levels=3,
        decoder_n_points=4,
        decoder_layers=6,
        decoder_attention_heads=8,
        decoder_activation_function="relu",
        attention_dropout=0.0,
        num_denoising=100,
        label_noise_ratio=0.5,
        box_noise_scale=1.0,
        learnt_init_query=False,
        image_size=[640, 640],
        eval_idx=-1,
        disable_custom_kernels=True,
        with_box_refine=True,
    ):
        self.parent = parent
        self.batch_size = batch_size
        self.is_training = is_training
        self.use_labels = use_labels
        self.n_targets = n_targets
        self.num_labels = num_labels
        self.initializer_range = initializer_range
        self.layer_norm_eps = layer_norm_eps
        self.batch_norm_eps = batch_norm_eps
        self.use_timm_backbone = use_timm_backbone
        self.backbone_config = backbone_config
        self.num_channels = num_channels
        self.backbone = backbone
        self.use_pretrained_backbone = use_pretrained_backbone
        self.dilation = dilation
        self.d_model = d_model
        self.encoder_in_channels = encoder_in_channels
        self.feat_strides = feat_strides
        self.encoder_layers = encoder_layers
        self.encoder_ffn_dim = encoder_ffn_dim
        self.encoder_attention_heads = encoder_attention_heads
        self.dropout = dropout
        self.activation_dropout = activation_dropout
        self.encode_proj_layers = encode_proj_layers
        self.pe_temperature = pe_temperature
        self.encoder_activation_function = encoder_activation_function
        self.activation_function = activation_function
        self.eval_size = eval_size
        self.normalize_before = normalize_before
        self.num_queries = num_queries
        self.decoder_in_channels = decoder_in_channels
        self.decoder_ffn_dim = decoder_ffn_dim
        self.num_feature_levels = num_feature_levels
        self.decoder_n_points = decoder_n_points
        self.decoder_layers = decoder_layers
        self.decoder_attention_heads = decoder_attention_heads
        self.decoder_activation_function = decoder_activation_function
        self.attention_dropout = attention_dropout
        self.num_denoising = num_denoising
        self.label_noise_ratio = label_noise_ratio
        self.box_noise_scale = box_noise_scale
        self.learnt_init_query = learnt_init_query
        self.image_size = image_size
        self.eval_idx = eval_idx
        self.disable_custom_kernels = disable_custom_kernels
        self.with_box_refine = with_box_refine

    def prepare_config_and_inputs(self):
        pixel_values = floats_tensor([self.batch_size, self.num_channels, *self.image_size])

        pixel_mask = torch.ones([self.batch_size, *self.image_size], device=torch_device)

        labels = None
        if self.use_labels:
            # labels is a list of Dict (each Dict being the labels for a given example in the batch)
            labels = []
            for i in range(self.batch_size):
                target = {}
                target["class_labels"] = torch.randint(
                    high=self.num_labels, size=(self.n_targets,), device=torch_device
                )
                target["boxes"] = torch.rand(self.n_targets, 4, device=torch_device)
                labels.append(target)

        config = self.get_config()
        config.num_labels = self.num_labels
        return config, pixel_values, pixel_mask, labels

    def get_config(self):
        return RTDetrConfig(
            initializer_range=self.initializer_range,
            layer_norm_eps=self.layer_norm_eps,
            batch_norm_eps=self.batch_norm_eps,
            use_timm_backbone=self.use_timm_backbone,
            backbone_config=self.backbone_config,
            num_channels=self.num_channels,
            backbone=self.backbone,
            use_pretrained_backbone=self.use_pretrained_backbone,
            dilation=self.dilation,
            d_model=self.d_model,
            encoder_in_channels=self.encoder_in_channels,
            feat_strides=self.feat_strides,
            encoder_layers=self.encoder_layers,
            encoder_ffn_dim=self.encoder_ffn_dim,
            encoder_attention_heads=self.encoder_attention_heads,
            dropout=self.dropout,
            activation_dropout=self.activation_dropout,
            encode_proj_layers=self.encode_proj_layers,
            pe_temperature=self.pe_temperature,
            encoder_activation_function=self.encoder_activation_function,
            activation_function=self.activation_function,
            eval_size=self.eval_size,
            normalize_before=self.normalize_before,
            num_queries=self.num_queries,
            decoder_in_channels=self.decoder_in_channels,
            decoder_ffn_dim=self.decoder_ffn_dim,
            num_feature_levels=self.num_feature_levels,
            decoder_n_points=self.decoder_n_points,
            decoder_layers=self.decoder_layers,
            decoder_attention_heads=self.decoder_attention_heads,
            decoder_activation_function=self.decoder_activation_function,
            attention_dropout=self.attention_dropout,
            num_denoising=self.num_denoising,
            label_noise_ratio=self.label_noise_ratio,
            box_noise_scale=self.box_noise_scale,
            learnt_init_query=self.learnt_init_query,
            image_size=self.image_size,
            eval_idx=self.eval_idx,
            disable_custom_kernels=self.disable_custom_kernels,
            with_box_refine=self.with_box_refine,
        )

    def prepare_config_and_inputs_for_common(self):
        config, pixel_values, pixel_mask, labels = self.prepare_config_and_inputs()
        inputs_dict = {"pixel_values": pixel_values}
        return config, inputs_dict

    def create_and_check_rt_detr_model(self, config, pixel_values, pixel_mask, labels):
        model = RTDetrModel(config=config)
        model.to(torch_device)
        model.eval()

        result = model(pixel_values=pixel_values, pixel_mask=pixel_mask)
        result = model(pixel_values)

        self.parent.assertEqual(result.last_hidden_state.shape, (self.batch_size, self.num_queries, self.d_model))

    def create_and_check_rt_detr_object_detection_head_model(self, config, pixel_values, pixel_mask, labels):
        model = RTDetrForObjectDetection(config=config)
        model.to(torch_device)
        model.eval()

        result = model(pixel_values=pixel_values, pixel_mask=pixel_mask)
        result = model(pixel_values)

        self.parent.assertEqual(result.logits.shape, (self.batch_size, self.num_queries, self.num_labels))
        self.parent.assertEqual(result.pred_boxes.shape, (self.batch_size, self.num_queries, 4))

        result = model(pixel_values=pixel_values, pixel_mask=pixel_mask, labels=labels)

        self.parent.assertEqual(result.loss.shape, ())
        self.parent.assertEqual(result.logits.shape, (self.batch_size, self.num_queries, self.num_labels))
        self.parent.assertEqual(result.pred_boxes.shape, (self.batch_size, self.num_queries, 4))


@require_torch
class RTDetrModelTest(ModelTesterMixin, PipelineTesterMixin, unittest.TestCase):
    all_model_classes = (RTDetrModel, RTDetrForObjectDetection) if is_torch_available() else ()
    pipeline_model_mapping = (
        {"image-feature-extraction": RTDetrModel, "object-detection": RTDetrForObjectDetection}
        if is_torch_available()
        else {}
    )
    test_torchscript = False
    test_pruning = False
    test_resize_embeddings = False
    has_attentions = False
    test_head_masking = False

    # special case for head models
    def _prepare_for_class(self, inputs_dict, model_class, return_labels=False):
        inputs_dict = super()._prepare_for_class(inputs_dict, model_class, return_labels=return_labels)

        if return_labels:
            if model_class.__name__ == "RTDetrForObjectDetection":
                labels = []
                for i in range(self.model_tester.batch_size):
                    target = {}
                    target["class_labels"] = torch.ones(
                        size=(self.model_tester.n_targets,), device=torch_device, dtype=torch.long
                    )
                    target["boxes"] = torch.ones(
                        self.model_tester.n_targets, 4, device=torch_device, dtype=torch.float
                    )
                    labels.append(target)
                inputs_dict["labels"] = labels

        return inputs_dict

    def setUp(self):
        self.model_tester = RTDetrModelTester(self)
        self.config_tester = ConfigTester(self, config_class=RTDetrConfig, has_text_modality=False)

    def test_config(self):
        # we don't test common_properties and arguments_init as these don't apply for Deformable DETR
        self.config_tester.create_and_test_config_to_json_string()
        self.config_tester.create_and_test_config_to_json_file()
        self.config_tester.create_and_test_config_from_and_save_pretrained()
        self.config_tester.create_and_test_config_with_num_labels()
        self.config_tester.check_config_can_be_init_without_params()

    def test_rt_detr_model(self):
        config_and_inputs = self.model_tester.prepare_config_and_inputs()
        self.model_tester.create_and_check_rt_detr_model(*config_and_inputs)

    def test_rt_detr_object_detection_head_model(self):
        config_and_inputs = self.model_tester.prepare_config_and_inputs()
        self.model_tester.create_and_check_rt_detr_object_detection_head_model(*config_and_inputs)

    @unittest.skip(reason="RTDetr does not use inputs_embeds")
    def test_inputs_embeds(self):
        pass

    @unittest.skip(reason="RTDetr does not use hidden states")
    def test_hidden_states_output(self):
        pass

    @unittest.skip(reason="RTDetr does not support input and output embeddings")
    def test_model_common_attributes(self):
        pass

    @unittest.skip(reason="RTDetr was not designed smaller.")
    def test_model_is_small(self):
        pass

    def test_retain_grad_hidden_states_attentions(self):
        config, inputs_dict = self.model_tester.prepare_config_and_inputs_for_common()
        config.output_hidden_states = True

        model_class = self.all_model_classes[0]
        model = model_class(config)
        model.to(torch_device)

        inputs = self._prepare_for_class(inputs_dict, model_class)

        outputs = model(**inputs)
        encoder_hidden_states = outputs.encoder_hidden_states[0]
        encoder_hidden_states.retain_grad()
        outputs["logits"].flatten()[0].backward(retain_graph=True)

        self.assertIsNotNone(encoder_hidden_states.grad)

    def test_forward_signature(self):
        config, _ = self.model_tester.prepare_config_and_inputs_for_common()

        for model_class in self.all_model_classes:
            model = model_class(config)
            signature = inspect.signature(model.forward)
            arg_names = [*signature.parameters.keys()]
            expected_arg_names = ["pixel_values"]
            self.assertListEqual(arg_names[:1], expected_arg_names)

    # removed retain_grad and grad on decoder_hidden_states, as queries don't require grad
    def test_retain_grad_hidden_states_attentions(self):
        config, inputs_dict = self.model_tester.prepare_config_and_inputs_for_common()
        config.output_hidden_states = True
        config.output_attentions = True

        # no need to test all models as different heads yield the same functionality
        model_class = self.all_model_classes[0]
        model = model_class(config)
        model.to(torch_device)

        inputs = self._prepare_for_class(inputs_dict, model_class)

        outputs = model(**inputs)

        # we take the second output since last_hidden_state is the second item
        output = outputs[1]

        encoder_hidden_states = outputs.encoder_hidden_states[0]
        encoder_attentions = outputs.encoder_attentions[0]
        encoder_hidden_states.retain_grad()
        encoder_attentions.retain_grad()

        decoder_attentions = outputs.decoder_attentions[0]
        decoder_attentions.retain_grad()

        cross_attentions = outputs.cross_attentions[0]
        cross_attentions.retain_grad()

        output.flatten()[0].backward(retain_graph=True)

        self.assertIsNotNone(encoder_hidden_states.grad)
        self.assertIsNotNone(encoder_attentions.grad)
        self.assertIsNotNone(decoder_attentions.grad)
        self.assertIsNotNone(cross_attentions.grad)

    @unittest.skip(reason="Model doesn't use tied weights")
    def test_tied_model_weights_key_ignore(self):
        pass

    def test_initialization(self):
        config, inputs_dict = self.model_tester.prepare_config_and_inputs_for_common()

        configs_no_init = _config_zero_init(config)
        for model_class in self.all_model_classes:
            model = model_class(config=configs_no_init)
            # Skip the check for the backbone
            for name, module in model.named_modules():
                if module.__class__.__name__ == "DetaBackboneWithPositionalEncodings":
                    backbone_params = [f"{name}.{key}" for key in module.state_dict().keys()]
                    break

            for name, param in model.named_parameters():
                if param.requires_grad:
                    if (
                        "level_embed" in name
                        or "sampling_offsets.bias" in name
                        or "value_proj" in name
                        or "output_proj" in name
                        or "reference_points" in name
                        or name in backbone_params
                    ):
                        continue
                    self.assertIn(
                        ((param.data.mean() * 1e9).round() / 1e9).item(),
                        [0.0, 1.0],
                        msg=f"Parameter {name} of model {model_class} seems not properly initialized",
                    )

    def test_model_from_pretrained(self):
        for model_name in RTDETR_PRETRAINED_MODEL_ARCHIVE_LIST:
            model = RTDetrModel.from_pretrained(model_name)
            self.assertIsNotNone(model)


TOLERANCE = 1e-4


# We will verify our results on an image of cute cats
def prepare_img():
    image = Image.open("./tests/fixtures/tests_samples/COCO/000000039769.png")
    return image


@require_torch
@require_vision
class RTDetrModelIntegrationTest(unittest.TestCase):
    @cached_property
    def default_image_processor(self):
        return RTDetrImageProcessor.from_pretrained(CHECKPOINT) if is_vision_available() else None

    def test_inference_object_detection_head(self):
        model = RTDetrForObjectDetection.from_pretrained(CHECKPOINT).to(torch_device)

        image_processor = self.default_image_processor
        image = prepare_img()
        inputs = image_processor(images=image, return_tensors="pt").to(torch_device)

        with torch.no_grad():
            outputs = model(**inputs)

        expected_shape_logits = torch.Size((1, 300, model.config.num_labels))
        self.assertEqual(outputs.logits.shape, expected_shape_logits)

        expected_logits = torch.tensor(
            [
                [-4.64763879776001, -5.001153945922852, -4.978509902954102],
                [-4.159348487854004, -4.703853607177734, -5.946484565734863],
                [-4.437461853027344, -4.65836238861084, -6.235235691070557],
            ]
        ).to(torch_device)
        expected_boxes = torch.tensor(
            [
                [0.1688060760498047, 0.19992263615131378, 0.21225441992282867],
                [0.768376350402832, 0.41226309537887573, 0.4636859893798828],
                [0.25953856110572815, 0.5483334064483643, 0.4777486026287079],
            ]
        ).to(torch_device)

        self.assertTrue(torch.allclose(outputs.logits[0, :3, :3], expected_logits, atol=1e-4))

        expected_shape_boxes = torch.Size((1, 300, 4))
        self.assertEqual(outputs.pred_boxes.shape, expected_shape_boxes)
        self.assertTrue(torch.allclose(outputs.pred_boxes[0, :3, :3], expected_boxes, atol=1e-4))

        # verify postprocessing
        results = image_processor.post_process_object_detection(
            outputs, threshold=0.0, target_sizes=[image.size[::-1]]
        )[0]
        expected_scores = torch.tensor(
            [0.9703017473220825, 0.9599503874778748, 0.9575679302215576, 0.9506784677505493], device=torch_device
        )
        expected_labels = [57, 15, 15, 65]
        expected_slice_boxes = torch.tensor(
            [
                [
                    [0.13774871826171875, 0.37818431854248047, 640.1307373046875, 476.21087646484375],
                    [343.38134765625, 24.276838302612305, 640.140380859375, 371.4957275390625],
                    [13.225126266479492, 54.17934799194336, 318.9842224121094, 472.220703125],
                ]
            ],
            device=torch_device,
        )

        self.assertTrue(torch.allclose(results["scores"][:4], expected_scores, atol=1e-4))
        self.assertSequenceEqual(results["labels"][:4].tolist(), expected_labels)
        print(results["boxes"][:4])
        self.assertTrue(torch.allclose(results["boxes"][:4], expected_slice_boxes))
