# coding=utf-8
# Copyright 2020 The Google AI Language Team Authors, Allegro.pl and The HuggingFace Inc. team.
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
""" HerBERT configuration """

import logging

from .configuration_bert import BertConfig


logger = logging.getLogger(__name__)

HERBERT_PRETRAINED_CONFIG_ARCHIVE_MAP = {
    "allegro/herbert-base-cased": "https://s3.amazonaws.com/models.huggingface.co/bert/allegro/herbert-base-cased/config.json",
    "allegro/herbert-large-cased": "https://s3.amazonaws.com/models.huggingface.co/bert/allegro/herbert-large-cased/config.json",
}


class HerbertConfig(BertConfig):
    """
    This class overrides :class:`~transformers.BertConfig`. Please check the
    superclass for the appropriate documentation alongside usage examples.
    """

    pretrained_config_archive_map = HERBERT_PRETRAINED_CONFIG_ARCHIVE_MAP
    model_type = "herbert"
