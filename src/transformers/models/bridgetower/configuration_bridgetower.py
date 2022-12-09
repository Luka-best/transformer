# coding=utf-8
# Copyright 2022 The HuggingFace Inc. team. All rights reserved.
#
# Licensed under the Apache License=, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing=, software
# distributed under the License is distributed on an "AS IS" BASIS=,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND=, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
""" BridgeTower model configuration"""

from ...configuration_utils import PretrainedConfig
from ...utils import logging


logger = logging.get_logger(__name__)

BRIDGETOWER_PRETRAINED_CONFIG_ARCHIVE_MAP = {
    "BridgeTower/bridgetower-base": "https://huggingface.co/BridgeTower/bridgetower-base/blob/main/config.json",
    "BridgeTower/bridgetower-base-itm-mlm": "https://huggingface.co/BridgeTower/bridgetower-base-itm/blob/main/config.json",
 }


class BridgeTowerConfig(PretrainedConfig):
    r"""
    This is the configuration class to store the configuration of a [`BridgeTowerModel`]. It is used to instantiate a
    BridgeTower model according to the specified arguments, defining the model architecture. Instantiating a
    configuration with the defaults will yield a similar configuration to that of the bridgetower-base
    [BridegTower/bridgetower-base](https://huggingface.co/BridgeTower/bridgetower-base/) architecture.

    Configuration objects inherit from [`PretrainedConfig`] and can be used to control the model outputs. Read the
    documentation from [`PretrainedConfig`] for more information.

    Args:
        cache_dir (`str`, *optional*, defaults to `"/tmp"`):
            Path to the cache directory.
        classifier_drop_rate (`float`, *optional*, defaults to 0.1):
            The drop out probability for classifier's Dropout layer.
        cross_modal_transform_shared (`bool`, *optional*, defaults to `True`):
            Whether cross modal transformer layers are shared.
        downstream_fusion (`bool`, *optional*, defaults to `False`):
            Whether to enable downstream fusion.
        downstream_fusion_layers (`int`, *optional*, defaults to 1):
            Number of fusion layers for downstream tasks.
        downstream_fusion_method (`str`, *optional*, defaults to `"elmo"`):
            Fusion method for downstream tasks.
        drop_rate (`float`, *optional*, defaults to 0.1):
            Drop out probability.
        freeze_RoBERTa (`bool`, *optional*, defaults to `False`):
            Whether to freeze RoBERTa.
        freeze_ViT (`bool`, *optional*, defaults to `False`):
            Whether to freeze ViT.
        freeze_layer_count_roberta (`bool`, *optional*, defaults to `False`):
            Whether to freeze layer count for RobERTa.
        freeze_layer_count_vit (`bool`, *optional*, defaults to `False`):
            Whether to freeze layer count for ViT.
        head_hidden_scale (`int`, *optional*, defaults to 2):
            Scale of hidden layers head.
        hidden_size (`int`, *optional*, defaults to 768):
            Dimensionality of the encoder layers and the pooler layer.
        image_size (`int`, *optional*, defaults to 288):
            The size (resolution) of each image.
        input_image_embed_size (`int`, *optional*, defaults to 768):
            Embedding size of the input image.
        input_text_embed_size (`int`, *optional*, defaults to 768):
            Embedding size of the input text.
        link_tower_shared (`bool`, *optional*, defaults to `False`):
            Whether the bride/link tower layers are shared.
        link_tower_type (`str`, *optional*, defaults to `"add"`):
            Type of the bridge/link layer.
        log_dir (`str`, *optional*, defaults to `"log_dir"`):
            Path to the log directory.
        loss_names (`Dict[str, int]`, *optional*):
            Various loss options.
        max_text_len (`int`, *optional*, defaults to 50):
            Maximum text length.
        mlp_ratio (`int`, *optional*, defaults to 4):
            Ratio of MLP hidden dim to embedding dim.
        model_type (`str`, *optional*, defaults to `"bridgetower"`):
            Model type.
        nlvr2_head_format (`str`, *optional*, defaults to `"pair"`):
            Head format for nlvr2.
        num_attention_heads (`int`, *optional*, defaults to 12):
            Number of attention heads for each attention layer in the Transformer encoder.
        num_hidden_layers (`int`, *optional*, defaults to 6):
            Number of hidden layers in the Transformer encoder.
        num_nodes (`int`, *optional*, defaults to 1):
            Number of nodes for multi-node training.
        only_load_cross_modal_from_meter (`bool`, *optional*, defaults to `False`):
            Whether to load cross modal transformer from meter.
        patch_size (`int`, *optional*, defaults to 16):
            The size (resolution) of each patch.
        resolution_before (`int`, *optional*, defaults to 224):
            Prior resolution.
        stop_gradient (`bool`, *optional*, defaults to `False`):
            Whether to stop gradient for training.
        task_head_layers (`int`, *optional*, defaults to 2):
            Number of task head layers.
        test_only (`bool`, *optional*, defaults to `False`):
            Whether model is used only for test.
        tokenizer (`str`, *optional*, defaults to `"roberta-base"`):
            Choice of the text tokenizer.
        unfreeze_RoBERTa_attention (`bool`, *optional*, defaults to `False`):
            Whether to unfreeze RoBERTa's LayerNorm.
        unfreeze_RoBERTa_embeddings (`bool`, *optional*, defaults to `False`):
            Whether to unfreeze RoBERTa's embeddings.
        unfreeze_RoBERTa_encoder (`bool`, *optional*, defaults to `False`):
            Whether to unfreeze RoBERTa's encoder.
        unfreeze_RoBERTa_layernorm (`bool`, *optional*, defaults to `False`):
            Whether to unfreeze RoBERTa's LayerNorm.
        unfreeze_ViT_attention (`bool`, *optional*, defaults to `False`):
            Whether to unfreeze ViT's attention.
        unfreeze_ViT_layernorm (`bool`, *optional*, defaults to `False`):
            Whether to unfreeze ViT's LayerNorm.
        vit (`str`, *optional*, defaults to `"ViT-B/16"`):
            ViT model configuration.
        vit_layernorm_init_from_vit (`bool`, *optional*, defaults to `False`):
            Whether to init ViT LayerNorm from ViT.
        vit_layernorm_shared (`bool`, *optional*, defaults to `True`):
            Whether ViT's LayerNorm layers are shared.
        vit_remove_last (`bool`, *optional*, defaults to `False`):
            Whether to remove ViT's last layer.
        vocab_size (`int`, *optional*, defaults to 50265):
            Vocabulary size of the text part of the model. Defines the number of different tokens that can be
            represented by the `inputs_ids` passed when calling [`BridgeTowerModel`].
        vqav2_label_size (`int`, *optional*, defaults to 3129):
            Label size for vqav2.

    Example:

    ```python
    >>> from transformers import BridgeTowerModel, BridgeTowerConfig

    >>> # Initializing a BridgeTower BridgeTower/bridgetower-base style configuration
    >>> configuration = BridgeTowerConfig()

    >>> # Initializing a model from the BridgeTower/bridgetower-base style configuration
    >>> model = BridgeTowerModel(configuration)

    >>> # Accessing the model configuration
    >>> configuration = model.config
    ```"""
    model_type = "bridgetower"

    def __init__(
        self,      
        cache_dir='/tmp',
        classifier_drop_rate=0.1,
        cross_modal_transform_shared=True,
        downstream_fusion=False,
        downstream_fusion_layers=1,
        downstream_fusion_method='elmo',
        drop_rate=0.1,
        freeze_RoBERTa=False,
        freeze_ViT=False,
        freeze_layer_count_roberta=False,
        freeze_layer_count_vit=False,
        head_hidden_scale=2,
        hidden_act="gelu",
        hidden_size=768,
        image_size=288,
        input_image_embed_size=768,
        input_text_embed_size=768,
        is_encoder_decoder=False,
        layer_norm_eps=1e-05,
        link_tower_shared=False,
        link_tower_type='add',
        log_dir='log_dir',
        loss_names={'contras': 0,
                'irtr': 0,
                'itm': 0,
                'mlm': 0,
                'mpp': 0,
                'nlvr2': 0,
                'snli': 0,
                'vcr': 0,
                'vcr_qar': 0,
                'vqa': 1},
        max_text_len=50,
        mlp_ratio=4,
        model_type='bridgetower',
        nlvr2_head_format='pair',
        num_attention_heads=12,
        num_hidden_layers=6,
        num_nodes=1,
        only_load_cross_modal_from_meter=False,
        patch_size=16,
        resolution_before=224,
        stop_gradient=False,
        task_head_layers=2,
        test_only=False,
        tie_word_embeddings=False,
        tokenizer='roberta-base',
        unfreeze_RoBERTa_attention=False,
        unfreeze_RoBERTa_embeddings=False,
        unfreeze_RoBERTa_encoder=False,
        unfreeze_RoBERTa_layernorm=False,
        unfreeze_ViT_attention=False,
        unfreeze_ViT_layernorm=False,
        vit='ViT-B/16',
        vit_layernorm_init_from_vit=False,
        vit_layernorm_shared=True,
        vit_remove_last=False,
        vocab_size=50265,
        vqav2_label_size=3129,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.cache_dir = cache_dir
        self.classifier_drop_rate = classifier_drop_rate
        self.cross_modal_transform_shared = cross_modal_transform_shared
        self.downstream_fusion = downstream_fusion
        self.downstream_fusion_layers = downstream_fusion_layers
        self.downstream_fusion_method = downstream_fusion_method
        self.drop_rate = drop_rate
        self.freeze_RoBERTa = freeze_RoBERTa
        self.freeze_ViT = freeze_ViT
        self.freeze_layer_count_roberta = freeze_layer_count_roberta
        self.freeze_layer_count_vit = freeze_layer_count_vit
        self.head_hidden_scale = head_hidden_scale
        self.hidden_act = hidden_act
        self.hidden_size = hidden_size
        self.image_size = image_size
        self.input_image_embed_size = input_image_embed_size
        self.input_text_embed_size = input_text_embed_size
        self.is_encoder_decoder = is_encoder_decoder
        self.layer_norm_eps = layer_norm_eps
        self.link_tower_shared = link_tower_shared
        self.link_tower_type = link_tower_type
        self.log_dir = log_dir
        self.loss_names = loss_names
        self.max_text_len = max_text_len
        self.mlp_ratio = mlp_ratio
        self.model_type = model_type
        self.nlvr2_head_format = nlvr2_head_format
        self.num_attention_heads = num_attention_heads
        self.num_hidden_layers = num_hidden_layers
        self.num_nodes = num_nodes
        self.only_load_cross_modal_from_meter = only_load_cross_modal_from_meter
        self.patch_size = patch_size
        self.resolution_before = resolution_before
        self.stop_gradient = stop_gradient
        self.task_head_layers = task_head_layers
        self.test_only = test_only
        self.tie_word_embeddings = tie_word_embeddings
        self.tokenizer = tokenizer
        self.unfreeze_RoBERTa_attention = unfreeze_RoBERTa_attention
        self.unfreeze_RoBERTa_embeddings = unfreeze_RoBERTa_embeddings
        self.unfreeze_RoBERTa_encoder = unfreeze_RoBERTa_encoder
        self.unfreeze_RoBERTa_layernorm = unfreeze_RoBERTa_layernorm
        self.unfreeze_ViT_attention = unfreeze_ViT_attention
        self.unfreeze_ViT_layernorm = unfreeze_ViT_layernorm
        self.vit = vit
        self.vit_layernorm_init_from_vit = vit_layernorm_init_from_vit
        self.vit_layernorm_shared = vit_layernorm_shared
        self.vit_remove_last = vit_remove_last
        self.vocab_size = vocab_size
        self.vqav2_label_size = vqav2_label_size
