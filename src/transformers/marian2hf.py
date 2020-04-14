import argparse
from pathlib import Path

import numpy as np
import torch
import yaml

from durbango import lmap, pickle_save, remove_prefix
from transformers import BertConfig, BertModel, MarianConfig, MarianModel
from transformers.marian_constants import BERT_LAYER_CONVERTER, EMBED_CONVERTER
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from zipfile import ZipFile

import wget
import yaml
from transformers.tokenization_utils import ADDED_TOKENS_FILE, TOKENIZER_CONFIG_FILE
from transformers.tokenization_marian import MarianSPTokenizer
OPUS_MODELS_PATH = "/Users/shleifer/OPUS-MT-train/models"  # git clone git@github.com:Helsinki-NLP/Opus-MT.git


def convert_encoder_layer(opus_dict, layer_tag):
    sd = {}
    for k in opus_dict:
        if not k.startswith(layer_tag):
            continue
        stripped = remove_prefix(k, layer_tag)
        v = opus_dict[k].T  # besides embeddings, everything must be transposed.
        sd[BERT_LAYER_CONVERTER[stripped]] = torch.tensor(v).squeeze()
    return sd


def load_layers_(bmodel: BertModel, opus_state: dict):
    for i, layer in enumerate(bmodel.encoder.layer):
        layer_tag = f"decoder_l{i+1}_" if bmodel.config.is_decoder else f"encoder_l{i+1}_"
        sd = convert_encoder_layer(opus_state, layer_tag)
        layer.load_state_dict(sd, strict=True)


def convert_embeddings_(opus_state) -> dict:
    sd = {}
    for k in EMBED_CONVERTER:
        if k in opus_state:
            sd[EMBED_CONVERTER[k]] = torch.tensor(opus_state[k])
    return sd


CONFIG_KEY = "special:model.yml"


class OpusState:
    def __init__(self, npz_path):
        self.state_dict = np.load(npz_path)
        self.cfg = load_model_yaml(self.state_dict)
        self.state_keys = list(self.state_dict.keys())

    @property
    def extra_keys(self):
        extra = []
        for k in self.state_keys:
            if k.startswith("encoder_l"):
                continue
            if k.startswith("decoder_l"):
                continue
            if k == CONFIG_KEY:
                continue
            else:
                extra.append(k)
        return extra


def convert_to_berts(opus_path: str):
    opus_state: dict = np.load(opus_path)
    n_keys = len(opus_state)
    marian_cfg: dict = load_model_yaml(opus_state)
    vocab_size = opus_state["Wemb"].shape[0]
    hidden_size, intermediate_shape = opus_state["encoder_l1_ffn_W1"].shape
    cfg = MarianConfig(
        vocab_size=vocab_size,
        hidden_size=hidden_size,
        num_hidden_layers=int(marian_cfg["enc-depth"]),
        num_attention_heads=int(marian_cfg["transformer-heads"]),  # getattr(yaml_cfg, 'transformer-heads', 'swish'),
        intermediate_size=intermediate_shape,
        hidden_act=marian_cfg["transformer-aan-activation"],
    )
    model = MarianModel(cfg)
    print("loaded empty marian model")
    load_layers_(model.encoder, opus_state)
    print("loaded encoder")
    load_layers_(model.decoder.bert, opus_state)
    embs_state: dict = convert_embeddings_(opus_state)
    result = model.encoder.embeddings.load_state_dict(embs_state, strict=False)
    print(f"Embeddings: {result})")  # TODO(SS): logger
    # TODO(SS): tie weights
    # model.decoder.bert.embeddings.load_state_dict(embs_state, strict=False)
    return model

def load_yaml(path):
    with open(path) as f:
        return yaml.load(f, Loader=yaml.BaseLoader)

def load_model_yaml(opus_dict):
    cfg_str = "".join(lmap(chr, opus_dict[CONFIG_KEY]))
    yaml_cfg = load_yaml(cfg_str[:-1])
    for k in ["dec-depth", "enc-depth", "transformer-heads"]:
        yaml_cfg[k] = int(yaml_cfg[k])
    return yaml_cfg

DEFAULT_PATH = "/Users/shleifer/marian/opus_en_fr/opus.bpe32k-bpe32k.transformer.model1.npz.best-perplexity.npz"


def convert_model(model_path, save_dir):
    model = convert_to_berts(model_path)
    Path(save_dir).mkdir(exist_ok=True)
    model.save_pretrained(save_dir)


def find_model_file(dest_dir):  # this one better
    model_files = list(Path(dest_dir).glob("*.npz"))
    assert len(model_files) == 1
    model_file = model_files[0]
    return model_file



def parse_readmes(repo_path=OPUS_MODELS_PATH):
    results = {}
    for p in Path(repo_path).ls():
        n_dash = p.name.count("-")
        if n_dash == 0:
            continue
        else:
            lns = list(open(p / "README.md").readlines())
            results[p.name] = parse_readme(lns)
    return results


def parse_readme(lns):
    subres = {}
    for ln in [x.strip() for x in lns]:
        if not ln.startswith("*"):
            continue
        ln = ln[1:].strip()

        for k in ["download", "dataset", "models", "model", "pre-processing"]:
            if ln.startswith(k):
                break
        else:
            continue
        if k in ["dataset", "model", "pre-processing"]:
            splat = ln.split(":")
            _, v = splat
            subres[k] = v
        elif k == "download":
            v = ln.split("(")[-1][:-1]
            subres[k] = v
    return subres


def unzip(zip_path, dest_dir):
    with ZipFile(zip_path, "r") as zipObj:
        zipObj.extractall(dest_dir)


def download_unzip(url, dest_dir):
    filename = wget.download(url)
    unzip(filename, dest_dir)
    os.remove(filename)


def save_json(content, path):
    with open(path, "w") as f:
        json.dump(content, f)

def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)

def write_metadata(dest_dir):
    dest = Path(dest_dir)
    dname = dest.name.split("-")
    dct = dict(target_lang=dname[-1], source_lang="-".join(dname[:-1]))
    save_json(dct, dest_dir / TOKENIZER_CONFIG_FILE)


# def write_added_tokens_file(dest_dir, vocab_size):
#    added_tokens = {''}


def add_to_vocab_(vocab: Dict[str, int], special_tokens: List[str]):
    start = max(vocab.values()) + 1
    for tok in special_tokens:
        if tok in vocab:
            continue
        vocab[tok] = start
        start += 1

def add_special_tokens_to_vocab(model_dir: Path = 'en-de'):
    vocab = yaml.load(open('en-de/opus.spm32k-spm32k.vocab.yml'), Loader=yaml.BaseLoader)
    vocab = {k: int(v) for k,v in vocab.items()}
    add_to_vocab_(vocab, ['<pad>'])
    save_json(vocab, model_dir/'vocab.json')

import shutil
from pathlib import Path
def save_tokenizer(self, save_directory):
    # FIXME, what if you add tokens?
    dest = Path(save_directory)
    src_path = Path(self.init_kwargs['source_spm'])

    for dest_name in {"source.spm", "target.spm", "tokenizer_config.json"}:
        shutil.copyfile(src_path.parent / dest_name, dest / dest_name)
    save_json(tokenizer.encoder, dest/'vocab.json')

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # Required parameters
    parser.add_argument("--src", type=str, help="path to marian model dir", default=DEFAULT_PATH)
    parser.add_argument("--dest", type=str, default=None, help="Path to the output PyTorch model.")
    parser.add_argument(
        "--hf_config", default=None, type=str, help="Which huggingface architecture to use: bart-large-xsum"
    )
    args = parser.parse_args()

    source_dir = Path(args.src)
    dest_dir = f'converted-{source_dir.name}' if args.dest is None else args.dest
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(exist_ok=True)


    add_special_tokens_to_vocab(source_dir)
    tokenizer = MarianSPTokenizer.from_pretrained(str(source_dir))
    save_tokenizer(tokenizer, dest_dir)

    model_path = find_model_file(source_dir)
    convert_model(model_path, dest_dir)
