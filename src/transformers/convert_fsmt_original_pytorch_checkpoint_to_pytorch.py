# coding=utf-8
# Copyright 2018 The HuggingFace Inc. team.
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
"""

Convert fairseq transform wmt19 checkpoint.

To convert run:
assuming the fairseq data is under data/wmt19.ru-en.ensemble, data/wmt19.en-ru.ensemble, etc

export ROOT=/code/huggingface/transformers-fair-wmt
cd $ROOT
mkdir data

# get data (run once)
wget https://dl.fbaipublicfiles.com/fairseq/models/wmt19.en-de.joined-dict.ensemble.tar.gz
wget https://dl.fbaipublicfiles.com/fairseq/models/wmt19.de-en.joined-dict.ensemble.tar.gz
wget https://dl.fbaipublicfiles.com/fairseq/models/wmt19.en-ru.ensemble.tar.gz
wget https://dl.fbaipublicfiles.com/fairseq/models/wmt19.ru-en.ensemble.tar.gz
tar -xvzf wmt19.en-de.joined-dict.ensemble.tar.gz
tar -xvzf wmt19.de-en.joined-dict.ensemble.tar.gz
tar -xvzf wmt19.en-ru.ensemble.tar.gz
tar -xvzf wmt19.ru-en.ensemble.tar.gz


# run conversions and uploads

export PAIR=ru-en
PYTHONPATH="src" python src/transformers/convert_fsmt_original_pytorch_checkpoint_to_pytorch.py --fsmt_checkpoint_path data/wmt19.$PAIR.ensemble/model4.pt --pytorch_dump_folder_path data/wmt19-$PAIR

export PAIR=en-ru
PYTHONPATH="src" python src/transformers/convert_fsmt_original_pytorch_checkpoint_to_pytorch.py --fsmt_checkpoint_path data/wmt19.$PAIR.ensemble/model4.pt --pytorch_dump_folder_path data/wmt19-$PAIR

export PAIR=de-en
PYTHONPATH="src" python src/transformers/convert_fsmt_original_pytorch_checkpoint_to_pytorch.py --fsmt_checkpoint_path data/wmt19.$PAIR.joined-dict.ensemble/model4.pt --pytorch_dump_folder_path data/wmt19-$PAIR

export PAIR=en-de
PYTHONPATH="src" python src/transformers/convert_fsmt_original_pytorch_checkpoint_to_pytorch.py --fsmt_checkpoint_path data/wmt19.$PAIR.joined-dict.ensemble/model4.pt --pytorch_dump_folder_path data/wmt19-$PAIR


# upload
cd data
transformers-cli upload -y wmt19-ru-en
transformers-cli upload -y wmt19-en-ru
transformers-cli upload -y wmt19-de-en
transformers-cli upload -y wmt19-en-de
cd -

# if updating just small files and not the large models, here is a script to generate the right commands:
perl -le 'for $f (@ARGV) { print qq[transformers-cli upload -y $_/$f --filename $_/$f] for map { "wmt19-$_" } ("en-ru", "ru-en", "de-en", "en-de")}' vocab-src.json vocab-tgt.json tokenizer_config.json config.json
# add/remove files as needed

# Caching note: Unfortunately due to CDN caching the uploaded model may be unavailable for up to 24hs after upload
# So the only way to start using the new model sooner is either:
# 1. download it to a local path and use that path as model_name
# 2. make sure you use: from_pretrained(..., use_cdn=False) everywhere

# happy translations


######################################################################################

Convert fairseq transform wmt16 en-de checkpoints from https://github.com/jungokasai/deep-shallow


pip install gdown

# get data (run once)

cd data
gdown 'https://drive.google.com/uc?id=1x_G2cjvM1nW5hjAB8-vWxRqtQTlmIaQU'
gdown 'https://drive.google.com/uc?id=1oA2aqZlVNj5FarxBlNXEHpBS4lRetTzU'
gdown 'https://drive.google.com/uc?id=1Wup2D318QYBFPW_NKI1mfP_hXOfmUI9r'
tar -xvzf trans_ende_12-1_0.2.tar.gz
tar -xvzf trans_ende-dist_12-1_0.2.tar.gz
tar -xvzf trans_ende-dist_6-1_0.2.tar.gz

gdown 'https://drive.google.com/uc?id=1mNufoynJ9-Zy1kJh2TA_lHm2squji0i9'
gdown 'https://drive.google.com/uc?id=1iO7um-HWoNoRKDtw27YUSgyeubn9uXqj'
tar -xvzf wmt16.en-de.deep-shallow.dist.tar.gz
tar -xvzf wmt16.en-de.deep-shallow.tar.gz

cp wmt16.en-de.deep-shallow/data-bin/dict.*.txt trans_ende_12-1_0.2
cp wmt16.en-de.deep-shallow.dist/data-bin/dict.*.txt trans_ende-dist_12-1_0.2
cp wmt16.en-de.deep-shallow.dist/data-bin/dict.*.txt trans_ende-dist_6-1_0.2
cp wmt16.en-de.deep-shallow/bpecodes trans_ende_12-1_0.2
cp wmt16.en-de.deep-shallow.dist/bpecodes trans_ende-dist_12-1_0.2
cp wmt16.en-de.deep-shallow.dist/bpecodes trans_ende-dist_6-1_0.2


# another set wmt19-6-6-de-en
gdown 'https://drive.google.com/uc?id=1j6z9fYdlUyOYsh7KJoumRlr1yHczxR5T'
gdown 'https://drive.google.com/uc?id=1yT7ZjqfvUYOBXvMjeY8uGRHQFWoSo8Q5'
gdown 'https://drive.google.com/uc?id=15gAzHeRUCs-QV8vHeTReMPEh1j8excNE'
tar -xvzf wmt19.de-en.tar.gz
tar -xvzf wmt19_deen_base_dr0.1_1.tar.gz
tar -xvzf wmt19_deen_big_dr0.1_2.tar.gz
cp wmt19.de-en/data-bin/dict.*.txt wmt19_deen_base_dr0.1_1
cp wmt19.de-en/data-bin/dict.*.txt wmt19_deen_big_dr0.1_2

cd -


# run conversions and uploads

# wmt16-en-de set

PYTHONPATH="src" python src/transformers/convert_fsmt_original_pytorch_checkpoint_to_pytorch.py --fsmt_checkpoint_path data/trans_ende-dist_12-1_0.2/checkpoint_top5_average.pt --pytorch_dump_folder_path data/wmt16-en-de-dist-12-1

PYTHONPATH="src" python src/transformers/convert_fsmt_original_pytorch_checkpoint_to_pytorch.py --fsmt_checkpoint_path data/trans_ende-dist_6-1_0.2/checkpoint_top5_average.pt --pytorch_dump_folder_path data/wmt16-en-de-dist-6-1

PYTHONPATH="src" python src/transformers/convert_fsmt_original_pytorch_checkpoint_to_pytorch.py --fsmt_checkpoint_path data/trans_ende_12-1_0.2/checkpoint_top5_average.pt --pytorch_dump_folder_path data/wmt16-en-de-12-1


# wmt19-de-en set

PYTHONPATH="src" python src/transformers/convert_fsmt_original_pytorch_checkpoint_to_pytorch.py --fsmt_checkpoint_path data/wmt19_deen_base_dr0.1_1/checkpoint_best.pt --pytorch_dump_folder_path data/wmt19-de-en-6-6-base

PYTHONPATH="src" python src/transformers/convert_fsmt_original_pytorch_checkpoint_to_pytorch.py --fsmt_checkpoint_path data/wmt19_deen_big_dr0.1_2/checkpoint_best.pt --pytorch_dump_folder_path data/wmt19-de-en-6-6-big


# upload
cd data
transformers-cli upload -y wmt16-en-de-dist-12-1
transformers-cli upload -y wmt16-en-de-dist-6-1
transformers-cli upload -y wmt16-en-de-12-1
transformers-cli upload -y wmt19-de-en-6-6-base
transformers-cli upload -y wmt19-de-en-6-6-big
cd -


# XXX: move into model card

git clone https://github.com/huggingface/transformers
cd transformers
export PAIR=en-de
export DATA_DIR=data/$PAIR
export SAVE_DIR=data/$PAIR
export BS=64
export NUM_BEAMS=5
mkdir -p $DATA_DIR
sacrebleu -t wmt19 -l $PAIR --echo src > $DATA_DIR/val.source
sacrebleu -t wmt19 -l $PAIR --echo ref > $DATA_DIR/val.target

MODEL_PATH=/code/huggingface/transformers-fair-wmt/data/wmt16-en-de-dist-12-1
echo $PAIR $MODEL_PATH
PYTHONPATH="src:examples/seq2seq" python examples/seq2seq/run_eval.py $MODEL_PATH $DATA_DIR/val.source $SAVE_DIR/test_translations.txt --reference_path $DATA_DIR/val.target --score_path $SAVE_DIR/test_bleu.json --bs $BS --task translation --num_beams $NUM_BEAMS

MODEL_PATH=/code/huggingface/transformers-fair-wmt/data/wmt16-en-de-dist-6-1
echo $PAIR $MODEL_PATH
PYTHONPATH="src:examples/seq2seq" python examples/seq2seq/run_eval.py $MODEL_PATH $DATA_DIR/val.source $SAVE_DIR/test_translations.txt --reference_path $DATA_DIR/val.target --score_path $SAVE_DIR/test_bleu.json --bs $BS --task translation --num_beams $NUM_BEAMS

MODEL_PATH=/code/huggingface/transformers-fair-wmt/data/wmt16-en-de-12-1
echo $PAIR $MODEL_PATH
PYTHONPATH="src:examples/seq2seq" python examples/seq2seq/run_eval.py $MODEL_PATH $DATA_DIR/val.source $SAVE_DIR/test_translations.txt --reference_path $DATA_DIR/val.target --score_path $SAVE_DIR/test_bleu.json --bs $BS --task translation --num_beams $NUM_BEAMS

checkpoint_top5_average.pt:

num_beams=5

chkpt file| top5_average | best    |
----------|--------------|---------|
dist-12-1 | 29.9134      | 30.2591 |
dist-6-1  | 29.9837      | 29.3349 |
12-1      | 26.4008      | 24.1803 |

checkpoint_best.pt


# wmt19-de-en set

export PAIR=de-en
export DATA_DIR=data/$PAIR
export SAVE_DIR=data/$PAIR
export BS=64
export NUM_BEAMS=5
mkdir -p $DATA_DIR
sacrebleu -t wmt19 -l $PAIR --echo src > $DATA_DIR/val.source
sacrebleu -t wmt19 -l $PAIR --echo ref > $DATA_DIR/val.target

MODEL_PATH=/code/huggingface/transformers-fair-wmt/data/wmt19-de-en-6-6-base
echo $PAIR $MODEL_PATH
PYTHONPATH="src:examples/seq2seq" python examples/seq2seq/run_eval.py $MODEL_PATH $DATA_DIR/val.source $SAVE_DIR/test_translations.txt --reference_path $DATA_DIR/val.target --score_path $SAVE_DIR/test_bleu.json --bs $BS --task translation --num_beams $NUM_BEAMS

MODEL_PATH=/code/huggingface/transformers-fair-wmt/data/wmt19-de-en-6-6-big
echo $PAIR $MODEL_PATH
PYTHONPATH="src:examples/seq2seq" python examples/seq2seq/run_eval.py $MODEL_PATH $DATA_DIR/val.source $SAVE_DIR/test_translations.txt --reference_path $DATA_DIR/val.target --score_path $SAVE_DIR/test_bleu.json --bs $BS --task translation --num_beams $NUM_BEAMS




```


"""

import argparse
import json
import logging
import os
import re
from collections import OrderedDict
from os.path import basename, dirname

import fairseq
import torch
from fairseq import hub_utils
from fairseq.data.dictionary import Dictionary

from transformers import WEIGHTS_NAME
from transformers.configuration_fsmt import FSMTConfig
from transformers.modeling_fsmt import FSMTForConditionalGeneration
from transformers.tokenization_fsmt import VOCAB_FILES_NAMES
from transformers.tokenization_utils_base import TOKENIZER_CONFIG_FILE


logging.basicConfig(level=logging.INFO)

ORG_NAME = "stas"  # XXX: will become facebook

json_indent = 2


def rewrite_dict_keys(d):
    # (1) remove word breaking symbol, (2) add word ending symbol where the word is not broken up,
    # e.g.: d = {'le@@': 5, 'tt@@': 6, 'er': 7} => {'le': 5, 'tt': 6, 'er</w>': 7}
    d2 = dict((re.sub(r"@@$", "", k), v) if k.endswith("@@") else (re.sub(r"$", "</w>", k), v) for k, v in d.items())
    keep_keys = "<s> <pad> </s> <unk>".split()
    # restore the special tokens
    for k in keep_keys:
        del d2[f"{k}</w>"]
        d2[k] = d[k]  # restore
    return d2


def write_model_card(model_card_dir, src_lang, tgt_lang):

    texts = {
        "en": "Machine learning is great, isn't it?",
        "ru": "Машинное обучение - это здорово, не так ли?",
        "de": "Maschinelles Lernen ist großartig, oder?",
    }

    # BLUE scores as follows:
    # "pair": [fairseq, transformers]
    scores = {
        "en-ru": ["[36.4](http://matrix.statmt.org/matrix/output/1914?run_id=6724)", "33.29"],
        "ru-en": ["[41.3](http://matrix.statmt.org/matrix/output/1907?run_id=6937)", "38.93"],
        "de-en": ["[42.3](http://matrix.statmt.org/matrix/output/1902?run_id=6750)", "41.18"],
        "en-de": ["[43.1](http://matrix.statmt.org/matrix/output/1909?run_id=6862)", "42.79"],
    }
    pair = f"{src_lang}-{tgt_lang}"

    readme = f"""
---

<!-- This file has been auto-generated by src/transformers/convert_fsmt_original_pytorch_checkpoint_to_pytorch.py - DO NOT EDIT or your changes will be lost -->

language: {src_lang}, {tgt_lang}
thumbnail:
tags:
- translation
- wmt19
license: Apache 2.0
datasets:
- http://www.statmt.org/wmt19/ ([test-set](http://matrix.statmt.org/test_sets/newstest2019.tgz?1556572561))
metrics:
- http://www.statmt.org/wmt19/metrics-task.html
---

# FSMT

## Model description

This is a ported version of [fairseq wmt19 transformer](https://github.com/pytorch/fairseq/blob/master/examples/wmt19/README.md) for {src_lang}-{tgt_lang}.

For more details, please see, [Facebook FAIR's WMT19 News Translation Task Submission](https://arxiv.org/abs/1907.06616).

The abbreviation FSMT stands for FairSeqMachineTranslation

All four models are available:

* [wmt19-en-ru](https://huggingface.co/{ORG_NAME}/wmt19-en-ru)
* [wmt19-ru-en](https://huggingface.co/{ORG_NAME}/wmt19-ru-en)
* [wmt19-en-de](https://huggingface.co/{ORG_NAME}/wmt19-en-de)
* [wmt19-de-en](https://huggingface.co/{ORG_NAME}/wmt19-de-en)

## Intended uses & limitations

#### How to use

```python
from transformers.tokenization_fsmt import FSMTTokenizer
from transformers.modeling_fsmt import FSMTForConditionalGeneration
mname = "{ORG_NAME}/wmt19-{src_lang}-{tgt_lang}"
tokenizer = FSMTTokenizer.from_pretrained(mname)
model = FSMTForConditionalGeneration.from_pretrained(mname)

input = "{texts[src_lang]}
input_ids = tokenizer.encode(input, return_tensors="pt")
outputs = model.generate(input_ids)
decoded = tokenizer.decode(outputs[0], skip_special_tokens=True)
print(decoded) # {texts[tgt_lang]}

```

#### Limitations and bias

- The original (and this ported model) doesn't seem to handle well inputs with repeated sub-phrases, [content gets truncated](https://discuss.huggingface.co/t/issues-with-translating-inputs-containing-repeated-phrases/981)

## Training data

Pretrained weights were left identical to the original model released by fairseq. For more details, please, see the [paper](https://arxiv.org/abs/1907.06616)

## Eval results

pair   | fairseq | transformers
-------|---------|----------
{pair}  | {scores[pair][0]} | {scores[pair][1]}


`transformers`` currently doesn't support model ensemble, therefore the best performing checkpoint was ported (``model4.pt``).


The score was calculated using this code:

```bash
git clone https://github.com/huggingface/transformers
cd transformers
export PAIR={pair}
export DATA_DIR=data/$PAIR
export SAVE_DIR=data/$PAIR
export BS=8
export NUM_BEAMS=50
mkdir -p $DATA_DIR
sacrebleu -t wmt19 -l $PAIR --echo src > $DATA_DIR/val.source
sacrebleu -t wmt19 -l $PAIR --echo ref > $DATA_DIR/val.target
echo $PAIR
PYTHONPATH="src:examples/seq2seq" python examples/seq2seq/run_eval.py {ORG_NAME}/wmt19-$PAIR $DATA_DIR/val.source $SAVE_DIR/test_translations.txt --reference_path $DATA_DIR/val.target --score_path $SAVE_DIR/test_bleu.json --bs $BS --task translation --num_beams $NUM_BEAMS
```

## TODO

- port model ensemble (fairseq uses 4 model checkpoints)

"""
    os.makedirs(model_card_dir, exist_ok=True)
    path = os.path.join(model_card_dir, "README.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(readme)


def convert_fsmt_checkpoint_to_pytorch(fsmt_checkpoint_path, pytorch_dump_folder_path):

    # prep
    assert os.path.exists(fsmt_checkpoint_path)
    os.makedirs(pytorch_dump_folder_path, exist_ok=True)
    print(f"Writing results to {pytorch_dump_folder_path}")

    # handle various types of models

    checkpoint_file = basename(fsmt_checkpoint_path)
    fsmt_folder_path = dirname(fsmt_checkpoint_path)

    cls = fairseq.model_parallel.models.transformer.ModelParallelTransformerModel
    models = cls.hub_models()
    kwargs = {"bpe": "fastbpe", "tokenizer": "moses"}
    data_name_or_path = "."
    # note: since the model dump is old, fairseq has upgraded its model some
    # time later, and it does a whole lot of rewrites and splits on the saved
    # weights, therefore we can't use torch.load() directly on the model file.
    # see: upgrade_state_dict(state_dict) in fairseq_model.py
    print(f"using checkpoint {checkpoint_file}")
    chkpt = hub_utils.from_pretrained(
        fsmt_folder_path, checkpoint_file, data_name_or_path, archive_map=models, **kwargs
    )

    args = dict(vars(chkpt["args"]))

    src_lang = args["source_lang"]
    tgt_lang = args["target_lang"]

    data_root = dirname(pytorch_dump_folder_path)
    model_dir = basename(pytorch_dump_folder_path)
    proj_root = dirname(dirname(dirname(os.path.realpath(__file__))))

    # dicts
    src_dict_file = os.path.join(fsmt_folder_path, f"dict.{src_lang}.txt")
    tgt_dict_file = os.path.join(fsmt_folder_path, f"dict.{tgt_lang}.txt")

    src_dict = Dictionary.load(src_dict_file)
    src_vocab = rewrite_dict_keys(src_dict.indices)
    src_vocab_size = len(src_vocab)
    src_vocab_file = os.path.join(pytorch_dump_folder_path, "vocab-src.json")
    print(f"Generating {src_vocab_file}")
    with open(src_vocab_file, "w", encoding="utf-8") as f:
        f.write(json.dumps(src_vocab, ensure_ascii=False, indent=json_indent))

    tgt_dict = Dictionary.load(tgt_dict_file)
    tgt_vocab = rewrite_dict_keys(tgt_dict.indices)
    tgt_vocab_size = len(tgt_vocab)
    tgt_vocab_file = os.path.join(pytorch_dump_folder_path, "vocab-tgt.json")
    print(f"Generating {tgt_vocab_file}")
    with open(tgt_vocab_file, "w", encoding="utf-8") as f:
        f.write(json.dumps(tgt_vocab, ensure_ascii=False, indent=json_indent))

    # merges_file (bpecodes)
    merges_file = os.path.join(pytorch_dump_folder_path, VOCAB_FILES_NAMES["merges_file"])
    fsmt_merges_file = os.path.join(fsmt_folder_path, "bpecodes")
    with open(fsmt_merges_file, encoding="utf-8") as fin:
        merges = fin.read()
    merges = re.sub(r" \d+$", "", merges, 0, re.M)  # remove frequency number
    print(f"Generating {merges_file}")
    with open(merges_file, "w", encoding="utf-8") as fout:
        fout.write(merges)

    # model config
    fsmt_model_config_file = os.path.join(pytorch_dump_folder_path, "config.json")

    # validate bpe/tokenizer config, as currently it's hardcoded to moses+fastbpe -
    # may have to modify the tokenizer if a different type is used by a future model
    assert args["bpe"] == "fastbpe", f"need to extend tokenizer to support bpe={args['bpe']}"
    assert args["tokenizer"] == "moses", f"need to extend tokenizer to support bpe={args['tokenizer']}"

    model_conf = {
        "architectures": ["FSMTForConditionalGeneration"],
        "model_type": "fsmt",
        "activation_dropout": args["activation_dropout"],
        "activation_function": "relu",
        "attention_dropout": args["attention_dropout"],
        "d_model": args["decoder_embed_dim"],
        "dropout": args["dropout"],
        "init_std": 0.02,
        "max_position_embeddings": args["max_source_positions"],
        "num_hidden_layers": args["encoder_layers"],
        "src_vocab_size": src_vocab_size,
        "tgt_vocab_size": tgt_vocab_size,
        "langs": [src_lang, tgt_lang],
        "encoder_attention_heads": args["encoder_attention_heads"],
        "encoder_ffn_dim": args["encoder_ffn_embed_dim"],
        "encoder_layerdrop": args["encoder_layerdrop"],
        "encoder_layers": args["encoder_layers"],
        "decoder_attention_heads": args["decoder_attention_heads"],
        "decoder_ffn_dim": args["decoder_ffn_embed_dim"],
        "decoder_layerdrop": args["decoder_layerdrop"],
        "decoder_layers": args["decoder_layers"],
        "bos_token_id": 0,
        "pad_token_id": 1,
        "eos_token_id": 2,
        "is_encoder_decoder": True,
        "scale_embedding": not args["no_scale_embedding"],
        "tie_word_embeddings": args["share_all_embeddings"],
    }

    print(f"Generating {fsmt_model_config_file}")
    with open(fsmt_model_config_file, "w", encoding="utf-8") as f:
        f.write(json.dumps(model_conf, ensure_ascii=False, indent=json_indent))

    # tokenizer config
    fsmt_tokenizer_config_file = os.path.join(pytorch_dump_folder_path, TOKENIZER_CONFIG_FILE)

    tokenizer_conf = {
        "langs": [src_lang, tgt_lang],
        "model_max_length": 1024,
    }

    print(f"Generating {fsmt_tokenizer_config_file}")
    with open(fsmt_tokenizer_config_file, "w", encoding="utf-8") as f:
        f.write(json.dumps(tokenizer_conf, ensure_ascii=False, indent=json_indent))

    # model
    model = chkpt["models"][0]
    model_state_dict = model.state_dict()

    # rename keys to start with 'model.'
    model_state_dict = OrderedDict(("model." + k, v) for k, v in model_state_dict.items())

    # remove unneeded keys
    ignore_keys = [
        "model.model",
        "model.encoder.version",
        "model.decoder.version",
        "model.encoder_embed_tokens.weight",
        "model.decoder_embed_tokens.weight",
    ]
    for k in ignore_keys:
        model_state_dict.pop(k, None)

    config = FSMTConfig.from_pretrained(pytorch_dump_folder_path)
    model_new = FSMTForConditionalGeneration(config)

    # check that it loads ok
    model_new.load_state_dict(model_state_dict, strict=False)

    # save
    pytorch_weights_dump_path = os.path.join(pytorch_dump_folder_path, WEIGHTS_NAME)
    print(f"Generating {pytorch_weights_dump_path}")
    torch.save(model_state_dict, pytorch_weights_dump_path)

    # model card
    model_card_dir = os.path.join(proj_root, "model_cards", ORG_NAME, model_dir)
    print(f"Generating model_card {src_lang}-{tgt_lang}")
    write_model_card(model_card_dir, src_lang, tgt_lang)

    print("Conversion is done!")
    print("\nLast step is to upload the files to s3")
    print(f"cd {data_root}")
    print(f"transformers-cli upload {model_dir}")
    # XXX: this is invalid - waiting on issue to be resolved
    print("Note: CDN caches files for up to 24h, so use `from_pretrained(mname, use_cdn=False)` to force redownload")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # Required parameters
    parser.add_argument(
        "--fsmt_checkpoint_path",
        default=None,
        type=str,
        required=True,
        help="Path to the official PyTorch checkpoint file which is expected to reside in the dump dir with dicts, bpecodes, etc.",
    )
    parser.add_argument(
        "--pytorch_dump_folder_path", default=None, type=str, required=True, help="Path to the output PyTorch model."
    )
    args = parser.parse_args()
    convert_fsmt_checkpoint_to_pytorch(args.fsmt_checkpoint_path, args.pytorch_dump_folder_path)
