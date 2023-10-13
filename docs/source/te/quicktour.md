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


[`పైప్‌లైన్`] యొక్క ఉదాహరణను సృష్టించడం ద్వారా మరియు మీరు దానిని ఉపయోగించాలనుకుంటున్న పనిని పేర్కొనడం ద్వారా ప్రారంభించండి. ఈ గైడ్‌లో, మీరు సెంటిమెంట్ విశ్లేషణ కోసం [`పైప్‌లైన్`]ని ఉదాహరణగా ఉపయోగిస్తారు:

```py
>>> from transformers import pipeline

>>> classifier = pipeline("sentiment-analysis")
```

సెంటిమెంట్ విశ్లేషణ కోసం [`పైప్‌లైన్`] డిఫాల్ట్ [ప్రీట్రైన్డ్ మోడల్](https://huggingface.co/distilbert-base-uncased-finetuned-sst-2-english) మరియు టోకెనైజర్‌ని డౌన్‌లోడ్ చేస్తుంది మరియు కాష్ చేస్తుంది. ఇప్పుడు మీరు మీ లక్ష్య వచనంలో `క్లాసిఫైయర్`ని ఉపయోగించవచ్చు:

```py
>>> classifier("We are very happy to show you the 🤗 Transformers library.")
[{'label': 'POSITIVE', 'score': 0.9998}]
```

మీరు ఒకటి కంటే ఎక్కువ ఇన్‌పుట్‌లను కలిగి ఉంటే, నిఘంటువుల జాబితాను అందించడానికి మీ ఇన్‌పుట్‌లను జాబితాగా [`పైప్‌లైన్`]కి పంపండి:

```py
>>> results = classifier(["We are very happy to show you the 🤗 Transformers library.", "We hope you don't hate it."])
>>> for result in results:
...     print(f"label: {result['label']}, with score: {round(result['score'], 4)}")
label: POSITIVE, with score: 0.9998
label: NEGATIVE, with score: 0.5309
```

[`పైప్‌లైన్`] మీకు నచ్చిన ఏదైనా పని కోసం మొత్తం డేటాసెట్‌ను కూడా పునరావృతం చేయగలదు. ఈ ఉదాహరణ కోసం, స్వయంచాలక ప్రసంగ గుర్తింపును మన పనిగా ఎంచుకుందాం:

```py
>>> import torch
>>> from transformers import pipeline

>>> speech_recognizer = pipeline("automatic-speech-recognition", model="facebook/wav2vec2-base-960h")
```

మీరు మళ్లీ మళ్లీ చెప్పాలనుకుంటున్న ఆడియో డేటాసెట్‌ను లోడ్ చేయండి (మరిన్ని వివరాల కోసం 🤗 డేటాసెట్‌లు [త్వరిత ప్రారంభం](https://huggingface.co/docs/datasets/quickstart#audio) చూడండి. ఉదాహరణకు, [MInDS-14](https://huggingface.co/datasets/PolyAI/minds14) డేటాసెట్‌ను లోడ్ చేయండి:

```py
>>> from datasets import load_dataset, Audio

>>> dataset = load_dataset("PolyAI/minds14", name="en-US", split="train")  # doctest: +IGNORE_RESULT
```

డేటాసెట్ యొక్క నమూనా రేటు నమూనాతో సరిపోలుతుందని మీరు నిర్ధారించుకోవాలి
రేటు [`facebook/wav2vec2-base-960h`](https://huggingface.co/facebook/wav2vec2-base-960h) దీనిపై శిక్షణ పొందింది:

```py
>>> dataset = dataset.cast_column("audio", Audio(sampling_rate=speech_recognizer.feature_extractor.sampling_rate))
```

`"ఆడియో"` కాలమ్‌కి కాల్ చేస్తున్నప్పుడు ఆడియో ఫైల్‌లు స్వయంచాలకంగా లోడ్ చేయబడతాయి మరియు మళ్లీ నమూనా చేయబడతాయి.
మొదటి 4 నమూనాల నుండి ముడి వేవ్‌ఫార్మ్ శ్రేణులను సంగ్రహించి, పైప్‌లైన్‌కు జాబితాగా పాస్ చేయండి:

```py
>>> result = speech_recognizer(dataset[:4]["audio"])
>>> print([d["text"] for d in result])
['I WOULD LIKE TO SET UP A JOINT ACCOUNT WITH MY PARTNER HOW DO I PROCEED WITH DOING THAT', "FONDERING HOW I'D SET UP A JOIN TO HELL T WITH MY WIFE AND WHERE THE AP MIGHT BE", "I I'D LIKE TOY SET UP A JOINT ACCOUNT WITH MY PARTNER I'M NOT SEEING THE OPTION TO DO IT ON THE APSO I CALLED IN TO GET SOME HELP CAN I JUST DO IT OVER THE PHONE WITH YOU AND GIVE YOU THE INFORMATION OR SHOULD I DO IT IN THE AP AN I'M MISSING SOMETHING UQUETTE HAD PREFERRED TO JUST DO IT OVER THE PHONE OF POSSIBLE THINGS", 'HOW DO I FURN A JOINA COUT']
```

ఇన్‌పుట్‌లు పెద్దగా ఉన్న పెద్ద డేటాసెట్‌ల కోసం (స్పీచ్ లేదా విజన్ వంటివి), మెమరీలోని అన్ని ఇన్‌పుట్‌లను లోడ్ చేయడానికి మీరు జాబితాకు బదులుగా జెనరేటర్‌ను పాస్ చేయాలనుకుంటున్నారు. మరింత సమాచారం కోసం [పైప్‌లైన్ API సూచన](./main_classes/pipelines)ని చూడండి.

### పైప్‌లైన్‌లో మరొక మోడల్ మరియు టోకెనైజర్‌ని ఉపయోగించండి

[`పైప్‌లైన్`] [Hub](https://huggingface.co/models) నుండి ఏదైనా మోడల్‌ను కలిగి ఉంటుంది, దీని వలన ఇతర వినియోగ-కేసుల కోసం [`పైప్‌లైన్`]ని సులభంగా స్వీకరించవచ్చు. ఉదాహరణకు, మీరు ఫ్రెంచ్ టెక్స్ట్‌ను హ్యాండిల్ చేయగల మోడల్ కావాలనుకుంటే, తగిన మోడల్ కోసం ఫిల్టర్ చేయడానికి హబ్‌లోని ట్యాగ్‌లను ఉపయోగించండి. అగ్ర ఫిల్టర్ చేసిన ఫలితం మీరు ఫ్రెంచ్ టెక్స్ట్ కోసం ఉపయోగించగల సెంటిమెంట్ విశ్లేషణ కోసం ఫైన్‌ట్యూన్ చేయబడిన బహుభాషా [BERT మోడల్](https://huggingface.co/nlptown/bert-base-multilingual-uncased-sentiment)ని అందిస్తుంది:

```py
>>> model_name = "nlptown/bert-base-multilingual-uncased-sentiment"
```

<frameworkcontent>
<pt> 
ముందుగా శిక్షణ పొందిన మోడల్‌ను లోడ్ చేయడానికి [`AutoModelForSequenceClassification`] మరియు [`AutoTokenizer`]ని ఉపయోగించండి మరియు దాని అనుబంధిత టోకెనైజర్ (తదుపరి విభాగంలో `AutoClass`పై మరిన్ని):

```py
>>> from transformers import AutoTokenizer, AutoModelForSequenceClassification

>>> model = AutoModelForSequenceClassification.from_pretrained(model_name)
>>> tokenizer = AutoTokenizer.from_pretrained(model_name)
```
</pt>
<tf>
ముందుగా శిక్షణ పొందిన మోడల్‌ను లోడ్ చేయడానికి [`TFAutoModelForSequenceClassification`] మరియు [`AutoTokenizer`]ని ఉపయోగించండి మరియు దాని అనుబంధిత టోకెనైజర్ (తదుపరి విభాగంలో `TFAutoClass`పై మరిన్ని):
  
```py
>>> from transformers import AutoTokenizer, TFAutoModelForSequenceClassification

>>> model = TFAutoModelForSequenceClassification.from_pretrained(model_name)
>>> tokenizer = AutoTokenizer.from_pretrained(model_name)
```
</tf>
</frameworkcontent>

[`పైప్‌లైన్`]లో మోడల్ మరియు టోకెనైజర్‌ను పేర్కొనండి మరియు ఇప్పుడు మీరు ఫ్రెంచ్ టెక్స్ట్‌పై `క్లాసిఫైయర్`ని వర్తింపజేయవచ్చు:

```py
>>> classifier = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)
>>> classifier("Nous sommes très heureux de vous présenter la bibliothèque 🤗 Transformers.")
[{'label': '5 stars', 'score': 0.7273}]
```

మీరు మీ వినియోగ-కేస్ కోసం మోడల్‌ను కనుగొనలేకపోతే, మీరు మీ డేటాపై ముందుగా శిక్షణ పొందిన మోడల్‌ను చక్కగా మార్చాలి. ఎలాగో తెలుసుకోవడానికి మా [ఫైన్‌ట్యూనింగ్ ట్యుటోరియల్](./ట్రైనింగ్)ని చూడండి. చివరగా, మీరు మీ ప్రీట్రైన్డ్ మోడల్‌ని ఫైన్‌ట్యూన్ చేసిన తర్వాత, దయచేసి అందరి కోసం మెషిన్ లెర్నింగ్‌ని డెమోక్రటైజ్ చేయడానికి హబ్‌లోని సంఘంతో మోడల్‌ను [షేరింగ్](./model_sharing) పరిగణించండి! 🤗

## AutoClass

<Youtube id="AhChOFRegn4"/>

హుడ్ కింద, మీరు పైన ఉపయోగించిన [`పైప్‌లైన్`]కి శక్తిని అందించడానికి [`AutoModelForSequenceClassification`] మరియు [`AutoTokenizer`] తరగతులు కలిసి పని చేస్తాయి. ఒక [AutoClass](./model_doc/auto) అనేది ముందుగా శిక్షణ పొందిన మోడల్ యొక్క ఆర్కిటెక్చర్‌ను దాని పేరు లేదా మార్గం నుండి స్వయంచాలకంగా తిరిగి పొందే సత్వరమార్గం. మీరు మీ టాస్క్ కోసం తగిన `ఆటోక్లాస్`ని మాత్రమే ఎంచుకోవాలి మరియు ఇది అనుబంధిత ప్రీప్రాసెసింగ్ క్లాస్.

మునుపటి విభాగం నుండి ఉదాహరణకి తిరిగి వెళ్లి, [`పైప్‌లైన్`] ఫలితాలను ప్రతిబింబించడానికి మీరు `ఆటోక్లాస్`ని ఎలా ఉపయోగించవచ్చో చూద్దాం.

### AutoTokenizer

ఒక మోడల్‌కు ఇన్‌పుట్‌లుగా సంఖ్యల శ్రేణిలో వచనాన్ని ప్రీప్రాసెసింగ్ చేయడానికి టోకెనైజర్ బాధ్యత వహిస్తుంది. పదాన్ని ఎలా విభజించాలి మరియు ఏ స్థాయిలో పదాలను విభజించాలి ([tokenizer సారాంశం](./tokenizer_summary)లో టోకనైజేషన్ గురించి మరింత తెలుసుకోండి) సహా టోకనైజేషన్ ప్రక్రియను నియంత్రించే అనేక నియమాలు ఉన్నాయి. గుర్తుంచుకోవలసిన ముఖ్యమైన విషయం ఏమిటంటే, మీరు మోడల్‌కు ముందే శిక్షణ పొందిన అదే టోకనైజేషన్ నియమాలను ఉపయోగిస్తున్నారని నిర్ధారించుకోవడానికి మీరు అదే మోడల్ పేరుతో టోకెనైజర్‌ను తక్షణం చేయాలి.

[`AutoTokenizer`]తో టోకెనైజర్‌ను లోడ్ చేయండి:

```py
>>> from transformers import AutoTokenizer

>>> model_name = "nlptown/bert-base-multilingual-uncased-sentiment"
>>> tokenizer = AutoTokenizer.from_pretrained(model_name)
```

మీ వచనాన్ని టోకెనైజర్‌కు పంపండి:

```py
>>> encoding = tokenizer("We are very happy to show you the 🤗 Transformers library.")
>>> print(encoding)
{'input_ids': [101, 11312, 10320, 12495, 19308, 10114, 11391, 10855, 10103, 100, 58263, 13299, 119, 102],
 'token_type_ids': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
 'attention_mask': [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]}
```

టోకెనైజర్ వీటిని కలిగి ఉన్న నిఘంటువుని అందిస్తుంది:

* [input_ids](./glossary#input-ids): మీ టోకెన్‌ల సంఖ్యాపరమైన ప్రాతినిధ్యం.
* [అటెన్షన్_మాస్క్](.గ్లోసరీ#అటెన్షన్-మాస్క్): ఏ టోకెన్‌లకు హాజరు కావాలో సూచిస్తుంది.

ఒక టోకెనైజర్ ఇన్‌పుట్‌ల జాబితాను కూడా ఆమోదించగలదు మరియు ఏకరీతి పొడవుతో బ్యాచ్‌ను తిరిగి ఇవ్వడానికి టెక్స్ట్‌ను ప్యాడ్ చేసి కత్తిరించవచ్చు:

<frameworkcontent>
<pt>

```py
>>> pt_batch = tokenizer(
...     ["We are very happy to show you the 🤗 Transformers library.", "We hope you don't hate it."],
...     padding=True,
...     truncation=True,
...     max_length=512,
...     return_tensors="pt",
... )
```
</pt>
<tf>

```py
>>> tf_batch = tokenizer(
...     ["We are very happy to show you the 🤗 Transformers library.", "We hope you don't hate it."],
...     padding=True,
...     truncation=True,
...     max_length=512,
...     return_tensors="tf",
... )
```
</tf>
</frameworkcontent>

<Tip>

టోకనైజేషన్ గురించి మరిన్ని వివరాల కోసం [ప్రీప్రాసెస్](./ప్రీప్రాసెసింగ్) ట్యుటోరియల్‌ని చూడండి మరియు ఇమేజ్, ఆడియో మరియు మల్టీమోడల్ ఇన్‌పుట్‌లను ప్రీప్రాసెస్ చేయడానికి [`ఆటోఇమేజ్‌ప్రాసెసర్`], [`ఆటోఫీచర్ ఎక్స్‌ట్రాక్టర్` మరియు [`ఆటోప్రాసెసర్`] ఎలా ఉపయోగించాలి.

</Tip>

### AutoModel

<frameworkcontent>
<pt>
🤗 ట్రాన్స్‌ఫార్మర్లు ప్రీట్రైన్డ్ ఇన్‌స్టాన్స్‌లను లోడ్ చేయడానికి సులభమైన మరియు ఏకీకృత మార్గాన్ని అందిస్తాయి. దీని అర్థం మీరు [`ఆటోటోకనైజర్`]ని లోడ్ చేసినట్లుగా [`ఆటోమోడల్`]ని లోడ్ చేయవచ్చు. టాస్క్ కోసం సరైన [`ఆటోమోడల్`]ని ఎంచుకోవడం మాత్రమే తేడా. టెక్స్ట్ (లేదా సీక్వెన్స్) వర్గీకరణ కోసం, మీరు [`AutoModelForSequenceClassification`]ని లోడ్ చేయాలి:


```py
>>> from transformers import AutoModelForSequenceClassification

>>> model_name = "nlptown/bert-base-multilingual-uncased-sentiment"
>>> pt_model = AutoModelForSequenceClassification.from_pretrained(model_name)
```

<Tip>

[`AutoModel`] క్లాస్ ద్వారా సపోర్ట్ చేసే టాస్క్‌ల కోసం [టాస్క్ సారాంశం](./task_summary)ని చూడండి.

</Tip>

ఇప్పుడు మీ ప్రీప్రాసెస్ చేయబడిన బ్యాచ్ ఇన్‌పుట్‌లను నేరుగా మోడల్‌కి పంపండి. మీరు `**`ని జోడించడం ద్వారా నిఘంటువుని అన్‌ప్యాక్ చేయాలి:

```py
>>> pt_outputs = pt_model(**pt_batch)
```

మోడల్ తుది యాక్టివేషన్‌లను `logits` లక్షణంలో అవుట్‌పుట్ చేస్తుంది. సంభావ్యతలను తిరిగి పొందడానికి సాఫ్ట్‌మాక్స్ ఫంక్షన్‌ను `logits` కు వర్తింపజేయండి:


```py
>>> from torch import nn

>>> pt_predictions = nn.functional.softmax(pt_outputs.logits, dim=-1)
>>> print(pt_predictions)
tensor([[0.0021, 0.0018, 0.0115, 0.2121, 0.7725],
        [0.2084, 0.1826, 0.1969, 0.1755, 0.2365]], grad_fn=<SoftmaxBackward0>)
```
