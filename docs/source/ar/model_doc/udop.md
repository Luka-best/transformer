# UDOP

## نظرة عامة
تم اقتراح نموذج UDOP في [توحيد الرؤية والنص والتخطيط لمعالجة المستندات الشاملة](https://arxiv.org/abs/2212.02623) بواسطة Zineng Tang, Ziyi Yang, Guoxin Wang, Yuwei Fang, Yang Liu, Chenguang Zhu, Michael Zeng, Cha Zhang, Mohit Bansal.

يعتمد UDOP على بنية Transformer الترميزية فك الترميز المستندة إلى [T5](t5) لمهام الذكاء الاصطناعي للمستندات مثل تصنيف صور المستندات، وتحليل المستندات، والأسئلة والأجوبة البصرية للمستندات.

ملخص الورقة هو ما يلي:

نقترح معالجة المستندات الشاملة (UDOP)، وهي نموذج Document AI أساسي يوحد أوضاع النص والصورة والتخطيط معًا بتنسيقات مهام متنوعة، بما في ذلك فهم المستندات وتوليد المستندات. يستفيد UDOP من الارتباط المكاني بين المحتوى النصي وصورة المستند لنمذجة أوضاع الصورة والنص والتخطيط باستخدام تمثيل موحد. باستخدام محول Vision-Text-Layout المبتكر، يوحد UDOP بين المعالجة المسبقة ومهام المجال المتعدد لأسفل البنية المستندة إلى التسلسل. يتم المعالجة المسبقة لـ UDOP على كل من مجموعات البيانات الوثائقية واسعة النطاق غير الموسومة باستخدام أهداف ذاتية الإشراف مبتكرة وبيانات موسومة متنوعة. يتعلم UDOP أيضًا إنشاء صور المستندات من أوضاع النص والتخطيط عبر إعادة بناء الصورة المقنعة. على حد علمنا، هذه هي المرة الأولى في مجال الذكاء الاصطناعي للمستندات التي يحقق فيها نموذج واحد في نفس الوقت تحرير المستندات العصبية وتخصيص المحتوى بجودة عالية. تحدد طريقتنا الحالة الراهنة لـ 9 مهام AI للمستندات، على سبيل المثال فهم المستندات والأسئلة والأجوبة، عبر مجالات البيانات المتنوعة مثل تقارير التمويل والأوراق الأكاديمية والمواقع الإلكترونية. يحتل UDOP المرتبة الأولى في لوحة القيادة الخاصة بمعيار فهم المستندات (DUE).

<img src="https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/transformers/model_doc/udop_architecture.jpg" alt="drawing" width="600"/>

<small> هندسة UDOP. مأخوذة من <a href="https://arxiv.org/abs/2212.02623">الورقة الأصلية.</a> </small>

## نصائح الاستخدام

- بالإضافة إلى *input_ids*، يتوقع [`UdopForConditionalGeneration`] أيضًا إدخال `bbox`، وهو عبارة عن صناديق حدود (أي مواضع ثنائية الأبعاد) للرموز المميزة للإدخال. يمكن الحصول على هذه باستخدام محرك OCR خارجي مثل [Tesseract](https://github.com/tesseract-ocr/tesseract) من Google (يتوفر [غلاف Python](https://pypi.org/project/pytesseract/)). يجب أن يكون كل صندوق حد في تنسيق (x0، y0، x1، y1)، حيث يتوافق (x0، y0) مع موضع الركن العلوي الأيسر في صندوق الحد، ويمثل (x1، y1) موضع الركن السفلي الأيمن. لاحظ أنه يجب عليك أولاً تطبيع صناديق الحدود لتكون على مقياس 0-1000. لتطبيع، يمكنك استخدام الدالة التالية:

```python
def normalize_bbox(bbox, width, height):
    return [
    int(1000 * (bbox[0] / width)),
    int(1000 * (bbox[1] / height)),
    int(1000 * (bbox[2] / width)),
    int(1000 * (bbox[3] / height)),
    ]
```

هنا، `width` و`height` يقابلان عرض وارتفاع المستند الأصلي الذي يحدث فيه الرمز المميز. يمكن الحصول على تلك باستخدام مكتبة Python Image Library (PIL)، على سبيل المثال، كما يلي:

```python
from PIL import Image

# يمكن أن تكون الوثيقة png أو jpg، إلخ. يجب تحويل ملفات PDF إلى صور.
image = Image.open(name_of_your_document).convert("RGB")

width, height = image.size
```

يمكنك استخدام [`UdopProcessor`] لتحضير الصور والنص للنموذج، والذي يتولى كل ذلك. بشكل افتراضي، تستخدم هذه الفئة محرك Tesseract لاستخراج قائمة بالكلمات والصناديق (الإحداثيات) من مستند معين. وظيفتها مكافئة لتلك الموجودة في [`LayoutLMv3Processor`]، وبالتالي فهي تدعم تمرير إما `apply_ocr=False` في حالة تفضيلك لاستخدام محرك OCR الخاص بك أو `apply_ocr=true` في حالة رغبتك في استخدام محرك OCR الافتراضي. راجع دليل الاستخدام لـ [LayoutLMv2](layoutlmv2#usage-layoutlmv2processor) فيما يتعلق بجميع حالات الاستخدام الممكنة (تكون وظيفة `UdopProcessor` متطابقة).

- إذا كنت تستخدم محرك OCR الخاص بك، فإن إحدى التوصيات هي واجهة برمجة تطبيقات القراءة من Azure [Read API](https://learn.microsoft.com/en-us/azure/ai-services/computer-vision/how-to/call-read-api)، والتي تدعم ما يسمى بقطاعات الخطوط. يؤدي استخدام تضمينات موضع القطاع عادةً إلى أداء أفضل.
- أثناء الاستدلال، يوصى باستخدام طريقة `generate` لتوليد النص تلقائيًا بالنظر إلى صورة المستند.
- تم المعالجة المسبقة للنموذج لكل من الأهداف الخاضعة للإشراف الذاتي. يمكنك استخدام بادئات المهام المختلفة (المطالبات) المستخدمة أثناء المعالجة المسبقة لاختبار القدرات الجاهزة للاستخدام. على سبيل المثال، يمكن مطالبة النموذج بـ "الأسئلة والأجوبة. ما هو التاريخ؟"، حيث "الأسئلة والأجوبة." هو بادئة المهمة المستخدمة أثناء المعالجة المسبقة لـ DocVQA. راجع [الورقة](https://arxiv.org/abs/2212.02623) (الجدول 1) لجميع بادئات المهام.
- يمكنك أيضًا ضبط [`UdopEncoderModel`]، وهو الجزء الترميز فقط من UDOP، والذي يمكن اعتباره محول ترميز LayoutLMv3. بالنسبة إلى المهام التمييزية، يمكنك ببساطة إضافة مصنف خطي في الأعلى وضبطه على مجموعة بيانات موسومة.

تمت المساهمة بهذا النموذج من قبل [nielsr](https://huggingface.co/nielsr).

يمكن العثور على الكود الأصلي [هنا](https://github.com/microsoft/UDOP).

## الموارد

قائمة بموارد Hugging Face الرسمية وموارد المجتمع (المشار إليها بـ 🌎) لمساعدتك في البدء باستخدام UDOP. إذا كنت مهتمًا بتقديم مورد لإدراجه هنا، فالرجاء فتح طلب سحب وسنقوم بمراجعته! يجب أن يوضح المورد المثالي شيئًا جديدًا بدلاً من تكرار مورد موجود.

- يمكن العثور على دفاتر الملاحظات التوضيحية المتعلقة بـ UDOP [هنا](https://github.com/NielsRogge/Transformers-Tutorials/tree/master/UDOP) والتي توضح كيفية ضبط UDOP على مجموعة بيانات مخصصة بالإضافة إلى الاستدلال. 🌎
- [دليل مهام الأسئلة والأجوبة للمستندات](../tasks/document_question_answering)

## UdopConfig

[[autodoc]] UdopConfig

## UdopTokenizer

[[autodoc]] UdopTokenizer

- build_inputs_with_special_tokens
- get_special_tokens_mask
- create_token_type_ids_from_sequences
- save_vocabulary

## UdopTokenizerFast

[[autodoc]] UdopTokenizerFast

## UdopProcessor

[[autodoc]] UdopProcessor

- __call__

## UdopModel

[[autodoc]] UdopModel

- forward

## UdopForConditionalGeneration

[[autodoc]] UdopForConditionalGeneration

- forward

## UdopEncoderModel

[[autodoc]] UdopEncoderModel

- forward