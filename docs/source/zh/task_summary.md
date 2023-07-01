<!--版权所有 2020 年 HuggingFace 团队。保留所有权利。
根据 Apache 许可证，第 2.0 版（“许可证”），您不得在未遵守许可证的情况下使用此文件。您可以在以下位置获取许可证的副本
http://www.apache.org/licenses/LICENSE-2.0
除非适用法律要求或书面同意，根据许可证分发的软件是基于“按原样”提供的，无论是明示的还是暗示的。请参阅许可证以获取特定语言下的权限和限制的详细信息。⚠️ 请注意，此文件是 Markdown 格式的，但包含我们的文档生成器（类似于 MDX）的特定语法，您的 Markdown 查看器可能无法正确渲染。
-->

# 🤗 Transformers 可以做什么


🤗 Transformers 是一个预训练的最先进模型库，用于自然语言处理（NLP）、计算机视觉、音频和语音处理任务。该库不仅包含 Transformer 模型，还包括现代卷积网络等非 Transformer 模型，用于计算机视觉任务。如果您看一下当今最受欢迎的消费产品，比如智能手机、应用程序和电视，很可能其中某种形式的深度学习技术起到了重要的作用。想要从智能手机拍摄的照片中去除背景物体？这是一个全景分割任务的示例（如果您还不知道这是什么意思，我们将在接下来的章节中进行描述！）。

本页面提供了使用 🤗 Transformers 库在只需三行代码的情况下解决不同语音和音频、计算机视觉以及 NLP 任务的概述！



## 音频

音频和语音处理任务与其他模态有些不同，主要是因为音频作为输入是一个连续信号。与文本不同，原始音频波形无法像句子可以被划分为单词那样被整齐地分割。为了解决这个问题，通常会以固定的间隔对原始音频信号进行采样。如果在一个间隔内采样更多的样本，采样率就更高，音频就更接近原始音频源。

以往的方法是对音频进行预处理，从中提取有用的特征。现在更常见的做法是直接将原始音频波形输入到特征编码器中，以提取音频表示。这简化了预处理步骤，并允许模型学习最重要的特征。

### 音频分类
音频分类是将音频数据标记为预定义类别的任务。它是一个广泛的类别，有许多具体的应用，其中一些包括：

* 声学场景分类：为音频标记场景标签（"办公室"，"海滩"，"体育场"）* 声学事件检测：为音频标记声音事件标签（"汽车喇叭"，"鲸鱼呼叫"，"玻璃破碎"）
* 标签化：为包含多个声音的音频标记标签（鸟鸣声，会议中的发言人识别）
* 音乐分类：为音乐标记流派标签（"金属"，"嘻哈"，"乡村"）

```py
>>> from transformers import pipeline

>>> classifier = pipeline(task = "audio-classification", model = "superb/hubert-base-superb-er")
>>> preds = classifier("https://huggingface.co/datasets/Narsil/asr_dummy/resolve/main/mlk.flac")
>>> preds = [{"score": round(pred["score"], 4), "label": pred ["label"]} for pred in preds]
>>> preds
[{'score': 0.4532, 'label': 'hap'},
 {'score': 0.3622, 'label': 'sad'},
 {'score': 0.0943, 'label': 'neu'},
 {'score': 0.0903, 'label': 'ang'}]
```

### 自动语音识别

自动语音识别（ASR）将语音转录为文本。由于语音是人类交流的一种自然形式，它是最常见的音频任务之一。如今，ASR 系统嵌入在像扬声器、手机和汽车等“智能”技术产品中。我们可以要求虚拟助手播放音乐、设置提醒并告诉我们天气。

但 Transformer 架构帮助解决的关键挑战之一是低资源语言。通过在大量语音数据上进行预训练，仅在低资源语言中使用一小时标记的语音数据对模型进行微调，仍然可以产生与之前使用 100 倍标记数据训练的 ASR 系统相比的高质量结果。

``` py
>>> from transformers import pipeline

>>> transcriber = pipeline(task = "automatic-speech-recognition", model = "openai/whisper-small")
>>> transcriber("https://huggingface.co/datasets/Narsil/asr_dummy/resolve/main/mlk.flac")
{'text': ' I have a dream that one day this nation will rise up and live out the true meaning of its creed.'}
```

## 计算机视觉

计算机视觉的一个最早成功的任务之一是使用卷积神经网络（CNN）识别邮政编码号码的图像。图像由像素组成，每个像素都有一个数值。这使得将图像表示为像素值矩阵变得容易。像素值的特定组合描述了图像的颜色。

解决计算机视觉任务的两种一般方法是：

1. 使用卷积来从低级特征到高级抽象事物学习图像的层次特征。
2. 将图像分成补丁，并使用 Transformer 逐渐学习每个图像补丁之间的关系以形成图像。与 CNN 偏爱的自下而上方法不同，这有点像从模糊的图像开始，然后逐渐使其变得清晰。

### 图像分类

图像分类将整个图像标记为预定义的类别集。与大多数分类任务一样，图像分类有许多实际应用场景，其中一些包括：
* 医疗保健：标记医学图像以检测疾病或监测患者健康
* 环境：标记卫星图像以监测森林砍伐、指导野生动植物管理或检测野火
* 农业：标记农作物图像以监测植物健康或用于土地利用监测的卫星图像
* 生态学：标记动物或植物物种图像以监测野生动物种群或跟踪濒危物种

``` py
>>> from transformers import pipeline

>>> classifier = pipeline(task = "image-classification")
>>> preds = classifier(
...     "https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/pipeline-cat-chonk.jpeg"
... )
>>> preds = [{"score": round(pred["score"], 4), "label": pred ["label"]} for pred in preds]
>>> print(*preds, sep = "\n")
{'score': 0.4335, 'label': 'lynx, catamount'}
{'score': 0.0348, 'label': 'cougar, puma, catamount, mountain lion, painter, panther, Felis concolor'}
{'score': 0.0324, 'label': 'snow leopard, ounce, Panthera uncia'}
{'score': 0.0239, 'label': 'Egyptian cat'}
{'score': 0.0229, 'label': 'tiger cat'}
```

### 物体检测

与图像分类不同，物体检测可在图像中识别多个对象及其位置（由边界框定义）。物体检测的一些示例应用包括：
* 自动驾驶车辆：检测其他车辆、行人和交通信号等日常交通对象 * 遥感：灾难监测、城市规划和天气预报* 缺陷检测：检测建筑物中的裂缝或结构损伤以及制造缺陷

``` py
>>> from transformers import pipeline

>>> detector = pipeline(task = "object-detection")
>>> preds = detector(
...     "https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/pipeline-cat-chonk.jpeg"
... )
>>> preds = [{"score": round(pred["score"], 4), "label": pred ["label"], "box": pred ["box"]} for pred in preds]
>>> preds
[{'score': 0.9865,
  'label': 'cat',
  'box': {'xmin': 178, 'ymin': 154, 'xmax': 882, 'ymax': 598}}]
```

### 图像分割

图像分割是一个像素级的任务，它将图像中的每个像素分配给一个类别。它与使用边界框标记和预测图像中的对象的对象检测不同，因为分割更加精细。分割可以在像素级别检测对象。图像分割有几种类型：

* 实例分割：除了标记对象的类别外，还标记每个不同实例的对象（"狗-1"，"狗-2"）

* 全景分割：语义分割和实例分割的组合；它为每个像素标记一个语义类别 **和** 每个不同对象的实例

分割任务在自动驾驶车辆中非常有用，可以创建一个像素级别的世界地图，以便它们可以安全地避开行人和其他车辆。在医学影像学中也很有用，任务的更细粒度可以帮助识别异常细胞或器官特征。

图像分割还可以在电子商务中使用，通过虚拟试穿衣服或通过相机在真实世界中叠加对象来创建增强现实体验。

``` py
>>> from transformers import pipeline

>>> segmenter = pipeline(task = "image-segmentation")
>>> preds = segmenter(
...     "https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/pipeline-cat-chonk.jpeg"
... )
>>> preds = [{"score": round(pred["score"], 4), "label": pred ["label"]} for pred in preds]
>>> print(*preds, sep = "\n")
{'score': 0.9879, 'label': 'LABEL_184'}
{'score': 0.9973, 'label': 'snow'}
{'score': 0.9972, 'label': 'cat'}
```

### 深度估计

深度估计预测图像中每个像素与相机的距离。这项计算机视觉任务对于场景理解和重建尤为重要。例如，在自动驾驶汽车中，车辆需要了解行人、交通标志和其他车辆等物体的距离，以避免障碍和碰撞。深度信息还有助于从 2D 图像构建 3D 表示，并可用于创建生物结构或建筑物的高质量 3D 表示。
深度估计有两种方法：

* 立体视觉：通过比较稍微不同角度拍摄的同一图像来估计深度* 单目视觉：通过单张图像估计深度

``` py
>>> from transformers import pipeline

>>> depth_estimator = pipeline(task = "depth-estimation")
>>> preds = depth_estimator(
...     "https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/pipeline-cat-chonk.jpeg"
... )
```

## 自然语言处理

NLP 任务是最常见的任务类型之一，因为对我们来说，文本是一种自然的交流方式。为了使模型能够识别文本，需要对文本进行分词。这意味着将一系列文本划分为单独的单词或子词（标记），然后将这些标记转换为数字。因此，您可以将一系列文本表示为一系列数字，一旦有了一系列数字，就可以将其输入模型以解决各种 NLP 任务！

### 文本分类
与任何其他模态的分类任务一样，文本分类将文本序列（可以是句子级别、段落或文档）标记为预定义的类别集合。文本分类有许多实际应用，其中一些包括：

* 情感分析：根据某种极性（如“积极”或“消极”）标记文本，可在政治、金融和市场营销等领域支持决策
* 内容分类：根据某个主题标记文本，以帮助组织和过滤新闻和社交媒体信息（“天气”、“体育”、“金融”等）

``` py
>>> from transformers import pipeline

>>> classifier = pipeline(task = "sentiment-analysis")
>>> preds = classifier("Hugging Face is the best thing since sliced bread!")
>>> preds = [{"score": round(pred["score"], 4), "label": pred ["label"]} for pred in preds]
>>> preds
[{'score': 0.9991, 'label': 'POSITIVE'}]
```

### 标记分类

在任何 NLP 任务中，文本都会经过预处理，将文本序列分隔为单个单词或子词。

这些被称为 [token](/glossary#token)。标记分类为每个标记分配来自预定义的类别集合的标签。

标记分类的两种常见类型是：

* 命名实体识别（NER）：根据实体类别（如组织、人员、地点或日期）标记标记。NER 在生物医学环境中特别流行，可以标记基因、蛋白质和药物名称。* 词性标注（POS）：根据其词性（名词、动词或形容词）标记标记。POS 用于帮助翻译系统理解两个相同单词在语法上的区别（作为名词的银行与作为动词的银行）。

``` py
>>> from transformers import pipeline

>>> classifier = pipeline(task = "ner")
>>> preds = classifier("Hugging Face is a French company based in New York City.")
>>> preds = [
...     {
...         "entity": pred ["entity"],
...         "score": round(pred ["score"], 4),
...         "index": pred ["index"],
...         "word": pred ["word"],
...         "start": pred ["start"],
...         "end": pred ["end"],
...     }
...     for pred in preds
... ]
>>> print(*preds, sep = "\n")
{'entity': 'I-ORG', 'score': 0.9968, 'index': 1, 'word': 'Hu', 'start': 0, 'end': 2}
{'entity': 'I-ORG', 'score': 0.9293, 'index': 2, 'word': '##gging', 'start': 2, 'end': 7}
{'entity': 'I-ORG', 'score': 0.9763, 'index': 3, 'word': 'Face', 'start': 8, 'end': 12}
{'entity': 'I-MISC', 'score': 0.9983, 'index': 6, 'word': 'French', 'start': 18, 'end': 24}
{'entity': 'I-LOC', 'score': 0.999, 'index': 10, 'word': 'New', 'start': 42, 'end': 45}
{'entity': 'I-LOC', 'score': 0.9987, 'index': 11, 'word': 'York', 'start': 46, 'end': 50}
{'entity': 'I-LOC', 'score': 0.9992, 'index': 12, 'word': 'City', 'start': 51, 'end': 55}
```

### 问答

问答是另一种基于标记的任务，它回答问题，有时提供上下文（开放域），有时没有上下文（封闭域）。当我们向虚拟助手提问餐厅是否营业时，就会发生这个任务。它还可以提供客户或技术支持，并帮助搜索引擎检索您所要求的相关信息。

问答有两种常见类型：

* 抽取式：给定一个问题和一些上下文，答案是模型从上下文中提取的一段文本

* 抽象式：给定一个问题和一些上下文，答案是从上下文中生成的；此方法由 [`Text2TextGenerationPipeline`] 处理，而不是下面显示的 [`QuestionAnsweringPipeline`]


``` py
>>> from transformers import pipeline

>>> question_answerer = pipeline(task = "question-answering")
>>> preds = question_answerer(
...     question = "What is the name of the repository?",
...     context = "The name of the repository is huggingface/transformers",
... )
>>> print(
...     f "score: {round(preds ['score'], 4)}, start: {preds ['start']}, end: {preds ['end']}, answer: {preds ['answer']}"
... )
score: 0.9327, start: 30, end: 54, answer: huggingface/transformers
```

### 摘要

摘要从较长的文本中创建一个较短的版本，同时尽量保留原始文档的大部分含义。摘要是一个序列到序列的任务；它输出一个比输入更短的文本序列。有许多长篇文档可以摘要，以帮助读者快速了解主要要点。立法法案、法律和金融文件、专利和科学论文是可以进行摘要的一些例子，以节省读者的时间并作为阅读辅助工具。

与问答类似，摘要有两种类型：
* 抽取式：从原始文本中识别并提取最重要的句子
* 抽象式：从原始文本生成目标摘要（可能包含输入文档中没有的新词）；[`SummarizationPipeline`] 使用抽象方法

``` py
>>> from transformers import pipeline

>>> summarizer = pipeline(task = "summarization")
>>> summarizer(
...     "In this work, we presented the Transformer, the first sequence transduction model based entirely on attention, replacing the recurrent layers most commonly used in encoder-decoder architectures with multi-headed self-attention. For translation tasks, the Transformer can be trained significantly faster than architectures based on recurrent or convolutional layers. On both WMT 2014 English-to-German and WMT 2014 English-to-French translation tasks, we achieve a new state of the art. In the former task our best model outperforms even all previously reported ensembles."
... )
[{'summary_text': ' The Transformer is the first sequence transduction model based entirely on attention . It replaces the recurrent layers most commonly used in encoder-decoder architectures with multi-headed self-attention . For translation tasks, the Transformer can be trained significantly faster than architectures based on recurrent or convolutional layers .'}]
```

### 翻译

翻译将一种语言的文本序列转换为另一种语言。

它在帮助来自不同背景的人们相互交流方面非常重要，可以帮助翻译内容触达更广泛的受众，甚至可以作为学习工具帮助人们学习一门新语言。除了摘要之外，翻译也是一个序列到序列的任务，即模型接收一个输入序列并返回一个目标输出序列。

在早期，翻译模型主要是单语言的，但最近对可以在许多语言对之间进行翻译的多语言模型越来越感兴趣。

``` py
>>> from transformers import pipeline

>>> text = "translate English to French: Hugging Face is a community-based open-source platform for machine learning."
>>> translator = pipeline(task = "translation", model = "t5-small")
>>> translator(text)
[{'translation_text': "Hugging Face est une tribune communautaire de l'apprentissage des machines."}]
```

### 语言建模

语言建模是一种预测文本序列中的单词的任务。它已成为非常流行的 NLP 任务，因为预训练的语言模型可以用于许多其他下游任务的微调。最近，大型语言模型（LLM）引起了很大的关注，它们展示了零或少许样本学习的能力。这意味着模型可以解决其未经明确训练的任务！语言模型可以用于生成流畅而令人信服的文本，但需要小心，因为文本可能不总是准确的。

语言建模有两种类型：

* 因果：模型的目标是预测序列中的下一个标记，未来标记被掩盖
    ```py
    >>> from transformers import pipeline

    >>> prompt = "Hugging Face is a community-based open-source platform for machine learning."
    >>> generator = pipeline(task="text-generation")
    >>> generator(prompt)  # doctest: +SKIP
    ```
* masked：模型的目标是在完全访问序列中的标记时预测被掩盖的标记。
    
    ```py
    >>> text = "Hugging Face is a community-based open-source <mask> for machine learning."
    >>> fill_mask = pipeline(task="fill-mask")
    >>> preds = fill_mask(text, top_k=1)
    >>> preds = [
    ...     {
    ...         "score": round(pred["score"], 4),
    ...         "token": pred["token"],
    ...         "token_str": pred["token_str"],
    ...         "sequence": pred["sequence"],
    ...     }
    ...     for pred in preds
    ... ]
    >>> preds
    [{'score': 0.2236,
      'token': 1761,
      'token_str': ' platform',
      'sequence': 'Hugging Face is a community-based open-source platform for machine learning.'}]
  ```

希望本页面为您提供了关于每种模态任务类型及其实际重要性的更多背景信息。在接下来的 [部分](tasks_explained) 中，您将了解🤗 Transformers 如何解决这些任务。