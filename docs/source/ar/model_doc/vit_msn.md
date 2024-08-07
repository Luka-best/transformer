# ViTMSN

## نظرة عامة

اقتُرح نموذج ViTMSN في الورقة البحثية [Masked Siamese Networks for Label-Efficient Learning](https://arxiv.org/abs/2204.07141) من قبل محمود عسران، وماثيلد كارون، وإيشان ميسرا، وبيوتر بوجانوفسكي، وفلوريان بورديس، وباسكال فينسنت، وأرماند جولين، ومايكل رابات، ونيكولاس بالاس. تعرض الورقة تصميمًا معماريًا للتعلم المشترك لتمثيل النماذج الأولية للرقعات المقنعة ومطابقتها مع الرقعات غير المقنعة. وبفضل هذا الإعداد، يحقق أسلوبهم أداءً ممتازًا في أنظمة التصوير منخفضة وقليلة للغاية.

ملخص الورقة البحثية هو كما يلي:

*نحن نقترح شبكات Siamese المقنعة (MSN)، وهو إطار عمل للتعلم الذاتي للإشراف لتعلم تمثيلات الصور. يقارن نهجنا تمثيل عرض صورة تحتوي على رقعات مقنعة عشوائيًا بتمثيل الصورة الأصلية غير المقنعة. تعد استراتيجية التعلم المسبق ذاتي الإشراف هذه قابلة للتطوير بشكل خاص عند تطبيقها على محولات الرؤية حيث تقوم الشبكة بمعالجة الرقعات غير المقنعة فقط. ونتيجة لذلك، تحسن شبكات MSN قابلية توسع تصميمات التعلم المشترك، مع إنتاج تمثيلات ذات مستوى دلالي عالٍ تتنافس بشكل فعال في تصنيف الصور منخفضة التصوير. على سبيل المثال، في ImageNet-1K، باستخدام 5000 صورة فقط، يحقق نموذج MSN الأساسي لدينا دقة 72.4٪، وباستخدام 1٪ من ملصقات ImageNet-1K، نحقق دقة 75.7٪، مما يحدد حالة جديدة من الفن للتعلم الذاتي للإشراف على هذا المعيار.*

<img src="https://i.ibb.co/W6PQMdC/Screenshot-2022-09-13-at-9-08-40-AM.png" alt="drawing" width="600"/>

<small> تصميم MSN. مأخوذة من <a href="https://arxiv.org/abs/2204.07141">الورقة البحثية الأصلية.</a> </small>

ساهم بهذا النموذج [sayakpaul](https://huggingface.co/sayakpaul). يمكن العثور على الكود الأصلي [هنا](https://github.com/facebookresearch/msn).

## نصائح الاستخدام

- MSN (شبكات Siamese المقنعة) هي طريقة للتعلم المسبق ذاتي الإشراف لمحولات الرؤية (ViTs). يتمثل الهدف من التعلم المسبق في مطابقة النماذج الأولية المخصصة لطرق عرض الصور غير المقنعة مع طرق عرض الصور المقنعة لنفس الصور.

- أصدر المؤلفون فقط الأوزان المُدربة مسبقًا للعمود الفقري (التدريب المسبق على ImageNet-1k). لذلك، لاستخدام ذلك في مجموعة بيانات تصنيف الصور الخاصة بك، استخدم فئة [`ViTMSNForImageClassification`] التي يتم تهيئتها من [`ViTMSNModel`]. اتبع [دفتر الملاحظات](https://github.com/huggingface/notebooks/blob/main/examples/image_classification.ipynb) هذا للحصول على تعليمات مفصلة حول الضبط الدقيق.

- تعد MSN مفيدة بشكل خاص في أنظمة التصوير منخفضة وقليلة للغاية. على وجه الخصوص، يحقق دقة 75.7٪ مع 1٪ فقط من ملصقات ImageNet-1K عند ضبطها الدقيق.

### استخدام Scaled Dot Product Attention (SDPA)

تتضمن PyTorch مشغل اهتمام النقاط المحددة المحدد كجزء من `torch.nn.functional`. تشمل هذه الوظيفة عدة تطبيقات يمكن تطبيقها اعتمادًا على المدخلات والأجهزة المستخدمة. راجع [الوثائق الرسمية](https://pytorch.org/docs/stable/generated/torch.nn.functional.scaled_dot_product_attention.html) أو صفحة [GPU Inference](https://huggingface.co/docs/transformers/main/en/perf_infer_gpu_one#pytorch-scaled-dot-product-attention) لمزيد من المعلومات.

يتم استخدام SDPA بشكل افتراضي لـ `torch>=2.1.1` عند توفر التنفيذ، ولكن يمكنك أيضًا تعيين `attn_implementation="sdpa"` في `from_pretrained()` لطلب استخدام SDPA بشكل صريح.

```py
from transformers import ViTMSNForImageClassification
model = ViTMSNForImageClassification.from_pretrained("facebook/vit-msn-base", attn_implementation="sdpa", torch_dtype=torch.float16)
...
```

للحصول على أفضل التحسينات، نوصي بتحميل النموذج بنصف الدقة (على سبيل المثال `torch.float16` أو `torch.bfloat16`).

في معيار محلي (A100-40GB، PyTorch 2.3.0، نظام التشغيل Ubuntu 22.04) مع `float32` ونموذج `facebook/vit-msn-base`، رأينا التحسينات التالية أثناء الاستدلال.

| حجم الدفعة | متوسط وقت الاستدلال (مللي ثانية)، وضع Eager | متوسط وقت الاستدلال (مللي ثانية)، نموذج SDPA | تسريع، SDPA / Eager (x) |
|--------------|-------------------------------------------|-------------------------------------------|------------------------------|
| 1 | 7 | 6 | 1.17 |
| 2 | 8 | 6 | 1.33 |
| 4 | 8 | 6 | 1.33 |
| 8 | 8 | 6 | 1.33 |

## الموارد

قائمة بموارد Hugging Face الرسمية وموارد المجتمع (المشار إليها بـ 🌎) لمساعدتك في البدء في استخدام ViT MSN.

<PipelineTag pipeline="image-classification"/>

- مدعوم [`ViTMSNForImageClassification`] بواسطة [نص البرنامج النصي](https://github.com/huggingface/transformers/tree/main/examples/pytorch/image-classification) و [دفتر الملاحظات](https://colab.research.google.com/github/huggingface/notebooks/blob/main/examples/image_classification.ipynb) هذا.

- راجع أيضًا: [دليل مهام تصنيف الصور](../tasks/image_classification)

إذا كنت مهتمًا بتقديم مورد لإدراجه هنا، فالرجاء فتح طلب سحب وسنراجعه! يجب أن يوضح المورد بشكل مثالي شيئًا جديدًا بدلاً من تكرار مورد موجود.

## ViTMSNConfig

[[autodoc]] ViTMSNConfig

## ViTMSNModel

[[autodoc]] ViTMSNModel

- forward

## ViTMSNForImageClassification

[[autodoc]] ViTMSNForImageClassification

- forward