# LayoutLMV2

## نظرة عامة

اقترح نموذج LayoutLMV2 في "LayoutLMv2: Multi-modal Pre-training for Visually-Rich Document Understanding" بواسطة يانغ شو، وييهينج شو، وتينجتشاو ليو، ولي كوي، وفورو وي، وجووكسين وانج، وييجوان لو، وديناي فلورنسيو، وتشا زهانج، ووانشيانج تشي، ومين زهانج، وليدونج تشو. ويحسن LayoutLMV2 من LayoutLM للحصول على نتائج متقدمة في العديد من معايير فهم صورة المستند:

- استخراج المعلومات من المستندات الممسوحة ضوئيًا: مجموعة بيانات FUNSD (مجموعة من 199 نموذجًا تضم أكثر من 30000 كلمة)، ومجموعة بيانات CORD (مجموعة من 800 إيصال للتدريب، و100 للتحقق، و100 للاختبار)، ومجموعة بيانات SROIE (مجموعة من 626 إيصال للتدريب و347 إيصال للاختبار)، ومجموعة بيانات Kleister-NDA (مجموعة من اتفاقات عدم الإفصاح من قاعدة بيانات EDGAR، بما في ذلك 254 وثيقة للتدريب، و83 وثيقة للتحقق، و203 وثيقة للاختبار).

- تصنيف صورة المستند: مجموعة بيانات RVL-CDIP (مجموعة من 400000 صورة تنتمي إلى واحدة من 16 فئة).

- الأسئلة والأجوبة البصرية للمستند: مجموعة بيانات DocVQA (مجموعة من 50000 سؤال محدد على 12000+ صورة للمستند).

ملخص الورقة هو كما يلي:

* أثبت التدريب المسبق للنص والتخطيط فعاليته في مجموعة متنوعة من مهام فهم المستندات الغنية بصريًا وذلك بفضل تصميم نموذج معماريته المتميز وميزة المستندات الكبيرة غير الموسومة الممسوحة ضوئيًا/الرقمية. وفي هذه الورقة، نقدم LayoutLMv2 من خلال التدريب المسبق للنص والتخطيط والصورة في إطار متعدد الوسائط، حيث يتم الاستفادة من تصميمات معمارية جديدة للنماذج ومهام التدريب المسبق. وعلى وجه التحديد، لا يستخدم LayoutLMv2 مهمة نمذجة اللغة المرئية المقنعة الموجودة فحسب، بل يستخدم أيضًا مهمتي محاذاة النص والصورة ومطابقة النص والصورة الجديدتين في مرحلة التدريب المسبق، حيث يتم تعلم التفاعل متعدد الوسائط بشكل أفضل. وفي الوقت نفسه، فإنه يدمج أيضًا آلية اهتمام ذاتي واعية مكانيًا في تصميم معمارية المحول، بحيث يمكن للنموذج أن يفهم تمامًا العلاقة الموضعية النسبية بين كتل النص المختلفة. وتظهر نتائج التجارب أن LayoutLMv2 يتفوق على الخطوط القاعدية القوية ويحقق نتائج متقدمة جديدة في مجموعة واسعة من مهام فهم المستندات الغنية بصريًا، بما في ذلك FUNSD (0.7895 -> 0.8420)، CORD (0.9493 -> 0.9601)، SROIE (0.9524 -> 0.9781)، Kleister-NDA (0.834 -> 0.852)، RVL-CDIP (0.9443 -> 0.9564)، وDocVQA (0.7295 -> 0.8672). ويُتاح نموذج LayoutLMv2 المدرب مسبقًا للجمهور على هذا الرابط https.*

يعتمد LayoutLMv2 على detectron2 وtorchvision وtesseract. قم بتشغيل ما يلي لتثبيتها:

```bash
python -m pip install 'git+https://github.com/facebookresearch/detectron2.git'
python -m pip install torchvision tesseract
```

(إذا كنت تقوم بالتطوير لـ LayoutLMv2، لاحظ أن اجتياز اختبارات doctests يتطلب أيضًا تثبيت هذه الحزم.)

## نصائح الاستخدام

- الفرق الرئيسي بين LayoutLMv1 وLayoutLMv2 هو أن الأخير يتضمن تضمينًا بصريًا أثناء التدريب المسبق (بينما يضيف LayoutLMv1 تضمينات بصرية فقط أثناء الضبط الدقيق).

- يضيف LayoutLMv2 كلًا من انحياز الاهتمام النسبي أحادي البعد وانحياز الاهتمام المكاني ثنائي البعد إلى درجات الاهتمام في طبقات الاهتمام الذاتي. يمكن العثور على التفاصيل في الصفحة 5 من الورقة.

- يمكن العثور على دفاتر الملاحظات التوضيحية حول كيفية استخدام نموذج LayoutLMv2 على RVL-CDIP وFUNSD وDocVQA وCORD [هنا](https://github.com/NielsRogge/Transformers-Tutorials).

- يستخدم LayoutLMv2 حزمة [Detectron2](https://github.com/facebookresearch/detectron2/) من Facebook AI لعمودها الفقري المرئي. راجع [هذا الرابط](https://detectron2.readthedocs.io/en/latest/tutorials/install.html) للحصول على تعليمات التثبيت.

- بالإضافة إلى `input_ids`، يتوقع [`~LayoutLMv2Model.forward`] إدخالين إضافيين، وهما `image` و`bbox`. ويمثل إدخال `image` صورة المستند الأصلي الذي تظهر فيه رموز النص. ويتوقع النموذج أن تكون كل صورة للمستند بحجم 224x224. وهذا يعني أنه إذا كان لديك دفعة من صور المستندات، فيجب أن يكون `image` عبارة عن مصفوفة من الشكل (batch_size، 3، 224، 224). ويمكن أن يكون هذا إما `torch.Tensor` أو `Detectron2.structures.ImageList`. لا تحتاج إلى تطبيع القنوات، حيث يقوم النموذج بذلك. ومن المهم ملاحظة أن العمود الفقري المرئي يتوقع قنوات BGR بدلاً من RGB، حيث أن جميع النماذج في Detectron2 يتم تدريبها مسبقًا باستخدام تنسيق BGR. وإدخال `bbox` عبارة عن حدود (مواضع ثنائية الأبعاد) لرموز النص المدخلة. وهذا مطابق لـ [`LayoutLMModel`]. ويمكن الحصول عليها باستخدام محرك التعرف الضوئي على الحروف مثل [Tesseract](https://github.com/tesseract-ocr/tesseract) من Google (يوجد [غلاف Python](https://pypi.org/project/pytesseract/) متاح). يجب أن يكون كل حد في تنسيق (x0، y0، x1، y1)، حيث يتوافق (x0، y0) مع موضع الركن العلوي الأيسر في الحد، و(x1، y1) يمثل موضع الركن السفلي الأيمن. لاحظ أنه يجب أولاً تطبيع الحدود لتكون على مقياس 0-1000. لتطبيع، يمكنك استخدام الدالة التالية:

```python
def normalize_bbox(bbox, width, height):
    return [
        int(1000 * (bbox[0] / width)),
        int(1000 * (bbox[1] / height)),
        int(1000 * (bbox[2] / width)),
        int(1000 * (bbox[3] / height)),
    ]
```

هنا، `width` و`height` هما عرض وارتفاع المستند الأصلي الذي يحدث فيه الرمز (قبل تغيير حجم الصورة). ويمكن الحصول عليها باستخدام مكتبة Python Image Library (PIL)، على سبيل المثال، كما يلي:

```python
from PIL import Image

image = Image.open(
    "name_of_your_document - can be a png, jpg, etc. of your documents (PDFs must be converted to images)."
)

width, height = image.size
```

ومع ذلك، يتضمن هذا النموذج معالجًا جديدًا تمامًا [`~transformers.LayoutLMv2Processor`] يمكن استخدامه لإعداد البيانات للنموذج مباشرة (بما في ذلك تطبيق التعرف الضوئي على الحروف تحت الغطاء). يمكن العثور على مزيد من المعلومات في قسم "الاستخدام" أدناه.

- داخليًا، سيرسل [`~transformers.LayoutLMv2Model`] إدخال `image` عبر عموده الفقري المرئي للحصول على خريطة ميزات ذات دقة أقل، يكون شكلها مطابقًا لسمة `image_feature_pool_shape` من [`~transformers.LayoutLMv2Config`]. يتم بعد ذلك تسطيح خريطة الميزات هذه للحصول على تسلسل من رموز الصورة. وبما أن حجم خريطة الميزات هو 7x7 بشكل افتراضي، فإننا نحصل على 49 رمز صورة. يتم بعد ذلك دمج هذه الرموز مع رموز النص، وإرسالها عبر مشفر المحول. وهذا يعني أن الحالات المخفية الأخيرة للنموذج سيكون لها طول 512 + 49 = 561، إذا قمت بضبط رموز النص حتى الطول الأقصى. وبشكل أكثر عمومية، سيكون للحالات المخفية الأخيرة شكل `seq_length` + `image_feature_pool_shape[0]` * `config.image_feature_pool_shape[1]`.

- عند استدعاء [`~transformers.LayoutLMv2Model.from_pretrained`]`]، سيتم طباعة تحذير مع قائمة طويلة من أسماء المعلمات التي لم يتم تهيئتها. وهذا ليس مشكلة، حيث أن هذه المعلمات هي إحصاءات التطبيع بالدفعات، والتي سيكون لها قيم عند الضبط الدقيق على مجموعة بيانات مخصصة.

- إذا كنت تريد تدريب النموذج في بيئة موزعة، فتأكد من استدعاء [`synchronize_batch_norm`] على النموذج من أجل مزامنة طبقات التطبيع بالدفعات للعمود الفقري المرئي بشكل صحيح.

بالإضافة إلى ذلك، هناك LayoutXLM، وهو إصدار متعدد اللغات من LayoutLMv2. يمكن العثور على مزيد من المعلومات على [صفحة توثيق LayoutXLM](layoutxlm).

## الموارد

قائمة بموارد Hugging Face الرسمية وموارد المجتمع (مشار إليها برمز 🌎) لمساعدتك في البدء باستخدام LayoutLMv2. إذا كنت مهتمًا بتقديم مورد لإدراجه هنا، فيرجى فتح طلب سحب Pull Request وسنراجعه! ويجب أن يثبت المورد شيئًا جديدًا بدلاً من تكرار مورد موجود.

<PipelineTag pipeline="text-classification"/>

- دفتر ملاحظات حول كيفية [ضبط نموذج LayoutLMv2 الدقيق لتصنيف النصوص على مجموعة بيانات RVL-CDIP](https://colab.research.google.com/github/NielsRogge/Transformers-Tutorials/blob/master/LayoutLMv2/RVL-CDIP/Fine_tuning_LayoutLMv2ForSequenceClassification_on_RVL_CDIP.ipynb).

- راجع أيضًا: [دليل مهام تصنيف النصوص](../tasks/sequence_classification)

<PipelineTag pipeline="question-answering"/>

- دفتر ملاحظات حول كيفية [ضبط نموذج LayoutLMv2 الدقيق لأسئلة وأجوبة على مجموعة بيانات DocVQA](https://colab.research.google.com/github/NielsRogge/Transformers-Tutorials/blob/master/LayoutLMv2/DocVQA/Fine_tuning_LayoutLMv2ForQuestionAnswering_on_DocVQA.ipynb).

- راجع أيضًا: [دليل مهام الأسئلة والأجوبة](../tasks/question_answering)

- راجع أيضًا: [دليل مهام الأسئلة والأجوبة للمستندات](../tasks/document_question_answering)

<PipelineTag pipeline="token-classification"/>

- دفتر ملاحظات حول كيفية [ضبط نموذج LayoutLMv2 الدقيق لتصنيف الرموز على مجموعة بيانات CORD](https://colab.research.google.com/github/NielsRogge/Transformers-Tutorials/blob/master/LayoutLMv2/CORD/Fine_tuning_LayoutLMv2ForTokenClassification_on_CORD.ipynb).

- دفتر ملاحظات حول كيفية [ضبط نموذج LayoutLMv2 الدقيق لتصنيف الرموز على مجموعة بيانات FUNSD](https://colab.research.google.com/github/NielsRogge/Transformers-Tutorials/blob/master/LayoutLMv2/FUNSD/Fine_tuning_LayoutLMv2ForTokenClassification_on_FUNSD_using_HuggingFace_Trainer.ipynb).

- راجع أيضًا: [دليل مهام تصنيف الرموز](../tasks/token_classification)
## Usage: LayoutLMv2Processor

أسهل طريقة لإعداد البيانات للنموذج هي استخدام [LayoutLMv2Processor]، والذي يجمع داخلياً بين معالج الصور [LayoutLMv2ImageProcessor] ومحلل الرموز [LayoutLMv2Tokenizer] أو [LayoutLMv2TokenizerFast]. ويتولى معالج الصور التعامل مع الصور، بينما يتعامل محلل الرموز مع النص. ويجمع المعالج بين الاثنين، وهو مثالي لنموذج متعدد الوسائط مثل LayoutLMv2. لاحظ أنه يمكنك استخدام كل منهما بشكل منفصل إذا كنت تريد التعامل مع وسيط واحد فقط.

```python
from transformers import LayoutLMv2ImageProcessor, LayoutLMv2TokenizerFast, LayoutLMv2Processor

image_processor = LayoutLMv2ImageProcessor()  # apply_ocr is set to True by default
tokenizer = LayoutLMv2TokenizerFast.from_pretrained("microsoft/layoutlmv2-base-uncased")
processor = LayoutLMv2Processor(image_processor, tokenizer)
```

باختصار، يمكنك تزويد [LayoutLMv2Processor] بصورة المستند (وربما بيانات إضافية)، وسينشئ المدخلات التي يتوقعها النموذج. داخلياً، يستخدم المعالج أولاً [LayoutLMv2ImageProcessor] لتطبيق التعرف الضوئي على الحروف (OCR) على الصورة للحصول على قائمة بالكلمات وحدود الصناديق المعيارية، بالإضافة إلى تغيير حجم الصورة إلى حجم معين للحصول على مدخلات الصورة. ثم يتم تزويد الكلمات وحدود الصناديق المعيارية إلى [LayoutLMv2Tokenizer] أو [LayoutLMv2TokenizerFast]، والذي يحولها إلى رموز على مستوى الرمز `input_ids`، و`attention_mask`، و`token_type_ids`، و`bbox`. ويمكنك أيضًا تزويد المعالج بعلامات الكلمات، والتي يتم تحويلها إلى `labels` على مستوى الرمز.

يستخدم [LayoutLMv2Processor] [PyTesseract](https://pypi.org/project/pytesseract/)، وهو غلاف Python حول محرك التعرف الضوئي على الحروف (OCR) Tesseract من Google، تحت الغطاء. لاحظ أنه يمكنك استخدام محرك التعرف الضوئي على الحروف (OCR) الذي تختاره وتوفير الكلمات وحدود الصناديق بنفسك. يتطلب ذلك تهيئة [LayoutLMv2ImageProcessor] مع `apply_ocr` تعيينها على `False`.

هناك ما مجموعه 5 حالات استخدام يدعمها المعالج. أدناه، نقوم بإدراجها جميعًا. لاحظ أن كل من هذه الحالات الاستخدامية تعمل لكل من المدخلات المجمعة وغير المجمعة (نوضحها لمدخلات غير مجمعة).

**حالة الاستخدام 1: تصنيف صورة المستند (التدريب والاستدلال) + تصنيف الرموز (الاستدلال)، apply_ocr = True**

هذه هي الحالة الأكثر بساطة، والتي سيؤدي فيها المعالج (في الواقع معالج الصور) إلى التعرف الضوئي على الحروف في الصورة للحصول على الكلمات وحدود الصناديق المعيارية.

```python
from transformers import LayoutLMv2Processor
from PIL import Image

processor = LayoutLMv2Processor.from_pretrained("microsoft/layoutlmv2-base-uncased")

image = Image.open(
    "name_of_your_document - can be a png, jpg, etc. of your documents (PDFs must be converted to images)."
).convert("RGB")
encoding = processor(
    image, return_tensors="pt"
)  # يمكنك أيضًا إضافة جميع معلمات محلل الرموز هنا مثل padding أو truncation
print(encoding.keys())
# dict_keys(['input_ids', 'token_type_ids', 'attention_mask', 'bbox', 'image'])
```

**حالة الاستخدام 2: تصنيف صورة المستند (التدريب والاستدلال) + تصنيف الرموز (الاستدلال)، apply_ocr=False**

في حالة الرغبة في إجراء التعرف الضوئي على الحروف بنفسك، يمكنك تهيئة معالج الصور مع `apply_ocr` تعيينها على `False`. في هذه الحالة، يجب عليك توفير الكلمات وحدود الصناديق المقابلة (المعيارية) بنفسك للمعالج.

```python
from transformers import LayoutLMv2Processor
from PIL import Image

processor = LayoutLMv2Processor.from_pretrained("microsoft/layoutlmv2-base-uncased", revision="no_ocr")

image = Image.open(
    "name_of_your_document - can be a png, jpg, etc. of your documents (PDFs must be converted to images)."
).convert("RGB")
words = ["hello", "world"]
boxes = [[1, 2, 3, 4], [5, 6, 7, 8]]  # تأكد من تطبيع حدود الصناديق الخاصة بك
encoding = processor(image, words, boxes=boxes, return_tensors="pt")
print(encoding.keys())
# dict_keys(['input_ids', 'token_type_ids', 'attention_mask', 'bbox', 'image'])
```

**حالة الاستخدام 3: تصنيف الرموز (التدريب)، apply_ocr=False**

بالنسبة لمهام تصنيف الرموز (مثل FUNSD وCORD وSROIE وKleister-NDA)، يمكنك أيضًا توفير علامات الكلمات المقابلة لتدريب النموذج. سيقوم المعالج بعد ذلك بتحويلها إلى `labels` على مستوى الرمز. بشكل افتراضي، سيقوم بتسمية أول كلمة فقط من الكلمة، وتسمية الكلمات المتبقية بـ -100، والتي هي `ignore_index` من PyTorch's CrossEntropyLoss. في حالة الرغبة في تسمية جميع الكلمات في الكلمة، يمكنك تهيئة محلل الرموز مع `only_label_first_subword` تعيينها على `False`.

```python
from transformers import LayoutLMv2Processor
from PIL import Image

processor = LayoutLMv2Processor.from_pretrained("microsoft/layoutlmv2-base-uncased", revision="no_ocr")

image = Image.open(
    "name_of_your_document - can be a png, jpg, etc. of your documents (PDFs must be converted to images)."
).convert("RGB")
words = ["hello", "world"]
boxes = [[1, 2, 3, 4], [5, 6, 7, 8]]  # تأكد من تطبيع حدود الصناديق الخاصة بك
word_labels = [1, 2]
encoding = processor(image, words, boxes=boxes, word_labels=word_labels, return_tensors="pt")
print(encoding.keys())
# dict_keys(['input_ids', 'token_type_ids', 'attention_mask', 'bbox', 'labels', 'image'])
```

**حالة الاستخدام 4: الإجابة على الأسئلة المرئية (الاستدلال)، apply_ocr=True**

بالنسبة لمهام الإجابة على الأسئلة المرئية (مثل DocVQA)، يمكنك تزويد المعالج بسؤال. بشكل افتراضي، سيقوم المعالج بتطبيق التعرف الضوئي على الحروف في الصورة، وإنشاء رموز [CLS] للأسئلة [SEP] للكلمات [SEP].

```python
from transformers import LayoutLMv2Processor
from PIL import Image

processor = LayoutLMv2Processor.from_pretrained("microsoft/layoutlmv2-base-uncased")

image = Image.open(
    "name_of_your_document - can be a png, jpg, etc. of your documents (PDFs must be converted to images)."
).convert("RGB")
question = "What's his name?"
encoding = processor(image, question, return_tensors="pt")
print(encoding.keys())
# dict_keys(['input_ids', 'token_type_ids', 'attention_mask', 'bbox', 'image'])
```

**حالة الاستخدام 5: الإجابة على الأسئلة المرئية (الاستدلال)، apply_ocr=False**

بالنسبة لمهام الإجابة على الأسئلة المرئية (مثل DocVQA)، يمكنك تزويد المعالج بسؤال. إذا كنت تريد إجراء التعرف الضوئي على الحروف بنفسك، يمكنك تزويد المعالج بالكلمات وحدود الصناديق (المعيارية) الخاصة بك.

```python
from transformers import LayoutLMv2Processor
from PIL import Image

processor = LayoutLMv2Processor.from_pretrained("microsoft/layoutlmv2-base-uncased", revision="no_ocr")

image = Image.open(
    "name_of_your_document - can be a png, jpg, etc. of your documents (PDFs must be converted to images)."
).convert("RGB")
question = "What's his name?"
words = ["hello", "world"]
boxes = [[1, 2, 3, 4], [5, 6, 7, 8]]  # تأكد من تطبيع حدود الصناديق الخاصة بك
encoding = processor(image, question, words, boxes=boxes, return_tensors="pt")
print(encoding.keys())
# dict_keys(['input_ids', 'token_type_ids', 'attention_mask', 'bbox', 'image'])
```

## LayoutLMv2Config

[[autodoc]] LayoutLMv2Config

## LayoutLMv2FeatureExtractor

[[autodoc]] LayoutLMv2FeatureExtractor

- __call__

## LayoutLMv2ImageProcessor

[[autodoc]] LayoutLMv2ImageProcessor

- preprocess

## LayoutLMv2Tokenizer

[[autodoc]] LayoutLMv2Tokenizer

- __call__

- save_vocabulary

## LayoutLMv2TokenizerFast

[[autodoc]] LayoutLMv2TokenizerFast

- __call__

## LayoutLMv2Processor

[[autodoc]] LayoutLMv2Processor

- __call__

## LayoutLMv2Model

[[autodoc]] LayoutLMv2Model

- forward

## LayoutLMv2ForSequenceClassification

[[autodoc]] LayoutLMv2ForSequenceClassification

## LayoutLMv2ForTokenClassification

[[autodoc]] LayoutLMv2ForTokenClassification

## LayoutLMv2ForQuestionAnswering

[[autodoc]] LayoutLMv2ForQuestionAnswering