<!--Copyright 2022 The HuggingFace Team. All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with
the License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
specific language governing permissions and limitations under the License.

⚠️ Note that this file is in Markdown but contain specific syntax for our doc-builder (similar to MDX) that may not be
rendered properly in your Markdown viewer.

-->

# UnivNet

## Overview

The UnivNet model was proposed in [UnivNet: A Neural Vocoder with Multi-Resolution Spectrogram Discriminators for High-Fidelity Waveform Generation](https://arxiv.org/abs/2106.07889) by Won Jang, Dan Lim, Jaesam Yoon, Bongwan Kin, and Juntae Kim.
The UnivNet model is a generative adversarial network (GAN) trained to synthesize high fidelity speech waveforms. Only the generator of the model, which maps a conditioning log-mel spectrogram and optional noise sequence to a speech waveform (e.g. a vocoder), is implemented here.

The abstract from the paper is the following:

*Most neural vocoders employ band-limited mel-spectrograms to generate waveforms. If full-band spectral features are used as the input, the vocoder can be provided with as much acoustic information as possible. However, in some models employing full-band mel-spectrograms, an over-smoothing problem occurs as part of which non-sharp spectrograms are generated. To address this problem, we propose UnivNet, a neural vocoder that synthesizes high-fidelity waveforms in real time. Inspired by works in the field of voice activity detection, we added a multi-resolution spectrogram discriminator that employs multiple linear spectrogram magnitudes computed using various parameter sets. Using full-band mel-spectrograms as input, we expect to generate high-resolution signals by adding a discriminator that employs spectrograms of multiple resolutions as the input. In an evaluation on a dataset containing information on hundreds of speakers, UnivNet obtained the best objective and subjective results among competing models for both seen and unseen speakers. These results, including the best subjective score for text-to-speech, demonstrate the potential for fast adaptation to new speakers without a need for training from scratch.*

Tips:

- The `noise_waveform` argument for [`UnivNetGan.forward`] should be standard Gaussian noise (such as from `torch.randn`) of shape `([batch_size], noise_length, config.model_in_channels)`. If not supplied, it will be randomly generated; you will most likely want to supply a `noise_length` argument in this case to get a waveform of the desired length. A `generator` can also be specified for reproducibility.
- When creating a [`UnivNetGanConfig`], the `resblock_kernel_sizes`, `resblock_stride_sizes`, and `resblock_dilation_sizes` arguments should have the same length (which corresponds to the number of outer resnet blocks in the vocoder).

This model was contributed by [dg845](https://huggingface.co/dg845).
To the best of my knowledge, there is no official code release, but an unofficial implementation can be found at [mindslab-ai/univnet](https://github.com/mindslab-ai/univnet).


## UnivNetGanConfig

[[autodoc]] UnivNetGanConfig

## UnivNetGan

[[autodoc]] UnivNetGan
    - forward