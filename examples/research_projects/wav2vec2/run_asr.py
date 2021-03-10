#!/usr/bin/env python3
import logging
import re
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Union

import datasets
import numpy as np
import torch
import torch.nn as nn
from packaging import version

import librosa
from transformers import (
    HfArgumentParser,
    Trainer,
    TrainingArguments,
    Wav2Vec2ForCTC,
    Wav2Vec2Processor,
    is_apex_available,
    trainer_utils,
)


if is_apex_available():
    from apex import amp

if version.parse(torch.__version__) >= version.parse("1.6"):
    _is_native_amp_available = True
    from torch.cuda.amp import autocast


logger = logging.getLogger(__name__)


@dataclass
class ModelArguments:
    """
    Arguments pertaining to which model/config/tokenizer we are going to fine-tune from.
    """

    model_name_or_path: str = field(
        metadata={"help": "Path to pretrained model or model identifier from huggingface.co/models"}
    )
    cache_dir: Optional[str] = field(
        default=None,
        metadata={"help": "Where do you want to store the pretrained models downloaded from huggingface.co"},
    )
    freeze_feature_extractor: Optional[bool] = field(
        default=True, metadata={"help": "Whether to freeze the feature extractor layers of the model."}
    )
    verbose_logging: Optional[bool] = field(
        default=False,
        metadata={"help": "Whether to log verbose messages or not."},
    )


def configure_logger(model_args: ModelArguments, training_args: TrainingArguments):
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(name)s -   %(message)s",
        datefmt="%m/%d/%Y %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    logging_level = logging.WARNING
    if model_args.verbose_logging:
        logging_level = logging.DEBUG
    elif trainer_utils.is_main_process(training_args.local_rank):
        logging_level = logging.INFO
    logger.setLevel(logging_level)


@dataclass
class DataTrainingArguments:
    """
    Arguments pertaining to what data we are going to input our model for training and eval.

    Using `HfArgumentParser` we can turn this class
    into argparse arguments to be able to specify them on
    the command line.
    """

    dataset_name: str = field(
        default=None, metadata={"help": "The name of the dataset to use (via the datasets library)."}
    )
    dataset_config_name: Optional[str] = field(
        default=None, metadata={"help": "The configuration name of the dataset to use (via the datasets library)."}
    )
    train_split_name: Optional[str] = field(
        default="train",
        metadata={
            "help": "The name of the training data set split to use (via the datasets library). Defaults to 'train'"
        },
    )
    validation_split_name: Optional[str] = field(
        default="validation",
        metadata={
            "help": "The name of the validation data set split to use (via the datasets library). Defaults to 'validation'"
        },
    )
    target_feature_extractor_sampling_rate: Optional[bool] = field(
        default=False,
        metadata={"help": "Resample loaded audio to target feature extractor's sampling rate or not."},
    )
    orthography: Optional[str] = field(
        default="librispeech",
        metadata={
            "help": "Orthography used for normalization and tokenization: 'librispeech' (default), 'timit', or 'buckwalter'."
        },
    )
    overwrite_cache: bool = field(
        default=False, metadata={"help": "Overwrite the cached preprocessed datasets or not."}
    )
    preprocessing_num_workers: Optional[int] = field(
        default=None,
        metadata={"help": "The number of processes to use for the preprocessing."},
    )


@dataclass
class Orthography:
    """
    Orthography scheme used for text normalization and tokenization.

    Args:
        do_lower_case (:obj:`bool`, `optional`, defaults to :obj:`False`):
            Whether or not to accept lowercase input and lowercase the output when decoding.
        additional_tokens (:obj:`List[str]`, `optional`, defaults to :obj:`[]`):
            Tokens to add to vocabulary. Particularly useful for transliteration in ASCII.
        word_delimiter_token (:obj:`str`, `optional`, defaults to :obj:`None`):
            When set, overrides the tokenizer's default for `word_delimiter_token` and added to vocabulary.
        translation_table (:obj:`Dict[str, str]`, `optional`, defaults to :obj:`{}`):
            Table to use with `str.translate()` when preprocessing text (e.g., "-" -> " ").
        words_to_remove (:obj:`Set[str]`, `optional`, defaults to :obj:`set()`):
            Words to remove when preprocessing text (e.g., "sil").
    """

    do_lower_case: bool = False
    additional_tokens: Optional[List[str]] = field(default_factory=list)
    word_delimiter_token: Optional[str] = None
    translation_table: Optional[Dict[str, str]] = field(default_factory=dict)
    words_to_remove: Optional[Set[str]] = field(default_factory=set)

    @classmethod
    def from_name(cls, name: str) -> "Orthography":
        if name == "librispeech":
            return cls()
        if name == "timit":
            return cls(
                do_lower_case=True,
                translation_table=str.maketrans(
                    {"-": " "}
                ),  # break compounds like "quarter-century-old" and replace pauses "--"
            )
        if (
            name == "buckwalter"
        ):  # for example, 'arabic_speech_corpus' dataset (note the addition of '^' to transliteration scheme)
            return cls(
                additional_tokens=list("'|>&<}AbptvjHxd*rzs$SDTZEg_fqklmnhwYyFNKaui~o`{PJVG^"),
                word_delimiter_token="/",  # "|" is Arabic letter alef with madda above
                translation_table=str.maketrans({"-": " "}),  # sometimes used to represent pauses
                words_to_remove={"sil"},  # until we have a "<sil>" special token
            )
        raise ValueError(f"Unsupported orthography: '{name}'.")

    def preprocess_for_training(
        self, text: str
    ) -> str:  # TODO(elgeish) return a pipeline instead? Or rely on branch predictor as is
        if len(self.translation_table) > 0:
            text = text.translate(self.translation_table)
        if len(self.words_to_remove) == 0:
            text = " ".join(text.split())  # clean up whilespaces
        else:
            text = " ".join(w for w in text.split() if w not in self.words_to_remove)  # and clean up whilespaces
        return text

    def create_processor(self, model_args: ModelArguments) -> Wav2Vec2Processor:
        processor = Wav2Vec2Processor.from_pretrained(
            model_args.model_name_or_path,
            cache_dir=model_args.cache_dir,
            do_lower_case=self.do_lower_case,
        )
        unique_no_split_tokens = processor.tokenizer.unique_no_split_tokens
        processor.tokenizer.add_tokens(
            self.additional_tokens
        )  # tokens may already exist in vocabulary; `add_tokens` will deduplicate
        if self.word_delimiter_token is not None:
            processor.tokenizer.add_tokens(self.word_delimiter_token)
            processor.tokenizer.word_delimiter_token = self.word_delimiter_token
        processor.tokenizer.unique_no_split_tokens = (
            unique_no_split_tokens  # HACK workaround for https://github.com/huggingface/transformers/issues/10622
        )
        return processor


@dataclass
class DataCollatorCTCWithPadding:
    """
    Data collator that will dynamically pad the inputs received.
    Args:
        processor (:class:`~transformers.Wav2Vec2Processor`)
            The processor used for proccessing the data.
        padding (:obj:`bool`, :obj:`str` or :class:`~transformers.tokenization_utils_base.PaddingStrategy`, `optional`, defaults to :obj:`True`):
            Select a strategy to pad the returned sequences (according to the model's padding side and padding index)
            among:
            * :obj:`True` or :obj:`'longest'`: Pad to the longest sequence in the batch (or no padding if only a single
              sequence if provided).
            * :obj:`'max_length'`: Pad to a maximum length specified with the argument :obj:`max_length` or to the
              maximum acceptable input length for the model if that argument is not provided.
            * :obj:`False` or :obj:`'do_not_pad'` (default): No padding (i.e., can output a batch with sequences of
              different lengths).
        max_length (:obj:`int`, `optional`):
            Maximum length of the ``input_values`` of the returned list and optionally padding length (see above).
        max_length_labels (:obj:`int`, `optional`):
            Maximum length of the ``labels`` returned list and optionally padding length (see above).
        pad_to_multiple_of (:obj:`int`, `optional`):
            If set will pad the sequence to a multiple of the provided value.
            This is especially useful to enable the use of Tensor Cores on NVIDIA hardware with compute capability >=
            7.5 (Volta).
    """

    processor: Wav2Vec2Processor
    padding: Union[bool, str] = True
    max_length: Optional[int] = None
    max_length_labels: Optional[int] = None
    pad_to_multiple_of: Optional[int] = None
    pad_to_multiple_of_labels: Optional[int] = None

    def __call__(self, features: List[Dict[str, Union[List[int], torch.Tensor]]]) -> Dict[str, torch.Tensor]:
        # split inputs and labels since they have to be of different lenghts and need
        # different padding methods
        input_features = [{"input_values": feature["input_values"]} for feature in features]
        label_features = [{"input_ids": feature["labels"]} for feature in features]

        batch = self.processor.pad(
            input_features,
            padding=self.padding,
            max_length=self.max_length,
            pad_to_multiple_of=self.pad_to_multiple_of,
            return_tensors="pt",
        )
        with self.processor.as_target_processor():
            labels_batch = self.processor.pad(
                label_features,
                padding=self.padding,
                max_length=self.max_length_labels,
                pad_to_multiple_of=self.pad_to_multiple_of_labels,
                return_tensors="pt",
            )

        # replace padding with -100 to ignore loss correctly
        labels = labels_batch["input_ids"].masked_fill(labels_batch.attention_mask.ne(1), -100)

        batch["labels"] = labels

        return batch


class CTCTrainer(Trainer):
    def training_step(self, model: nn.Module, inputs: Dict[str, Union[torch.Tensor, Any]]) -> torch.Tensor:
        """
        Perform a training step on a batch of inputs.

        Subclass and override to inject custom behavior.

        Args:
            model (:obj:`nn.Module`):
                The model to train.
            inputs (:obj:`Dict[str, Union[torch.Tensor, Any]]`):
                The inputs and targets of the model.

                The dictionary will be unpacked before being fed to the model. Most models expect the targets under the
                argument :obj:`labels`. Check your model's documentation for all accepted arguments.

        Return:
            :obj:`torch.Tensor`: The tensor with training loss on this batch.
        """

        model.train()
        inputs = self._prepare_inputs(inputs)

        if self.use_amp:
            with autocast():
                loss = self.compute_loss(model, inputs)
        else:
            loss = self.compute_loss(model, inputs)

        if self.args.n_gpu > 1:
            if model.module.config.ctc_loss_reduction == "mean":
                loss = loss.mean()
            elif model.module.config.ctc_loss_reduction == "sum":
                loss = loss.sum() / (inputs["labels"] >= 0).sum()
            else:
                raise ValueError(f"{model.config.ctc_loss_reduction} is not valid. Choose one of ['mean', 'sum']")

        if self.args.gradient_accumulation_steps > 1:
            loss = loss / self.args.gradient_accumulation_steps

        if self.use_amp:
            self.scaler.scale(loss).backward()
        elif self.use_apex:
            with amp.scale_loss(loss, self.optimizer) as scaled_loss:
                scaled_loss.backward()
        elif self.deepspeed:
            self.deepspeed.backward(loss)
        else:
            loss.backward()

        return loss.detach()


def main():
    # See all possible arguments in src/transformers/training_args.py
    # or by passing the --help flag to this script.
    # We now keep distinct sets of args, for a cleaner separation of concerns.

    parser = HfArgumentParser((ModelArguments, DataTrainingArguments, TrainingArguments))

    model_args, data_args, training_args = parser.parse_args_into_dataclasses()
    configure_logger(model_args, training_args)

    model = Wav2Vec2ForCTC.from_pretrained(model_args.model_name_or_path, cache_dir=model_args.cache_dir)
    orthography = Orthography.from_name(data_args.orthography.lower())
    processor = orthography.create_processor(model_args)
    processor.tokenizer.save_pretrained(training_args.output_dir)

    train_dataset = datasets.load_dataset(
        data_args.dataset_name, data_args.dataset_config_name, split=data_args.train_split_name
    )
    val_dataset = datasets.load_dataset(
        data_args.dataset_name, data_args.dataset_config_name, split=data_args.validation_split_name
    )

    wer_metric = datasets.load_metric("wer")
    target_sr = processor.feature_extractor.sampling_rate if data_args.target_feature_extractor_sampling_rate else None
    vocabulary_chars_str = "".join(t for t in processor.tokenizer.get_vocab().keys() if len(t) == 1)
    vocabulary_text_cleaner = re.compile(  # remove characters not in vocabulary
        f"[^\s{re.escape(vocabulary_chars_str)}]",  # allow space in addition to chars in vocabulary
        flags=re.IGNORECASE if processor.tokenizer.do_lower_case else 0,
    )
    text_updates = []

    def prepare_example(example):  # TODO(elgeish) make use of caching and/or multiprocessing
        example["speech"], example["sampling_rate"] = librosa.load(example["file"], sr=target_sr)
        # Normalize and clean up text; order matters!
        updated_text = orthography.preprocess_for_training(example["text"])
        updated_text = vocabulary_text_cleaner.sub("", updated_text)
        if updated_text != example["text"]:
            text_updates.append((example["text"], updated_text))
            example["text"] = updated_text
        return example

    train_dataset = train_dataset.map(prepare_example, remove_columns=["file"])
    val_dataset = val_dataset.map(prepare_example, remove_columns=["file"])
    logger.warning(f"Updated {len(text_updates)} transcript(s) using '{data_args.orthography}' orthography rules.")
    if logger.isEnabledFor(logging.DEBUG):
        for original_text, updated_text in text_updates:
            logger.debug(f'Updated text: "{original_text}" -> "{updated_text}"')
    text_updates = None

    def prepare_dataset(batch):
        # check that all files have the correct sampling rate
        assert (
            len(set(batch["sampling_rate"])) == 1
        ), f"Make sure all inputs have the same sampling rate of {processor.feature_extractor.sampling_rate}."

        batch["input_values"] = processor(batch["speech"], sampling_rate=batch["sampling_rate"][0]).input_values
        with processor.as_target_processor():
            batch["labels"] = processor(batch["text"]).input_ids
        return batch

    train_dataset = train_dataset.map(
        prepare_dataset,
        batch_size=training_args.per_device_train_batch_size,
        batched=True,
        num_proc=data_args.preprocessing_num_workers,
    )
    val_dataset = val_dataset.map(
        prepare_dataset,
        batch_size=training_args.per_device_train_batch_size,
        batched=True,
        num_proc=data_args.preprocessing_num_workers,
    )

    data_collator = DataCollatorCTCWithPadding(processor=processor, padding=True)

    def compute_metrics(pred):
        pred_logits = pred.predictions
        pred_ids = np.argmax(pred_logits, axis=-1)

        pred.label_ids[pred.label_ids == -100] = processor.tokenizer.pad_token_id

        pred_str = processor.batch_decode(pred_ids)
        # we do not want to group tokens when computing the metrics
        label_str = processor.batch_decode(pred.label_ids, group_tokens=False)
        if logger.isEnabledFor(logging.DEBUG):
            for prediction, reference in zip(pred_str, label_str):
                logger.debug(f'reference: "{reference}"')
                logger.debug(f'prediction: "{prediction}"')

        wer = wer_metric.compute(predictions=pred_str, references=label_str)

        return {"wer": wer}

    if model_args.freeze_feature_extractor:
        model.freeze_feature_extractor()

    trainer = CTCTrainer(
        model=model,
        data_collator=data_collator,
        args=training_args,
        compute_metrics=compute_metrics,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        tokenizer=processor.feature_extractor,
    )

    trainer.train()


if __name__ == "__main__":
    main()
