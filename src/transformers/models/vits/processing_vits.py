# coding=utf-8
# Copyright 2023 The HuggingFace Inc. team. All rights reserved.
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
"""Speech processor class for VITS."""

from ...processing_utils import ProcessorMixin


class VITSProcessor(ProcessorMixin):
    r"""
    Constructs a VITS processor which wraps a feature extractor and a tokenizer into a single processor.

    [`VITSProcessor`] offers all the functionalities of [`VITSFeatureExtractor`] and [`VITSTokenizer`]. See
    the docstring of [`~VITSProcessor.__call__`] and [`~VITSProcessor.decode`] for more information.

    Args:
        feature_extractor (`VITSFeatureExtractor`):
            An instance of [`VITSFeatureExtractor`]. The feature extractor is a required input.
        tokenizer (`VITSTokenizer`):
            An instance of [`VITSTokenizer`]. The tokenizer is a required input.
    """
    feature_extractor_class = "VITSFeatureExtractor"
    tokenizer_class = "VITSTokenizer"

    def __init__(self, feature_extractor, tokenizer):
        super().__init__(feature_extractor, tokenizer)

    def __call__(self, *args, **kwargs):
        """
        Processes audio and text input, as well as audio and text targets.

        You can process audio by using the argument `audio`, or process audio targets by using the argument
        `audio_target`. This forwards the arguments to VITSFeatureExtractor's
        [`~VITSFeatureExtractor.__call__`].

        You can process text by using the argument `text`, or process text labels by using the argument `text_target`.
        This forwards the arguments to VITSTokenizer's [`~VITSTokenizer.__call__`].

        Valid input combinations are:

        - `text` only
        - `audio` only
        - `text_target` only
        - `audio_target` only
        - `text` and `audio_target`
        - `audio` and `audio_target`
        - `text` and `text_target`
        - `audio` and `text_target`

        Please refer to the docstring of the above two methods for more information.
        """
        audio = kwargs.pop("audio", None)
        text = kwargs.pop("text", None)
        text_target = kwargs.pop("text_target", None)
        audio_target = kwargs.pop("audio_target", None)
        sampling_rate = kwargs.pop("sampling_rate", None)

        if audio is not None and text is not None:
            raise ValueError(
                "Cannot process both `audio` and `text` inputs. Did you mean `audio_target` or `text_target`?"
            )
        if audio_target is not None and text_target is not None:
            raise ValueError(
                "Cannot process both `audio_target` and `text_target` inputs. Did you mean `audio` or `text`?"
            )
        if audio is None and audio_target is None and text is None and text_target is None:
            raise ValueError(
                "You need to specify either an `audio`, `audio_target`, `text`, or `text_target` input to process."
            )

        if audio is not None:
            inputs = self.feature_extractor(audio, *args, sampling_rate=sampling_rate, **kwargs)
        elif text is not None:
            inputs = self.tokenizer(text, **kwargs)
        else:
            inputs = None

        if audio_target is not None:
            targets = self.feature_extractor(audio_target=audio_target, *args, sampling_rate=sampling_rate, **kwargs)
            labels = targets["input_values"]
        elif text_target is not None:
            targets = self.tokenizer(text_target, **kwargs)
            labels = targets["input_ids"]
        else:
            targets = None

        if inputs is None:
            return targets

        if targets is not None:
            inputs["labels"] = labels

            decoder_attention_mask = targets.get("attention_mask")
            if decoder_attention_mask is not None:
                inputs["decoder_attention_mask"] = decoder_attention_mask

        return inputs

    def pad(self, *args, **kwargs):
        """
        Collates the audio and text inputs, as well as their targets, into a padded batch.

        Audio inputs are padded by VITSFeatureExtractor's [`~VITSFeatureExtractor.pad`]. Text inputs are padded
        by VITSTokenizer's [`~VITSTokenizer.pad`].

        Valid input combinations are:

        - `input_ids` only
        - `input_values` only
        - `labels` only, either log-mel spectrograms or text tokens
        - `input_ids` and log-mel spectrogram `labels`
        - `input_values` and text `labels`

        Please refer to the docstring of the above two methods for more information.
        """
        input_values = kwargs.pop("input_values", None)
        input_ids = kwargs.pop("input_ids", None)
        labels = kwargs.pop("labels", None)

        if input_values is not None and input_ids is not None:
            raise ValueError("Cannot process both `input_values` and `input_ids` inputs.")
        if input_values is None and input_ids is None and labels is None:
            raise ValueError(
                "You need to specify either an `input_values`, `input_ids`, or `labels` input to be padded."
            )

        if input_values is not None:
            inputs = self.feature_extractor.pad(input_values, *args, **kwargs)
        elif input_ids is not None:
            inputs = self.tokenizer.pad(input_ids, **kwargs)
        else:
            inputs = None

        if labels is not None:
            if "input_ids" in labels or (isinstance(labels, list) and "input_ids" in labels[0]):
                targets = self.tokenizer.pad(labels, **kwargs)
                labels = targets["input_ids"]
            else:
                feature_size_hack = self.feature_extractor.feature_size
                self.feature_extractor.feature_size = self.feature_extractor.num_mel_bins
                targets = self.feature_extractor.pad(labels, *args, **kwargs)
                self.feature_extractor.feature_size = feature_size_hack
                labels = targets["input_values"]
        else:
            targets = None

        if inputs is None:
            return targets

        if targets is not None:
            inputs["labels"] = labels

            decoder_attention_mask = targets.get("attention_mask")
            if decoder_attention_mask is not None:
                inputs["decoder_attention_mask"] = decoder_attention_mask

        return inputs

    def batch_decode(self, *args, **kwargs):
        """
        This method forwards all its arguments to VITSTokenizer's [`~VITSTokenizer.batch_decode`]. Please refer
        to the docstring of this method for more information.
        """
        return self.tokenizer.batch_decode(*args, **kwargs)

    def decode(self, *args, **kwargs):
        """
        This method forwards all its arguments to VITSTokenizer's [`~VITSTokenizer.decode`]. Please refer to
        the docstring of this method for more information.
        """
        return self.tokenizer.decode(*args, **kwargs)
