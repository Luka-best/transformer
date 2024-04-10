# coding=utf-8
# Copyright 2024 The HuggingFace Team. All rights reserved.
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

import os
import unittest

from datasets import load_dataset

from transformers import AutoTokenizer, Rwkv5Tokenizer
from transformers.models.rwkv5.tokenization_rwkv5 import VOCAB_FILES_NAMES
from transformers.testing_utils import require_tokenizers, require_torch

from ...test_tokenization_common import TokenizerTesterMixin


@require_torch
@require_tokenizers
class RWKV5TokenizationTest(TokenizerTesterMixin, unittest.TestCase):
    tokenizer_class = Rwkv5Tokenizer
    # TODO we need a tokenizer list to make sure everything is tested
    rust_tokenizer_class = None
    test_rust_tokenizer = False
    from_pretrained_kwargs = {"add_prefix_space": True}
    test_seq2seq = False

    def setUp(self):
        super().setUp()
        vocab_tokens = [b'\x00', b'\x01', b'\x02', b'\x03', b'\x04', b'\x05', b'\x06', b'\x07', b'\x08', b'\t', b'\n', b'\x0b', b'\x0c', b'\r', b'\x0e', b'\x0f', b'\x10', b'\x11', b'\x12', b'\x13', b'\x14', b'\x15', b'\x16', b'\x17', b'\x18', b'\x19', b'\x1a', b'\x1b', b'\x1c', b'\x1d', b'\x1e', b'\x1f', b' ', b'!', b'"', b'#', b'$', b'%', b'&', b"'", b'(', b')', b'*', b'+', b',', b'-', b'.', b'/', b'0', b'1', b'2', b'3', b'4', b'5', b'6', b'7', b'8', b'9', b':', b';', b'<', b'=', b'>', b'?', b'@', b'A', b'B', b'C', b'D', b'E', b'F', b'G', b'H', b'I', b'J', b'K', b'L', b'M', b'N', b'O', b'P', b'Q', b'R', b'S', b'T', b'U', b'V', b'W', b'X', b'Y', b'Z', b'[', b'\\', b']', b'^', b'_', b'`', b'a', b'b', b'c']  # fmt: skip
        self.vocab_file = os.path.join(self.tmpdirname, VOCAB_FILES_NAMES["vocab_file"])
        with open(self.vocab_file, "w") as vocab_writer:
            for token in vocab_tokens:
                vocab_writer.write(str(token) + "\n")
        self.special_tokens_map = {"unk_token": "<s>"}

    def get_tokenizer(self, **kwargs):
        kwargs.update(self.special_tokens_map)
        return Rwkv5Tokenizer.from_pretrained(self.tmpdirname, **kwargs, trust_remote_code=True)

    def test_pretokenized_inputs(self):
        pass


class Rwkv5IntegrationTest(unittest.TestCase):
    def test_sample_prompt(self):
        tokenizer = AutoTokenizer.from_pretrained("ArthurZ/rwkv-5-utf", padding_side="left")
        prompt = "Hey how are you? 男：听说你们公司要派你去南方工作"
        ids = tokenizer.encode(prompt)
        print(ids)
        print(tokenizer.tokenize(prompt))
        print(tokenizer.convert_ids_to_tokens(tokenizer.encode(prompt)))
        print(tokenizer.convert_tokens_to_string(tokenizer.convert_ids_to_tokens(tokenizer.encode(prompt))))
        print(tokenizer.decode(tokenizer.encode(prompt)))

    def test_left_padding(self):
        tokenizer = AutoTokenizer.from_pretrained("ArthurZ/rwkv-5-utf", padding_side="left", pad_token="<s>")
        input_ids = tokenizer.encode(
            "Conceptually क ् रीम एंजलिस में दो मूल आयाम हैं - उत ् पाद और भूगोल ।", add_special_tokens=False
        )
        EXPECTED_INPUT_IDS = [48429, 35813, 22874, 33, 9495, 22882, 9489, 9477, 33, 2973, 144, 9458, 9465, 9480, 9488, 9484, 22881, 43260, 22877, 9494, 22881, 9491, 9480, 22873, 9478, 9487, 9477, 22886, 9493, 9458, 280, 33, 2973, 138, 9469, 33, 9495, 22879, 9487, 9471, 33, 2973, 149, 9479, 33, 9476, 9491, 9463, 9494, 9480, 33, 9496]  # fmt: skip
        self.assertEqual(input_ids, EXPECTED_INPUT_IDS)

        prompt = ['Chinese: 他补充道：“我们现在有 4 个月大没有糖尿病的老鼠，但它们曾经得过该病。”\n\nEnglish:', 'Chinese: 埃胡德·乌尔博士（新斯科舍省哈利法克斯市达尔豪西大学医学教授，加拿大糖尿病协会临床与科学部门教授）提醒，这项研究仍处在早期阶段。\n\nEnglish:', 'Chinese: 和其他一些专家一样，他对糖尿病能否治愈持怀疑态度。他指出，这些发现与已患有 1 型糖尿病的人无关。\n\nEnglish:', 'Chinese: 周一，瑞典学院诺贝尔文学委员会常务秘书萨拉·丹尼尔斯在瑞典广播电台的一档节目中向公众宣布，委员会因无法直接联系到鲍勃·迪伦，通知他获得了 2016 年诺贝尔文学奖，已经放弃了与他联系的尝试。\n\nEnglish:']  # fmt: skip
        inputs_ = tokenizer(prompt, padding=True)
        EXPECTED_INPUTS = {'input_ids': [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 48407, 59, 33, 10390, 16416, 10655, 17222, 43899, 12605, 10402, 14446, 11454, 13191, 287, 33, 10283, 13190, 11638, 13734, 13191, 15294, 12004, 14662, 14734, 15640, 18459, 19137, 10444, 11885, 10402, 13186, 15486, 12348, 17141, 16721, 14662, 10080, 9823, 261, 48487, 59], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 48407, 59, 33, 11514, 15737, 12363, 2453, 10306, 11979, 10936, 11606, 19133, 13034, 13033, 15034, 15864, 14787, 11164, 10788, 13764, 10660, 13033, 12154, 17136, 11979, 16805, 16501, 11638, 11871, 10913, 11871, 12996, 12809, 19137, 10842, 12745, 11638, 15294, 12004, 14662, 10926, 10423, 10288, 12216, 10261, 15034, 11871, 17303, 17723, 12996, 12809, 19134, 12848, 17363, 19137, 17148, 17999, 14880, 15087, 10383, 11621, 11454, 13057, 13199, 17775, 13619, 28329, 11, 48487, 59], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 48407, 59, 33, 11124, 10687, 10390, 10250, 10349, 10264, 11920, 10250, 13324, 19137, 10390, 11957, 15294, 12004, 14662, 15752, 11060, 13751, 12518, 12746, 12395, 14638, 12396, 12231, 10080, 10390, 12748, 10760, 19137, 17148, 10349, 10997, 14446, 10261, 12145, 12467, 13191, 284, 33, 11496, 15294, 12004, 14662, 14734, 10370, 13051, 10684, 28329, 11, 48487, 59], [0, 48407, 59, 33, 11105, 10250, 19137, 14523, 10689, 11871, 17796, 16741, 16873, 11979, 13012, 11871, 11733, 11098, 10423, 12182, 10843, 15036, 10325, 16102, 12705, 2453, 10291, 12001, 11979, 13033, 11454, 14523, 10689, 12210, 12925, 14600, 11022, 14734, 10250, 13351, 15907, 14778, 10285, 11047, 10678, 10420, 11908, 12155, 19137, 11733, 11098, 10423, 11416, 13051, 13764, 14781, 12824, 15671, 15304, 10792, 18298, 10861, 2453, 17159, 10431, 19137, 17189, 14862, 10390, 16056, 12348, 10333, 3493, 636, 33, 12201, 16741, 16873, 11979, 13012, 11871, 11665, 19137, 12145, 15486, 12983, 12269, 10333, 10261, 10390, 15671, 15304, 14734, 11986, 16707, 28329, 11, 48487, 59]], 'attention_mask': [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]]}  # fmt: skip
        self.assertDictEqual(dict(inputs_), EXPECTED_INPUTS)
        self.assertEqual(tokenizer.batch_decode(inputs_.input_ids, skip_special_tokens=True), prompt)

    @unittest.skip("This is just too slow")
    def test_integration_test_xnli(self):
        import tqdm

        pyth_tokenizer = AutoTokenizer.from_pretrained("ArthurZ/rwkv-5-utf", padding_side="left", pad_token="<s>")
        rust_tokenizer = pyth_tokenizer

        # dataset = load_dataset("code_x_glue_ct_code_to_text", "go")
        # for item in tqdm.tqdm(dataset["validation"]):
        #     string = item["code"]
        #     encoded1 = pyth_tokenizer.encode(string)
        #     encoded2 = rust_tokenizer.encode(string)

        #     self.assertEqual(encoded1, encoded2)

        #     decoded1 = pyth_tokenizer.decode(encoded1, skip_special_tokens=True)
        #     decoded2 = rust_tokenizer.decode(encoded2, skip_special_tokens=True)

        #     self.assertEqual(decoded1, decoded2)

        dataset = load_dataset("xnli", "all_languages")

        for item in tqdm.tqdm(dataset["train"]):
            for string in item["premise"].values():
                try:
                    encoded1 = pyth_tokenizer.encode(string)
                except UnicodeDecodeError:
                    print(f"Failed on :`{string}`")

                encoded2 = rust_tokenizer.encode(string)

                self.assertEqual(encoded1, encoded2)

                decoded1 = pyth_tokenizer.decode(encoded1, skip_special_tokens=True)
                decoded2 = rust_tokenizer.decode(encoded2, skip_special_tokens=True)

                self.assertEqual(decoded1, decoded2)


# TODO add integration tests slow. Maybe also work on fast?
