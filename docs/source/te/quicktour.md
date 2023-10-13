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

# శీఘ్ర పర్యటన

[[ఓపెన్-ఇన్-కోలాబ్]]

🤗 ట్రాన్స్‌ఫార్మర్‌లతో లేచి పరుగెత్తండి! మీరు డెవలపర్ అయినా లేదా రోజువారీ వినియోగదారు అయినా, ఈ శీఘ్ర పర్యటన మీకు ప్రారంభించడానికి సహాయం చేస్తుంది మరియు [`పైప్‌లైన్`] అనుమితి కోసం ఎలా ఉపయోగించాలో మీకు చూపుతుంది, [AutoClass](./model_doc/తో ప్రీట్రైన్డ్ మోడల్ మరియు ప్రిప్రాసెసర్/ ఆటో), మరియు PyTorch లేదా TensorFlowతో మోడల్‌కు త్వరగా శిక్షణ ఇవ్వండి. మీరు ఒక అనుభవశూన్యుడు అయితే, ఇక్కడ పరిచయం చేయబడిన భావనల గురించి మరింత లోతైన వివరణల కోసం మా ట్యుటోరియల్స్ లేదా [course](https://huggingface.co/course/chapter1/1)ని తనిఖీ చేయమని మేము సిఫార్సు చేస్తున్నాము.

మీరు ప్రారంభించడానికి ముందు, మీరు అవసరమైన అన్ని లైబ్రరీలను ఇన్‌స్టాల్ చేశారని నిర్ధారించుకోండి:

```bash
!pip install transformers datasets
```

మీరు మీ ప్రాధాన్య యంత్ర అభ్యాస ఫ్రేమ్‌వర్క్‌ను కూడా ఇన్‌స్టాల్ చేయాలి:

<frameworkcontent>
<pt>

```bash
pip install torch
```
</pt>
<tf>

```bash
pip install tensorflow
```
</tf>
</frameworkcontent>

## పైప్‌లైన్

<Youtube id="tiZFewofSLM"/>

[`పైప్‌లైన్`] అనుమితి కోసం ముందుగా శిక్షణ పొందిన నమూనాను ఉపయోగించడానికి సులభమైన మరియు వేగవంతమైన మార్గం. మీరు వివిధ పద్ధతులలో అనేక పనుల కోసం [`పైప్‌లైన్`] వెలుపల ఉపయోగించవచ్చు, వాటిలో కొన్ని క్రింది పట్టికలో చూపబడ్డాయి:


<Tip>

అందుబాటులో ఉన్న పనుల పూర్తి జాబితా కోసం, [పైప్‌లైన్ API సూచన](./main_classes/pipelines)ని తనిఖీ చేయండి.

</Tip>

Here is the translation in Telugu:

| **పని**                      | **వివరణ**                                                                                              | **మోడాలిటీ**    | **పైప్‌లైన్ ఐడెంటిఫైయర్**          |
|------------------------------|--------------------------------------------------------------------------------------------------------|-----------------|------------------------------------------|
| వచన వర్గీకరణు               | కొన్ని వచనాల అంతా ఒక లేబుల్‌ను కొడి                                                                   | NLP             | pipeline(task=“sentiment-analysis”)     |
| వచన సృష్టి                   | ప్రమ్పుటం కలిగినంత వచనం సృష్టించండి                                                                 | NLP             | pipeline(task=“text-generation”)        |
| సంక్షేపణ                     | వచనం లేదా పత్రం కొరకు సంక్షేపణ తయారుచేసండి                                        | NLP             | pipeline(task=“summarization”)          |
| చిత్రం వర్గీకరణు                | చిత్రంలో ఒక లేబుల్‌ను కొడి                                                           | కంప్యూటర్ విషయం | pipeline(task=“image-classification”) |
| చిత్రం విభజన                           | ఒక చిత్రంలో ప్రతి వ్యక్తిగత పిక్సల్‌ను ఒక లేబుల్‌గా నమోదు చేయండి (సెమాంటిక్, పానొప్టిక్, మరియు ఇన్స్టన్స్ విభజనలను మద్దతు చేస్తుంది)         | కంప్యూటర్ విషయం | pipeline(task=“image-segmentation”)   |
| వస్త్రం గుర్తువు                    | ఒక చిత్రంలో పదాల యొక్క బౌండింగ్ బాక్స్‌లను మరియు వస్త్రాల వర్గాలను అంచనా చేయండి      | కంప్యూటర్ విషయం | pipeline(task=“object-detection”)     |
| ఆడియో గుర్తువు                  | కొన్ని ఆడియో డేటానికి ఒక లేబుల్‌ను కొడి                                         | ఆడియో           | pipeline(task=“audio-classification”) |
| స్వయంచలన ప్రసంగ గుర్తువు   | ప్రసంగాన్ని వచనంగా వర్ణించండి                                                                         | ఆడియో           | pipeline(task=“automatic-speech-recognition”) |
| దృశ్య ప్రశ్న సంవాదం          | వచనం మరియు ప్రశ్నను నమోదు చేసిన చిత్రంతో ప్రశ్నకు సమాధానం ఇవ్వండి                     | బహుమూలిక          | pipeline(task=“vqa”)                   |
| పత్రం ప్రశ్న సంవాదం         | ప్రశ్నను పత్రం లేదా డాక్యుమెంట్‌తో సమాధానం ఇవ్వండి                               | బహుమూలిక          | pipeline(task="document-question-answering") |
| చిత్రం వ్రాసాయింగ్            | కొన్ని చిత్రానికి పిటియార్లను సృష్టించండి                                                         | బహుమూలిక          | pipeline(task="image-to-text")          |

