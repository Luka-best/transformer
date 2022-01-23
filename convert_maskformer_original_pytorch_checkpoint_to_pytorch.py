from __future__ import annotations
from ast import Tuple
from pathlib import Path
from PIL import Image
import requests
from sqlalchemy import over
import torch
import torch.nn as nn
from torch import Tensor
from dataclasses import dataclass, field
from pprint import pformat, pprint
from typing import Iterator, List, Any, Dict, Optional, Set
from src.transformers.models.maskformer.configuration_maskformer import ClassSpec, DatasetMetadata
from src.transformers.models.maskformer.modelling_maskformer import (
    MaskFormerConfig,
    MaskFormerForPanopticSegmentation,
    MaskFormerForPanopticSegmentationOutput,
    MaskFormerForSemanticSegmentation,
    MaskFormerForSemanticSegmentationOutput,
    MaskFormerModel,
)
from detectron2.config import get_cfg
from detectron2.projects.deeplab import add_deeplab_config
from MaskFormer.mask_former import add_mask_former_config, config
from MaskFormer.mask_former.mask_former_model import MaskFormer as OriginalMaskFormer
from detectron2.layers.wrappers import Conv2d as DetectronConv2d
import pytorch_lightning as pl
import torchvision.transforms as T
from detectron2.checkpoint import DetectionCheckpointer
from functools import partial
import logging
from detectron2.data import MetadataCatalog

pl.seed_everything(42)

StateDict = Dict[str, Tensor]
# easier to use pythong logging instead of going trough the hf utility logging file
# main issue there is the polluted namespace so I can't call `logging` directly
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


class TrackedStateDict:
    def __init__(self, to_track: Dict):
        """This class "tracks" a python dictionary by keeping track of which item is accessed.

        Args:
            to_track (Dict): The dictionary we wish to track
        """
        self.to_track = to_track
        self._seen: Set[str] = set()

    def __getitem__(self, key: str) -> Any:
        return self.to_track[key]

    def __setitem__(self, key: str, item: Any):
        self._seen.add(key)
        self.to_track[key] = item

    def diff(self) -> List[str]:
        """This method returns a set difference between the keys in the tracked state dict and the one we have access so far.
        This is an effective method to check if we have update all the keys

        Returns:
            List[str]: List of keys not yet updated
        """
        return set(list(self.to_track.keys())) - self._seen

    def copy(self) -> Dict:
        # proxy the call to the internal dictionary
        return self.to_track.copy()


# We will verify our results on an image of cute cats
def prepare_img():
    url = "http://images.cocodataset.org/val2017/000000039769.jpg"
    # url = "https://farm3.staticflickr.com/2628/3761093143_0233b13a00_z.jpg"
    # img_data = requests.get(url, stream=True).raw
    img_data = "/home/zuppif/Documents/Work/hugging_face/maskformer/input3.jpg"
    im = Image.open(img_data)
    return im


@dataclass
class Args:
    """Fake command line arguments needed by maskformer/detectron implementation"""

    config_file: str


def setup_cfg(args: Args):
    # load config from file and command-line arguments
    cfg = get_cfg()
    add_deeplab_config(cfg)
    add_mask_former_config(cfg)
    cfg.merge_from_file(args.config_file)
    cfg.freeze()
    return cfg


class OriginalMaskFormerConfigToOursConverter:
    def get_dataset_metadata(self, original_config: object) -> DatasetMetadata:
        ds_name: str = original_config.DATASETS.TEST[0]
        logging.info(f"Getting metadata from {ds_name}")
        metadata = MetadataCatalog.get(ds_name)
        # thing_classes and stuff_classes are equal
        labels = metadata.stuff_classes
        # same for colors
        colors = metadata.stuff_colors
        if metadata.get('thing_dataset_id_to_contiguous_id') is not None:
            print('thing_dataset_id_to_contiguous_id in', ds_name)
            thing_ids = metadata.thing_dataset_id_to_contiguous_id.values()
        else: 
            thing_ids = list(range(0, len(labels)))
        
        dataset_metadata = DatasetMetadata()
        dataset_metadata.classes = [None] * len(labels)
        for class_id, label, color in zip(range(len(labels)), labels, colors):
            dataset_metadata.classes[class_id] = ClassSpec(class_id in thing_ids, label, color)
        
        assert None not in dataset_metadata.classes
        return dataset_metadata

    def __call__(self, original_config: object) -> MaskFormerConfig:

        model = original_config.MODEL
        mask_former = model.MASK_FORMER
        swin = model.SWIN

        return MaskFormerConfig(
            dataset_metadata=self.get_dataset_metadata(original_config),
            fpn_feature_size=model.SEM_SEG_HEAD.CONVS_DIM,
            mask_feature_size=model.SEM_SEG_HEAD.MASK_DIM,
            num_classes=model.SEM_SEG_HEAD.NUM_CLASSES,
            no_object_weight=mask_former.NO_OBJECT_WEIGHT,
            num_queries=mask_former.NUM_OBJECT_QUERIES,
            swin_pretrain_img_size=swin.PRETRAIN_IMG_SIZE,
            swin_in_channels=3,
            swin_patch_size=swin.PATCH_SIZE,
            swin_embed_dim=swin.EMBED_DIM,
            swin_depths=swin.DEPTHS,
            swin_num_heads=swin.NUM_HEADS,
            swin_window_size=swin.WINDOW_SIZE,
            # TODO miss swin_attn_drop_rage, path_norm
            swin_drop_path_rate=swin.DROP_PATH_RATE,
            dice_weight=mask_former.DICE_WEIGHT,
            ce_weight=1.0,
            mask_weight=mask_former.MASK_WEIGHT,
            mask_classification=True,
            max_position_embeddings=1024,
            encoder_layers=6,
            encoder_ffn_dim=2048,
            encoder_attention_heads=8,
            decoder_layers=mask_former.DEC_LAYERS,
            decoder_ffn_dim=mask_former.DIM_FEEDFORWARD,
            decoder_attention_heads=mask_former.NHEADS,
            encoder_layerdrop=0.0,
            decoder_layerdrop=0.0,
            d_model=mask_former.HIDDEN_DIM,
            dropout=mask_former.DROPOUT,
            attention_dropout=0.0,
            activation_dropout=0.0,
            init_std=0.02,
            init_xavier_std=1.0,
            scale_embedding=False,
            auxiliary_loss=False,
            dilation=False,
        )


class MaskFormerCheckpointConverter:
    def __init__(self, original_model: OriginalMaskFormer, to_model: MaskFormerModel):
        self.original_model = original_model
        self.to_model = to_model

    def pop_all(self, renamed_keys: List[Tuple[str, str]], dst_state_dict: StateDict, src_state_dict: StateDict):
        for (src_key, dst_key) in renamed_keys:
            dst_state_dict[dst_key] = src_state_dict.pop(src_key)

    def replace_pixel_module(self, dst_state_dict: StateDict, src_state_dict: StateDict):
        dst_prefix: str = "pixel_level_module.pixel_decoder"
        src_prefix: str = "sem_seg_head.pixel_decoder"

        def replace_backbone():
            dst_prefix: str = "pixel_level_module.backbone"
            src_prefix: str = "backbone"

            renamed_keys = []

            for key in src_state_dict.keys():
                if key.startswith(src_prefix):
                    renamed_keys.append((key, key.replace(src_prefix, dst_prefix)))

            return renamed_keys

        def rename_keys_for_conv(detectron_conv: str, mine_conv: str):
            return [
                (f"{detectron_conv}.weight", f"{mine_conv}.0.weight"),
                # 2 cuz the have act in the middle -> rename it
                (f"{detectron_conv}.norm.weight", f"{mine_conv}.1.weight"),
                (f"{detectron_conv}.norm.bias", f"{mine_conv}.1.bias"),
            ]

        renamed_keys = [
            (f"{src_prefix}.mask_features.weight", f"{dst_prefix}.mask_proj.weight"),
            (f"{src_prefix}.mask_features.bias", f"{dst_prefix}.mask_proj.bias"),
            # the layers in the original one are in reverse order, stem is the last one!
        ]

        renamed_keys.extend(replace_backbone())

        renamed_keys.extend(rename_keys_for_conv(f"{src_prefix}.layer_4", f"{dst_prefix}.fpn.stem"))

        # add all the fpn layers (here we need some config parameters to know the size in advance)
        for src_i, dst_i in zip(range(3, 0, -1), range(0, 3)):
            renamed_keys.extend(
                rename_keys_for_conv(f"{src_prefix}.adapter_{src_i}", f"{dst_prefix}.fpn.layers.{dst_i}.proj")
            )
            renamed_keys.extend(
                rename_keys_for_conv(f"{src_prefix}.layer_{src_i}", f"{dst_prefix}.fpn.layers.{dst_i}.block")
            )

        self.pop_all(renamed_keys, dst_state_dict, src_state_dict)

    def rename_keys_in_detr_decoder(self, dst_state_dict: StateDict, src_state_dict: StateDict):
        dst_prefix: str = "transformer_module.detr_decoder"
        src_prefix: str = "sem_seg_head.predictor.transformer.decoder"
        # not sure why we are not popping direcetly here!
        # here we list all keys to be renamed (original name on the left, our name on the right)
        rename_keys = []
        for i in range(self.to_model.config.detr_decoder_layers):
            # decoder layers: 2 times output projection, 2 feedforward neural networks and 3 layernorms
            rename_keys.append(
                (
                    f"{src_prefix}.layers.{i}.self_attn.out_proj.weight",
                    f"{dst_prefix}.layers.{i}.self_attn.out_proj.weight",
                )
            )
            rename_keys.append(
                (
                    f"{src_prefix}.layers.{i}.self_attn.out_proj.bias",
                    f"{dst_prefix}.layers.{i}.self_attn.out_proj.bias",
                )
            )
            rename_keys.append(
                (
                    f"{src_prefix}.layers.{i}.multihead_attn.out_proj.weight",
                    f"{dst_prefix}.layers.{i}.encoder_attn.out_proj.weight",
                )
            )
            rename_keys.append(
                (
                    f"{src_prefix}.layers.{i}.multihead_attn.out_proj.bias",
                    f"{dst_prefix}.layers.{i}.encoder_attn.out_proj.bias",
                )
            )
            rename_keys.append((f"{src_prefix}.layers.{i}.linear1.weight", f"{dst_prefix}.layers.{i}.fc1.weight"))
            rename_keys.append((f"{src_prefix}.layers.{i}.linear1.bias", f"{dst_prefix}.layers.{i}.fc1.bias"))
            rename_keys.append((f"{src_prefix}.layers.{i}.linear2.weight", f"{dst_prefix}.layers.{i}.fc2.weight"))
            rename_keys.append((f"{src_prefix}.layers.{i}.linear2.bias", f"{dst_prefix}.layers.{i}.fc2.bias"))
            rename_keys.append(
                (f"{src_prefix}.layers.{i}.norm1.weight", f"{dst_prefix}.layers.{i}.self_attn_layer_norm.weight")
            )
            rename_keys.append(
                (f"{src_prefix}.layers.{i}.norm1.bias", f"{dst_prefix}.layers.{i}.self_attn_layer_norm.bias")
            )
            rename_keys.append(
                (f"{src_prefix}.layers.{i}.norm2.weight", f"{dst_prefix}.layers.{i}.encoder_attn_layer_norm.weight")
            )
            rename_keys.append(
                (f"{src_prefix}.layers.{i}.norm2.bias", f"{dst_prefix}.layers.{i}.encoder_attn_layer_norm.bias")
            )
            rename_keys.append(
                (f"{src_prefix}.layers.{i}.norm3.weight", f"{dst_prefix}.layers.{i}.final_layer_norm.weight")
            )
            rename_keys.append(
                (f"{src_prefix}.layers.{i}.norm3.bias", f"{dst_prefix}.layers.{i}.final_layer_norm.bias")
            )

        return rename_keys

    def replace_q_k_v_in_detr_decoder(self, dst_state_dict: StateDict, src_state_dict: StateDict):
        dst_prefix: str = "transformer_module.detr_decoder"
        src_prefix: str = "sem_seg_head.predictor.transformer.decoder"
        for i in range(self.to_model.config.detr_decoder_layers):
            # read in weights + bias of input projection layer of self-attention
            in_proj_weight = src_state_dict.pop(f"{src_prefix}.layers.{i}.self_attn.in_proj_weight")
            in_proj_bias = src_state_dict.pop(f"{src_prefix}.layers.{i}.self_attn.in_proj_bias")
            # next, add query, keys and values (in that order) to the state dict
            dst_state_dict[f"{dst_prefix}.layers.{i}.self_attn.q_proj.weight"] = in_proj_weight[:256, :]
            dst_state_dict[f"{dst_prefix}.layers.{i}.self_attn.q_proj.bias"] = in_proj_bias[:256]
            dst_state_dict[f"{dst_prefix}.layers.{i}.self_attn.k_proj.weight"] = in_proj_weight[256:512, :]
            dst_state_dict[f"{dst_prefix}.layers.{i}.self_attn.k_proj.bias"] = in_proj_bias[256:512]
            dst_state_dict[f"{dst_prefix}.layers.{i}.self_attn.v_proj.weight"] = in_proj_weight[-256:, :]
            dst_state_dict[f"{dst_prefix}.layers.{i}.self_attn.v_proj.bias"] = in_proj_bias[-256:]
            # read in weights + bias of input projection layer of cross-attention
            in_proj_weight_cross_attn = src_state_dict.pop(f"{src_prefix}.layers.{i}.multihead_attn.in_proj_weight")
            in_proj_bias_cross_attn = src_state_dict.pop(f"{src_prefix}.layers.{i}.multihead_attn.in_proj_bias")
            # next, add query, keys and values (in that order) of cross-attention to the state dict
            dst_state_dict[f"{dst_prefix}.layers.{i}.encoder_attn.q_proj.weight"] = in_proj_weight_cross_attn[:256, :]
            dst_state_dict[f"{dst_prefix}.layers.{i}.encoder_attn.q_proj.bias"] = in_proj_bias_cross_attn[:256]
            dst_state_dict[f"{dst_prefix}.layers.{i}.encoder_attn.k_proj.weight"] = in_proj_weight_cross_attn[
                256:512, :
            ]
            dst_state_dict[f"{dst_prefix}.layers.{i}.encoder_attn.k_proj.bias"] = in_proj_bias_cross_attn[256:512]
            dst_state_dict[f"{dst_prefix}.layers.{i}.encoder_attn.v_proj.weight"] = in_proj_weight_cross_attn[-256:, :]
            dst_state_dict[f"{dst_prefix}.layers.{i}.encoder_attn.v_proj.bias"] = in_proj_bias_cross_attn[-256:]

    def replace_detr_decoder(self, dst_state_dict: StateDict, src_state_dict: StateDict):
        dst_prefix: str = "transformer_module.detr_decoder"
        src_prefix: str = "sem_seg_head.predictor.transformer.decoder"
        renamed_keys = self.rename_keys_in_detr_decoder(dst_state_dict, src_state_dict)
        # add more
        renamed_keys.extend(
            [
                (f"{src_prefix}.norm.weight", f"{dst_prefix}.layernorm.weight"),
                (f"{src_prefix}.norm.bias", f"{dst_prefix}.layernorm.bias"),
            ]
        )

        self.pop_all(renamed_keys, dst_state_dict, src_state_dict)

        self.replace_q_k_v_in_detr_decoder(dst_state_dict, src_state_dict)

    def replace_transformer_module(self, dst_state_dict: StateDict, src_state_dict: StateDict):
        dst_prefix: str = "transformer_module"
        src_prefix: str = "sem_seg_head.predictor"

        self.replace_detr_decoder(dst_state_dict, src_state_dict)

        renamed_keys = [
            (f"{src_prefix}.query_embed.weight", f"{dst_prefix}.queries_embedder.weight"),
            (f"{src_prefix}.input_proj.weight", f"{dst_prefix}.input_proj.weight"),
            (f"{src_prefix}.input_proj.bias", f"{dst_prefix}.input_proj.bias"),
        ]

        self.pop_all(renamed_keys, dst_state_dict, src_state_dict)

    def replace_segmentation_module(self, dst_state_dict: StateDict, src_state_dict: StateDict):
        dst_prefix: str = "segmentation_module"
        src_prefix: str = "sem_seg_head.predictor"

        renamed_keys = [
            (f"{src_prefix}.class_embed.weight", f"{dst_prefix}.class_predictor.weight"),
            (f"{src_prefix}.class_embed.bias", f"{dst_prefix}.class_predictor.bias"),
        ]

        mlp_len = 3
        for i in range(mlp_len):
            renamed_keys.extend(
                [
                    (f"{src_prefix}.mask_embed.layers.{i}.weight", f"{dst_prefix}.mask_embedder.{i}.0.weight"),
                    (f"{src_prefix}.mask_embed.layers.{i}.bias", f"{dst_prefix}.mask_embedder.{i}.0.bias"),
                ]
            )

        self.pop_all(renamed_keys, dst_state_dict, src_state_dict)

    def __call__(self) -> MaskFormerModel:
        dst_state_dict = TrackedStateDict(self.to_model.state_dict())
        src_state_dict = self.original_model.state_dict()

        self.replace_pixel_module(dst_state_dict, src_state_dict)
        self.replace_transformer_module(dst_state_dict, src_state_dict)
        self.replace_segmentation_module(dst_state_dict, src_state_dict)

        logger.info(f"Missed keys are {pformat(dst_state_dict.diff())}")
        logger.info("🙌 Done")
        self.to_model.load_state_dict(dst_state_dict)

        return self.to_model

    @classmethod
    def from_original_config_and_checkpoint_file(
        cls, original_config_file: str, original_checkpoint_file: str
    ) -> MaskFormerCheckpointConverter:
        original_config = setup_cfg(Args(config_file=original_config_file))
        mask_former_kwargs = OriginalMaskFormer.from_config(original_config)

        original_model = OriginalMaskFormer(**mask_former_kwargs).eval()

        DetectionCheckpointer(original_model).load(original_checkpoint_file)

        config: MaskFormerConfig = OriginalMaskFormerConfigToOursConverter()(original_config)

        to_model = MaskFormerModel(config=config).eval()

        return cls(original_model, to_model)

    @staticmethod
    def using_dirs(checkpoints_dir: Path, config_dir: Path) -> Iterator[MaskFormerCheckpointConverter]:
        checkpoints: List[Path] = checkpoints_dir.glob("**/*.pkl")

        for checkpoint in checkpoints:
            logger.info(f"💪 Converting {checkpoint.stem}")
            # find associated config file
            config: Path = config_dir / checkpoint.parents[0].stem / "swin" / f"{checkpoint.stem}.yaml"
            yield MaskFormerCheckpointConverter.from_original_config_and_checkpoint_file(str(config), str(checkpoint))


checkpoints_dir = Path("/home/zuppif/Documents/Work/hugging_face/maskformer/weights")
config_dir = Path("/home/zuppif/Documents/Work/hugging_face/maskformer/MaskFormer/configs")


def test(src, dst):
    with torch.no_grad():

        # x = torch.zeros((1, 3, 384, 384))

        # src_features = src.backbone(x)
        # dst_features = dst.pixel_level_module.backbone(x.clone())

        # for src_feature, dst_feature in zip(src_features.values(), dst_features):
        #     assert torch.allclose(src_feature, dst_feature)

        # src_pixel_out = src.sem_seg_head.pixel_decoder.forward_features(src_features)
        # dst_pixel_out = dst.pixel_level_module(x)

        # assert torch.allclose(src_pixel_out[0], dst_pixel_out[1])
        # # turn off aux_loss loss
        # src.sem_seg_head.predictor.aux_loss = False
        # src_transformer_out = src.sem_seg_head.predictor(src_features["res5"], src_pixel_out[0])

        # dst_queries = dst.transformer_module(dst_pixel_out[0])
        # dst_transformer_out = dst.segmentation_module(dst_queries, dst_pixel_out[1])

        # assert torch.allclose(src_transformer_out["pred_logits"], dst_transformer_out["pred_logits"], atol=1e-4)

        # assert torch.allclose(src_transformer_out["pred_masks"], dst_transformer_out["pred_masks"], atol=1e-4)

        # src_out = src([{"image": x.squeeze(0)}])

        # dst_for_seg = MaskFormerForSemanticSegmentation(config=dst.config).eval()
        # dst_for_seg.model.load_state_dict(dst.state_dict())

        # dst_out: MaskFormerForSemanticSegmentationOutput = dst_for_seg(x)

        # assert torch.allclose(src_out[0]["sem_seg"], dst_out.segmentation, atol=1e-4)

        im = prepare_img()

        tr = T.Compose(
            [
                T.Resize((640, 640)),
                T.ToTensor(),
                T.Normalize(
                    mean=torch.tensor([123.675, 116.280, 103.530]) / 255.0,
                    std=torch.tensor([58.395, 57.120, 57.375]) / 255.0,
                ),
            ],
        )

        x = tr(im)

        # src_out = src([{"image": x}])
        # dst_out = dst_for_seg(x.unsqueeze(0))

        # assert torch.allclose(src_out[0]["sem_seg"], dst_out.segmentation, atol=1e-4)


        dst_for_pan_seg = MaskFormerForPanopticSegmentation(config=dst.config, overlap_mask_area_threshold=src.overlap_threshold, object_mask_threshold=src.object_mask_threshold).eval()
        dst_for_pan_seg.model.load_state_dict(dst.state_dict())

        src.panoptic_on = True

        src_out = src([{"image": x}])
        dst_out: MaskFormerForPanopticSegmentationOutput = dst_for_pan_seg(x.unsqueeze(0))
        # NOTE not all ds supports panoptic seg
        src_seg = src_out[0]["panoptic_seg"]
        print(src_seg[0].sum())
        print(dst_out.segmentation.sum())
        assert torch.allclose(src_out[0]["panoptic_seg"][0], dst_out.segmentation, atol=1e-4)

        for src_segment, dst_segment in zip(src_seg[1], dst_out.segments):
            assert src_segment['id'] == dst_segment['id']
            assert src_segment['category_id'] == dst_segment['category_id']
            assert src_segment['isthing'] == dst_segment['is_thing']

        logging.info("✅ Test passed!")


for converter in MaskFormerCheckpointConverter.using_dirs(checkpoints_dir, config_dir):
    converted = converter()
    test(converter.original_model, converted)


def test_with_img():
    im = prepare_img()

    tr = T.Compose(
        [
            T.Resize((640, 640)),
            T.ToTensor(),
            T.Normalize(
                mean=torch.tensor([123.675, 116.280, 103.530]) / 255.0,
                std=torch.tensor([58.395, 57.120, 57.375]) / 255.0,
            ),
        ],
    )

    x = tr(im)

    cfg = setup_cfg(Args())

    with torch.no_grad():

        from detectron2.checkpoint import DetectionCheckpointer

        mask_former_kwargs = OriginalMaskFormer.from_config(cfg)
        original_mask_former = OriginalMaskFormer(**mask_former_kwargs).eval()

        DetectionCheckpointer(original_mask_former).load(
            "/home/zuppif/Documents/Work/hugging_face/maskformer_swin_base_IN21k_384_bs16_160k_res640.pkl"
        )

        original_mask_former.sem_seg_head.predictor.aux_loss = False
        original_mask_former.eval()
        config = MaskFormerConfig()
        mask_former = MaskFormerModel(config=config).eval()
        # copy weights
        replace_maskformer(mask_former, original_mask_former)

        mask_former_for_seg = MaskFormerForSemanticSegmentation(config=config).eval()

        mask_former_for_seg.model.load_state_dict(mask_former.state_dict())

        original_outs = original_mask_former([{"image": x}])
        outs: MaskFormerForSemanticSegmentationOutput = mask_former_for_seg(x.unsqueeze(0))

        assert torch.allclose(original_outs[0]["sem_seg"], outs.segmentation, atol=1e-4)

        from torchvision.utils import draw_segmentation_masks
        from torchvision.transforms.functional import to_tensor

        img_with_mask = (to_tensor(im.resize((640, 640))) * 255).type(torch.uint8).permute(1, 2, 0).numpy()

        from detectron2.data import MetadataCatalog
        from detectron2.engine.defaults import DefaultPredictor
        from detectron2.utils.video_visualizer import VideoVisualizer
        from detectron2.utils.visualizer import ColorMode, Visualizer

        metadata = MetadataCatalog.get("ade20k_sem_seg_val")
        visualizer = Visualizer(img_with_mask, metadata)

        mask = original_outs[0]["sem_seg"].argmax(dim=0)
        mask = outs.segmentation[0].argmax(dim=0)
        vis_output = visualizer.draw_sem_seg(mask)

        vis_output.save("./test.png")

        # scores, labels = outs.pred_logits[0].softmax(-1).max(0)
        # print(scores, labels)
        # for mask in original_outs[0]["sem_seg"] > 0.5:
        #     img_with_mask = draw_segmentation_masks(img_with_mask, masks=mask, alpha=0.1)

        # import numpy as np
        # import matplotlib.pyplot as plt

        # import torchvision.transforms.functional as F

        # plt.rcParams["savefig.bbox"] = "tight"

        # def show(imgs):
        #     if not isinstance(imgs, list):
        #         imgs = [imgs]
        #     fix, axs = plt.subplots(ncols=len(imgs), squeeze=False)
        #     for i, img in enumerate(imgs):
        #         img = img.detach()
        #         img = F.to_pil_image(img)
        #         axs[0, i].imshow(np.asarray(img))
        #         axs[0, i].set(xticklabels=[], yticklabels=[], xticks=[], yticks=[])

        # show(img_with_mask)
        # plt.show()


def test_pan_seg():
    im = prepare_img()

    tr = T.Compose(
        [
            T.Resize((800, 1200)),
            T.ToTensor(),
            T.Normalize(
                mean=torch.tensor([123.675, 116.280, 103.530]) / 255.0,
                std=torch.tensor([58.395, 57.120, 57.375]) / 255.0,
            ),
        ],
    )

    x = tr(im)

    cfg = setup_cfg(
        Args(
            config_file="/home/zuppif/Documents/Work/hugging_face/transformers/MaskFormer/configs/coco-panoptic/swin/maskformer_panoptic_swin_base_IN21k_384_bs64_554k.yaml"
        )
    )

    with torch.no_grad():

        from detectron2.checkpoint import DetectionCheckpointer

        from detectron2.data import MetadataCatalog
        from detectron2.engine.defaults import DefaultPredictor
        from detectron2.utils.video_visualizer import VideoVisualizer
        from detectron2.utils.visualizer import ColorMode, Visualizer
        from torchvision.transforms.functional import to_tensor

        mask_former_kwargs = OriginalMaskFormer.from_config(cfg)
        original_mask_former = OriginalMaskFormer(**mask_former_kwargs).eval()

        DetectionCheckpointer(original_mask_former).load(
            "/home/zuppif/Documents/Work/hugging_face/maskformer_panoptic_swin_base_IN21k_384_bs64_554k.pkl"
        )
        original_mask_former.panoptic_on = True
        original_mask_former.sem_seg_head.predictor.aux_loss = False
        original_mask_former.eval()
        config = MaskFormerConfig(num_classes=133)
        mask_former = MaskFormerModel(config=config).eval()
        # copy weights
        replace_maskformer(mask_former, original_mask_former)

        mask_former_for_seg = MaskFormerForPanopticSegmentation(config=config).eval()
        mask_former_for_seg.model.load_state_dict(mask_former.state_dict())

        original_outs = original_mask_former([{"image": x}])
        # outs: MaskFormerForPanopticSegmentationOutput = mask_former_for_seg(x.unsqueeze(0))

        img_with_mask = (to_tensor(im.resize((1200, 800))) * 255).type(torch.uint8).permute(1, 2, 0).numpy()

        metadata = MetadataCatalog.get("coco_2017_val_panoptic")
        visualizer = Visualizer(img_with_mask, metadata)

        mask = original_outs[0]["panoptic_seg"][0]
        segments = original_outs[0]["panoptic_seg"][1]

        # mask = outs.segmentation
        # segments = outs.segments

        vis_output = visualizer.draw_panoptic_seg(mask, segments)

        vis_output.save("./test_pan.png")


# very_boring_test()
# test_with_img()

# test_pan_seg()
