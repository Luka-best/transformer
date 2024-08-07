# Depth Anything

## نظرة عامة

اقتُرح نموذج Depth Anything في ورقة بحثية بعنوان "Depth Anything: Unleashing the Power of Large-Scale Unlabeled Data" من قبل Lihe Yang و Bingyi Kang و Zilong Huang و Xiaogang Xu و Jiashi Feng و Hengshuang Zhao. ويستند Depth Anything على بنية DPT، وقد تم تدريبه على حوالي 62 مليون صورة، وحقق نتائج متقدمة في كل من تقدير العمق النسبي والمطلق.

وفيما يلي الملخص المستخرج من الورقة البحثية:

*يقدم هذا العمل Depth Anything، وهو حل عملي للغاية لتقدير العمق أحادي العين المتين. وبدون السعي إلى وحدات تقنية جديدة، نهدف إلى بناء نموذج أساسي بسيط ولكنه قوي للتعامل مع أي صور في أي ظروف. ولهذه الغاية، نقوم بزيادة حجم مجموعة البيانات من خلال تصميم محرك بيانات لجمع البيانات غير المُعَلَّمة على نطاق واسع (حوالي 62 مليون) ووضع العلامات عليها تلقائيًا، مما يزيد بشكل كبير من تغطية البيانات، وبالتالي تقليل خطأ التعميم. ونحن نبحث استراتيجيتين بسيطتين ولكن فعالتين تجعلان من الواعد زيادة حجم البيانات. أولاً، يتم إنشاء هدف تحسين أكثر تحديًا من خلال الاستفادة من أدوات زيادة البيانات. إنه يجبر النموذج على السعي بنشاط للحصول على معرفة بصرية إضافية واكتساب تمثيلات قوية. ثانيًا، تم تطوير إشراف مساعد لإجبار النموذج على وراثة المعلمات الإحصائية الدلالية الغنية من المشفرات المُدربة مسبقًا. نقوم بتقييم قدراته على نطاق واسع، بما في ذلك ست مجموعات بيانات عامة وصور تم التقاطها بشكل عشوائي. ويظهر قدرة انعمام مثيرة للإعجاب. علاوة على ذلك، من خلال ضبط دقة النموذج باستخدام معلومات العمق المتري من NYUv2 و KITTI، يتم تحديد حالات جديدة من حالات SOTA. كما يؤدي نموذج العمق الأفضل لدينا إلى شبكة تحكم أفضل تعتمد على العمق.*

<img src="https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/transformers/model_doc/depth_anything_overview.jpg" alt="drawing" width="600"/>

<small>نظرة عامة على Depth Anything. مأخوذة من <a href="https://arxiv.org/abs/2401.10891">الورقة البحثية الأصلية</a>.</small>

تمت المساهمة بهذا النموذج من قبل [nielsr](https://huggingface.co/nielsr). يمكن العثور على الكود الأصلي [هنا](https://github.com/LiheYoung/Depth-Anything).

## مثال على الاستخدام

هناك طريقتان رئيسيتان لاستخدام Depth Anything: إما باستخدام واجهة برمجة التطبيقات الخاصة بالخطوط الأنابيب، والتي تُبسِّط جميع التعقيدات لك، أو باستخدام فئة `DepthAnythingForDepthEstimation` بنفسك.

### واجهة برمجة التطبيقات الخاصة بالخطوط الأنابيب

تسمح واجهة برمجة التطبيقات باستخدام النموذج في بضع سطور من الكود:

```python
>>> from transformers import pipeline
>>> from PIL import Image
>>> import requests

>>> # تحميل الأنبوب
>>> pipe = pipeline(task="depth-estimation", model="LiheYoung/depth-anything-small-hf")

>>> # تحميل الصورة
>>> url = 'http://images.cocodataset.org/val2017/000000039769.jpg'
>>> image = Image.open(requests.get(url, stream=True).raw)

>>> # الاستنتاج
>>> depth = pipe(image)["depth"]
```

### استخدام النموذج بنفسك

إذا كنت تريد القيام بالمعالجة المسبقة واللاحقة بنفسك، فهذا هو كيفية القيام بذلك:

```python
>>> from transformers import AutoImageProcessor, AutoModelForDepthEstimation
>>> import torch
>>> import numpy as np
>>> from PIL import Image
>>> import requests

>>> url = "http://images.cocodataset.org/val2017/000000039769.jpg"
>>> image = Image.open(requests.get(url, stream=True).raw)

>>> image_processor = AutoImageProcessor.from_pretrained("LiheYoung/depth-anything-small-hf")
>>> model = AutoModelForDepthEstimation.from_pretrained("LiheYoung/depth-anything-small-hf")

>>> # إعداد الصورة للنموذج
>>> inputs = image_processor(images=image, return_tensors="pt")

>>> with torch.no_grad():
...     outputs = model(**inputs)
...     predicted_depth = outputs.predicted_depth

>>> # الاستيفاء إلى الحجم الأصلي
>>> prediction = torch.nn.functional.interpolate(
...     predicted_depth.unsqueeze(1),
...     size=image.size[::-1],
...     mode="bicubic",
...     align_corners=False,
... )

>>> # تصور التنبؤ
>>> output = prediction.squeeze().cpu().numpy()
>>> formatted = (output * 255 / np.max(output)).astype("uint8")
>>> depth = Image.fromarray(formatted)
```

## الموارد

قائمة بموارد Hugging Face الرسمية وموارد المجتمع (المشار إليها بـ 🌎) لمساعدتك في البدء باستخدام Depth Anything.

- [دليل مهام تقدير العمق أحادي العين](../tasks/depth_estimation)
- يمكن العثور على دفتر ملاحظات يُظهر الاستدلال باستخدام [`DepthAnythingForDepthEstimation`] [هنا](https://github.com/NielsRogge/Transformers-Tutorials/blob/master/Depth%20Anything/Predicting_depth_in_an_image_with_Depth_Anything.ipynb). 🌎

إذا كنت مهتمًا بتقديم مورد لإدراجه هنا، فيرجى فتح طلب سحب وسنراجعه! يجب أن يُظهر المورد في الوضع المثالي شيئًا جديدًا بدلاً من تكرار مورد موجود.

## DepthAnythingConfig

[[autodoc]] DepthAnythingConfig

## DepthAnythingForDepthEstimation

[[autodoc]] DepthAnythingForDepthEstimation

- forward