# coding=utf-8
# Copyright 2018 HuggingFace Inc..
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


import argparse
import logging
import sys
import unittest
from time import time
from unittest.mock import patch

from transformers.testing_utils import require_torch_tpu


logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger()


def get_setup_file():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f")
    args = parser.parse_args()
    return args.f


@require_torch_tpu
class TorchXLAExamplesTests(unittest.TestCase):
    def test_run_glue(self):
        import xla_spawn

        stream_handler = logging.StreamHandler(sys.stdout)
        logger.addHandler(stream_handler)

        output_directory = "run_glue_output"

        testargs = f"""
            text-classification/run_glue.py
            --num_cores=8
            text-classification/run_glue.py
            --do_train
            --do_eval
            --task_name=MRPC
            --data_dir=../glue_data/MRPC
            --cache_dir=./cache_dir
            --num_train_epochs=1
            --max_seq_length=128
            --learning_rate=3e-5
            --output_dir={output_directory}
            --overwrite_output_dir
            --logging_steps=5
            --save_steps=5
            --overwrite_cache
            --tpu_metrics_debug
            --model_name_or_path=bert-base-cased
            --per_device_train_batch_size=64
            --per_device_eval_batch_size=64
            --evaluate_during_training
            --overwrite_cache
            """.split()
        with patch.object(sys, "argv", testargs):
            start = time()
            xla_spawn.main()
            end = time()

            result = {}
            with open(f"{output_directory}/eval_results_mrpc.txt") as f:
                lines = f.readlines()
                for line in lines:
                    key, value = line.split(" = ")
                    result[key] = float(value)

            del result["eval_loss"]
            for value in result.values():
                # Assert that the model trains
                self.assertGreaterEqual(value, 0.70)

            # Assert that the script takes less than 100 seconds to make sure it doesn't hang.
            self.assertLess(end - start, 100)
