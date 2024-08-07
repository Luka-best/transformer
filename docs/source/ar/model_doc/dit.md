# DiT

## نظرة عامة

اقترح DiT في [DiT: Self-supervised Pre-training for Document Image Transformer](https://arxiv.org/abs/2203.02378) بواسطة Junlong Li, Yiheng Xu, Tengchao Lv, Lei Cui, Cha Zhang, Furu Wei.

يطبق DiT الهدف الخاضع للإشراف الذاتي لـ [BEiT](https://huggingface.co/docs/models/beit) (BERT pre-training of Image Transformers) على 42 مليون صورة للمستندات، مما يسمح بتحقيق نتائج متقدمة في المهام بما في ذلك:

- تصنيف صورة المستند: مجموعة بيانات [RVL-CDIP](https://www.cs.cmu.edu/~aharley/rvl-cdip/) (مجموعة من 400,000 صورة تنتمي إلى واحدة من 16 فئة).
- تحليل تخطيط المستند: مجموعة بيانات [PubLayNet](https://github.com/ibm-aur-nlp/PubLayNet) (مجموعة من أكثر من 360,000 صورة للمستندات تم إنشاؤها عن طريق التحليل التلقائي لملفات PubMed XML).
- كشف الجدول: مجموعة بيانات [ICDAR 2019 cTDaR](https://github.com/cndplab-founder/ICDAR2019_cTDaR) (مجموعة من 600 صورة تدريب و240 صورة اختبار).

الملخص من الورقة هو كما يلي:

*حققت Image Transformer مؤخرًا تقدمًا كبيرًا في فهم الصور الطبيعية، باستخدام تقنيات التدريب الخاضعة للإشراف (ViT، DeiT، إلخ) أو تقنيات التدريب الخاضعة للإشراف الذاتي (BEiT، MAE، إلخ). في هذه الورقة، نقترح DiT، وهو نموذج تحويل صورة مستند خاضع للإشراف الذاتي باستخدام صور نصية غير موسومة واسعة النطاق لمهام AI الخاصة بالمستندات، وهو أمر أساسي نظرًا لعدم وجود نظراء مشرفين بسبب نقص صور المستندات التي وضع عليها الإنسان علامات. نحن نستفيد من DiT كشبكة أساسية في مجموعة متنوعة من مهام AI الخاصة بالمستندات والقائمة على الرؤية، بما في ذلك تصنيف صورة المستند، وتحليل تخطيط المستند، وكذلك كشف الجدول. وقد أوضحت نتائج التجربة أن نموذج DiT الخاضع للإشراف الذاتي يحقق نتائج جديدة متقدمة في هذه المهام اللاحقة، مثل تصنيف صورة المستند (91.11 → 92.69)، وتحليل تخطيط المستند (91.0 → 94.9) واكتشاف الجدول (94.23 → 96.55).*

<img src="https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/dit_architecture.jpg" alt="drawing" width="600"/>

<small> ملخص النهج. مأخوذ من [الورقة الأصلية](https://arxiv.org/abs/2203.02378). </small>

تمت المساهمة بهذا النموذج بواسطة [nielsr](https://huggingface.co/nielsr). يمكن العثور على الكود الأصلي [هنا](https://github.com/microsoft/unilm/tree/master/dit).

## نصائح الاستخدام

يمكن للمرء استخدام أوزان DiT مباشرة مع واجهة برمجة تطبيقات AutoModel:

```python
from transformers import AutoModel

model = AutoModel.from_pretrained("microsoft/dit-base")
```

سيؤدي هذا إلى تحميل النموذج الذي تم تدريبه مسبقًا على نمذجة الصور المقنعة. لاحظ أن هذا لن يتضمن رأس نمذجة اللغة في الأعلى، والذي يستخدم للتنبؤ بالرموز البصرية.

لإدراج الرأس، يمكنك تحميل الأوزان في نموذج `BeitForMaskedImageModeling`، كما هو موضح أدناه:

```python
from transformers import BeitForMaskedImageModeling

model = BeitForMaskedImageModeling.from_pretrained("microsoft/dit-base")
```

يمكنك أيضًا تحميل نموذج مدرب من [المحور](https://huggingface.co/models?other=dit)، كما هو موضح أدناه:

```python
from transformers import AutoModelForImageClassification

model = AutoModelForImageClassification.from_pretrained("microsoft/dit-base-finetuned-rvlcdip")
```

تم ضبط نقطة التحقق هذه بشكل دقيق على [RVL-CDIP](https://www.cs.cmu.edu/~aharley/rvl-cdip/)، وهو معيار مرجعي مهم لتصنيف صورة المستند.

يمكن العثور على دفتر الملاحظات الذي يوضح الاستدلال لتصنيف صورة المستند [هنا](https://github.com/NielsRogge/Transformers-Tutorials/blob/master/DiT/Inference_with_DiT_(Document_Image_Transformer)_for_document_image_classification.ipynb).

## الموارد

قائمة بموارد Hugging Face الرسمية وموارد المجتمع (المشار إليها بـ 🌎) لمساعدتك في البدء باستخدام DiT.

<PipelineTag pipeline="image-classification"/>

- [`BeitForImageClassification`] مدعوم بواسطة [نص البرنامج النصي](https://github.com/huggingface/transformers/tree/main/examples/pytorch/image-classification) و [دفتر الملاحظات](https://colab.research.google.com/github/huggingface/notebooks/blob/main/examples/image_classification.ipynb) هذا.

إذا كنت مهتمًا بتقديم مورد لإدراجه هنا، فالرجاء فتح طلب سحب وسنقوم بمراجعته! يجب أن يوضح المورد في الوضع المثالي شيئًا جديدًا بدلاً من تكرار مورد موجود.

<Tip>
نظرًا لأن بنية DiT تعادل بنية BEiT، فيمكنك الرجوع إلى [صفحة وثائق BEiT](https://huggingface.co/docs/models/beit) للحصول على جميع النصائح وأمثلة التعليمات البرمجية ومفكرات Jupyter.
</Tip>