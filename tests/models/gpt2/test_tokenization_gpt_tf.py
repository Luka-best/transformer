import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from transformers import AutoConfig, TFGPT2LMHeadModel, is_tensorflow_text_available, is_tf_available
from transformers.models.gpt2.tokenization_gpt2 import GPT2Tokenizer
from transformers.testing_utils import require_tensorflow_text, slow


if is_tensorflow_text_available():
    from transformers.models.gpt2 import TFGPT2Tokenizer

if is_tf_available():
    import tensorflow as tf


TOKENIZER_CHECKPOINTS = ["gpt2"]
TINY_MODEL_CHECKPOINT = "gpt2"

if is_tf_available():

    class ModelToSave(tf.Module):
        def __init__(self, tokenizer):
            super().__init__()
            self.tokenizer = tokenizer
            config = AutoConfig.from_pretrained(TINY_MODEL_CHECKPOINT)
            self.model = TFGPT2LMHeadModel.from_config(config)

        @tf.function(input_signature=(tf.TensorSpec((None,), tf.string, name="text"), ))
        def serving(self, inputs):
            tokenized = self.tokenizer(inputs)

            input_ids_dense = tokenized["input_ids"].to_tensor()
            input_mask = tf.cast(input_ids_dense > 0, tf.int32)
            outputs = self.model(
                input_ids=input_ids_dense,
                attention_mask=input_mask,
            )
            
            return outputs["logits"]


@require_tensorflow_text
class GPTTokenizationTest(unittest.TestCase):
    # The TF tokenizers are usually going to be used as pretrained tokenizers from existing model checkpoints,
    # so that's what we focus on here.

    def setUp(self):
        super().setUp()

        self.tokenizers = [
            GPT2Tokenizer.from_pretrained(checkpoint) for checkpoint in (TOKENIZER_CHECKPOINTS )
        ]
        self.tf_tokenizers = [TFGPT2Tokenizer.from_pretrained(checkpoint) for checkpoint in TOKENIZER_CHECKPOINTS]
        assert len(self.tokenizers) == len(self.tf_tokenizers)

        self.test_sentences = [
            "This is a straightforward English test sentence.",
            "This one has some weird characters\rto\nsee\r\nif  those\u00E9break things.",
            "Now we're going to add some Chinese: 一 二 三 一二三",
            "And some much more rare Chinese: 齉 堃 齉堃",
            "Je vais aussi écrire en français pour tester les accents",
            "Classical Irish also has some unusual characters, so in they go: Gaelaċ, ꝼ",
        ]
        self.paired_sentences = list(zip(self.test_sentences, self.test_sentences[::-1]))

    def test_output_equivalence(self):
        for tokenizer, tf_tokenizer in zip(self.tokenizers, self.tf_tokenizers):
            for test_inputs in self.test_sentences:
                python_outputs = tokenizer([test_inputs], return_tensors="tf")
                tf_outputs = tf_tokenizer([test_inputs])

                for key in python_outputs.keys():
                    # convert them to numpy to avoid messing with ragged tensors
                    python_outputs_values = python_outputs[key].numpy()
                    tf_outputs_values = tf_outputs[key].numpy()

                    self.assertTrue(tf.reduce_all(python_outputs_values.shape == tf_outputs_values.shape))
                    self.assertTrue(tf.reduce_all(tf.cast(python_outputs_values, tf.int64) == tf_outputs_values))

    @slow
    def test_graph_mode(self):
        for tf_tokenizer in self.tf_tokenizers:
            compiled_tokenizer = tf.function(tf_tokenizer)
            for test_inputs in self.test_sentences:
                test_inputs = tf.constant(test_inputs)
                compiled_outputs = compiled_tokenizer(test_inputs)
                eager_outputs = tf_tokenizer(test_inputs)

                for key in eager_outputs.keys():
                    self.assertTrue(tf.reduce_all(eager_outputs[key] == compiled_outputs[key]))

    @slow
    def test_saved_model(self):
        for tf_tokenizer in self.tf_tokenizers:
            model = ModelToSave(tokenizer=tf_tokenizer)
            test_inputs = tf.convert_to_tensor(self.test_sentences)
            out = model.serving(test_inputs)  # Build model with some sample inputs
            with TemporaryDirectory() as tempdir:
                save_path = Path(tempdir) / "saved.model"
                tf.saved_model.save(
                    model,
                    save_path,
                    signatures={
                        "serving_default":
                            model.serving
                    }
                )
                loaded_model = tf.saved_model.load(save_path)
            loaded_output = loaded_model.signatures["serving_default"](test_inputs)["output_0"]
            # We may see small differences because the loaded model is compiled, so we need an epsilon for the test
            self.assertLessEqual(tf.reduce_max(tf.abs(out - loaded_output)), 1e-5)
