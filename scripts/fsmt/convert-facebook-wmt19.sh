#!/usr/bin/env bash

# this script acquires data and converts it to fsmt model
# it covers:
# - facebook/wmt19-ru-en
# - facebook/wmt19-en-ru
# - facebook/wmt19-de-en
# - facebook/wmt19-en-de

# this script needs to be run from the top level of the transformers repo
if [ ! -d "src/transformers" ]; then
    echo "Error: This script needs to be run from the top of the transformers repo"
    exit 1
fi

mkdir data

# get data (run once)

cd data
wget https://dl.fbaipublicfiles.com/fairseq/models/wmt19.en-de.joined-dict.ensemble.tar.gz
wget https://dl.fbaipublicfiles.com/fairseq/models/wmt19.de-en.joined-dict.ensemble.tar.gz
wget https://dl.fbaipublicfiles.com/fairseq/models/wmt19.en-ru.ensemble.tar.gz
wget https://dl.fbaipublicfiles.com/fairseq/models/wmt19.ru-en.ensemble.tar.gz
tar -xvzf wmt19.en-de.joined-dict.ensemble.tar.gz
tar -xvzf wmt19.de-en.joined-dict.ensemble.tar.gz
tar -xvzf wmt19.en-ru.ensemble.tar.gz
tar -xvzf wmt19.ru-en.ensemble.tar.gz
cd -

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
