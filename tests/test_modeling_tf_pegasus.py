"""Documentation string."""


import os
import unittest

from transformers import BartForConditionalGeneration, PegasusConfig, PegasusTokenizer, is_tf_available
from transformers.file_utils import cached_property
from transformers.testing_utils import require_tf, slow, torch_device

from .test_configuration_common import ConfigTester
from .test_modeling_tf_common import TFModelTesterMixin, ids_tensor


BANK_SNIPPET = (
    "To ensure a smooth flow of bank resolutions to the necessary signatories, "
    "I am requesting that Enron Treasury first route the bank resolutions to Angela Davis "
    "(EWS Legal) to be initialed before being routed to John Lavorato or Louise Kitchen.\n"
    "If you have any questions please call me at 3-6544."
    "Thank you for your attention to this matter."
)

if is_tf_available():
    import tensorflow as tf
    from transformers import TFPegasusLegacyModel, TFPegasusPretrainedModel
    from transformers.modeling_tf_pegasus import encode, decode
    from .test_modeling_bart import ModelTester
    from transformers.configuration_pegasus import PegasusConfig
    from .test_modeling_tf_common import TFModelTesterMixin, ids_tensor


class TFPegasusModelTester:
    def __init__(
        self, parent,
    ):
        self.parent = parent
        self.batch_size = 13
        self.seq_length = 7
        self.is_training = True
        self.use_labels = False
        self.vocab_size = 99
        self.hidden_size = 16
        self.num_hidden_layers = 2
        self.num_attention_heads = 4
        self.intermediate_size = 4
        self.hidden_act = "gelu"
        self.hidden_dropout_prob = 0.1
        self.attention_probs_dropout_prob = 0.1
        self.max_position_embeddings = 20
        self.eos_token_id = 2
        self.pad_token_id = 1
        self.bos_token_id = 0

    def prepare_config_and_inputs_for_common(self):
        input_ids = ids_tensor([self.batch_size, self.seq_length], self.vocab_size)  # .clamp(3,)

        input_mask = ids_tensor([self.batch_size, self.seq_length], vocab_size=2)

        config = PegasusConfig(
            vocab_size=self.vocab_size,
            d_model=self.hidden_size,
            encoder_layers=self.num_hidden_layers,
            decoder_layers=self.num_hidden_layers,
            encoder_attention_heads=self.num_attention_heads,
            decoder_attention_heads=self.num_attention_heads,
            encoder_ffn_dim=self.intermediate_size,
            decoder_ffn_dim=self.intermediate_size,
            dropout=self.hidden_dropout_prob,
            attention_dropout=self.attention_probs_dropout_prob,
            max_position_embeddings=self.max_position_embeddings,
            eos_token_id=1,
            bos_token_id=None,
            pad_token_id=0,
        )
        # inputs_dict = prepare_bart_inputs_dict(config, input_ids)
        # input_ids[:, -1] = config.eos_token_id
        return config, {"inputs": input_ids, "attention_mask": input_mask, "training": True}


class TFPegasusModelTest(TFModelTesterMixin, unittest.TestCase):
    is_encoder_decoder = True
    all_model_classes = (TFPegasusPretrainedModel,) if is_tf_available() else ()

    def setUp(self):
        self.model_tester = TFPegasusModelTester(self)
        self.config_tester = ConfigTester(self, config_class=PegasusConfig, d_model=32)


@require_tf
class IntegrationTest(unittest.TestCase):
    @cached_property
    def model(self):
        raise NotImplementedError("no s3 yet")

    # TODO: refactor to follow transformers' standard testing pipeline
    # @slow
    def test_pegasus_aeslc_model(self):
        model_dir = "../pegasus/ckpt/aeslc"
        spm_model = "../pegasus/ckpt/c4.unigram.newline.10pct.96000.model"
        assert os.path.exists(model_dir)

        self.assertTrue(tf.compat.v1.train.checkpoint_exists(model_dir))
        config = PegasusConfig(vocab_size=96000 + 103, d_model=1024, num_beams=8)

        # #hidden_size = 1024
        # #filter_size = 4096
        # num_heads = 16
        # num_encoder_layers = 16
        # num_decoder_layers = 16
        # label_smoothing = 0.0
        # dropout = 0.1
        # beam_size = 8
        # beam_alpha = 0.6

        with tf.Graph().as_default() as graph:
            with tf.compat.v1.Session() as sess:
                model = TFPegasusLegacyModel(config)

                # run the model to build all variables (but not initialized yet)
                dummy_inputs = {"inputs": tf.ones((2, 7), tf.int64), "targets": tf.ones((2, 5), tf.int64)}
                loss, outputs = model(dummy_inputs, True)
                self.assertEqual(loss.shape, [])
                self.assertEqual(outputs["logits"].shape, [2, 5, config.vocab_size])

                # create assignment map
                ignore_name = ["Adafactor", "global_step"]
                var_list = tf.compat.v1.global_variables(scope=None)
                ckpt_var_list = tf.train.list_variables(model_dir)
                ckpt_var_list = [var for var in ckpt_var_list if not any(ign in var[0] for ign in ignore_name)]
                new_var_name_dict = {var.name: var for var in var_list}
                assignment_map = {}
                for var in ckpt_var_list:
                    old_var_name = var[0]
                    new_var_name = var[0] + ":0"
                    assert new_var_name in new_var_name_dict
                    assignment_map[old_var_name] = new_var_name_dict[new_var_name]

                # define the initialization (but not intialized until global_variables_initializer is called)
                tf.compat.v1.train.init_from_checkpoint(model_dir, assignment_map)

                # check running
                raw_input_str = BANK_SNIPPET
                raw_target_str = "Treasury Bank Resolutions"  # or something close

                input_str = tf.compat.v1.placeholder(tf.string, shape=[1,], name=None)
                target_str = tf.compat.v1.placeholder(tf.string, shape=[1,], name=None)

                # tokenization
                input_ids = encode(input_str, 512, spm_model, encoder_type="sentencepiece")

                target_ids = encode(target_str, 32, spm_model, encoder_type="sentencepiece")

                input_ids = tf.reshape(input_ids, [1, 512])
                target_ids = tf.reshape(target_ids, [1, 32])

                output_ids = model.predict(
                    {"inputs": input_ids, "targets": target_ids}, 32, config.num_beams, beam_alpha=0.6
                )
                self.assertEqual(output_ids["outputs"].shape, [1, 32])
                # decode to str
                output_str = decode(output_ids["outputs"], spm_model, encoder_type="sentencepiece")
                sess.run(tf.compat.v1.global_variables_initializer())
                # Run it
                feed_dict = {input_str: [raw_input_str], target_str: [raw_target_str]}
                results, emb = sess.run([output_str, model.embedded_inputs], feed_dict=feed_dict)

                after_time, after_stack, logits, enc_input, encoder_states = sess.run(
                    [
                        model.signalled,
                        model.after_stack,
                        model.logits,
                        model.encoder_layer_input,
                        model.encoder_states,
                    ],
                    feed_dict=feed_dict,
                )

        print(f"Summary: {results}")
        print_tensor("1. embedded", emb)
        print_tensor("2. after pos", after_time)
        print_tensor("3. 2-1", after_time - emb)
        print_tensor("4. encoder layer 0 input", enc_input)
        print_tensor("5. encoder layer 1 input", encoder_states[0])

        # import ipdb; ipdb.set_trace()
        # print(f'after_time: {after_time}')
        # print(f'after_stack: {after_stack}')
        # print(f'logits: {logits}')

    def test_eager_pegasus(self):
        model_dir = "../pegasus/ckpt/aeslc"
        spm_model = "../pegasus/ckpt/c4.unigram.newline.10pct.96000.model"
        assert os.path.exists(model_dir)

        self.assertTrue(tf.compat.v1.train.checkpoint_exists(model_dir))
        config = PegasusConfig(vocab_size=96000 + 103, d_model=1024, num_beams=8)

        # #hidden_size = 1024
        # #filter_size = 4096
        # num_heads = 16
        # num_encoder_layers = 16
        # num_decoder_layers = 16
        # label_smoothing = 0.0
        # dropout = 0.1
        # beam_size = 8
        # beam_alpha = 0.6

        # run the model to build all variables (but not initialized yet)
        model = TFPegasusPretrainedModel(config)
        dummy_inputs = {"inputs": tf.ones((2, 7), tf.int64), "targets": tf.ones((2, 5), tf.int64)}
        loss, outputs = model(dummy_inputs, True)
        self.assertEqual(loss.shape, [])
        self.assertEqual(outputs["logits"].shape, [2, 5, config.vocab_size])
        model.restore

        # create assignment map
        ignore_name = ["Adafactor", "global_step"]
        # var_list = tf.compat.v1.global_variables(scope=None)
        ckpt_var_list = tf.train.list_variables(model_dir)
        ckpt_var_list = [var for var in ckpt_var_list if not any(ign in var[0] for ign in ignore_name)]
        new_var_name_dict = {var.name: var for var in var_list}
        assignment_map = {}
        for var in ckpt_var_list:
            old_var_name = var[0]
            new_var_name = var[0] + ":0"
            assert new_var_name in new_var_name_dict
            assignment_map[old_var_name] = new_var_name_dict[new_var_name]

        # define the initialization (but not intialized until global_variables_initializer is called)
        tf.compat.v1.train.init_from_checkpoint(model_dir, assignment_map)

        # check running
        raw_input_str = (
            "To ensure a smooth flow of bank resolutions to the necessary signatories, "
            "I am requesting that Enron Treasury first route the bank resolutions to Angela Davis "
            "(EWS Legal) to be initialed before being routed to John Lavorato or Louise Kitchen.\n"
            "If you have any questions please call me at 3-6544."
            "Thank you for your attention to this matter."
        )
        raw_target_str = "Treasury Bank Resolutions"  # or something close

        # input_str = tf.compat.v1.placeholder(tf.string, shape=[1, ], name=None)
        # target_str = tf.compat.v1.placeholder(tf.string, shape=[1, ], name=None)

        # tokenization
        input_ids = encode(raw_input_str, 512, spm_model, encoder_type="sentencepiece")
        target_ids = encode(raw_target_str, 32, spm_model, encoder_type="sentencepiece")

        input_ids = tf.reshape(input_ids, [1, 512])
        target_ids = tf.reshape(target_ids, [1, 32])

        output_ids = model.predict({"inputs": input_ids, "targets": target_ids,}, 32, config.num_beams, beam_alpha=0.6)
        self.assertEqual(output_ids["outputs"].shape, [1, 32])

        # decode to str
        output_str = decode(output_ids["outputs"], spm_model, encoder_type="sentencepiece")
        print(output_str)
        #
        # sess.run(tf.compat.v1.global_variables_initializer())
        #
        # print(sess.run(output_str,
        #                feed_dict={input_str: [raw_input_str], target_str: [raw_target_str]}))

    def test_bart_pegasus(self):
        tok = PegasusTokenizer.from_pretrained("sshleifer/pegasus")
        model = BartForConditionalGeneration.from_pretrained(
            "sshleifer/pegasus/aeslc", scale_embedding=True, num_beams=1
        ).to(torch_device)
        batch = tok([BANK_SNIPPET], return_tensors="pt").to(torch_device)
        summary = tok.batch_decode(model.generate(batch.input_ids), skip_special_tokens=False)[0]
        self.assertEqual(summary, "Bank Resolutions")


def print_tensor(msg, t):
    # assert t.shape
    slice = t[:, :3, :3]
    print(f"{msg}: shape: {t.shape}, slice: {slice}")
