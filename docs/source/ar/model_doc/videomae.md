# VideoMAE

## نظرة عامة
تم اقتراح نموذج VideoMAE في [VideoMAE: Masked Autoencoders are Data-Efficient Learners for Self-Supervised Video Pre-Training](https://arxiv.org/abs/2203.12602) بواسطة Zhan Tong وYibing Song وJue Wang وLimin Wang.

يوسع VideoMAE مشفرات السيارات المقنعة (MAE) إلى الفيديو، مدعيًا أداءً متميزًا في العديد من معايير تصنيف الفيديو.

ملخص الورقة هو كما يلي:

*يُعد تدريب المحولات الفيديو المسبق على مجموعات بيانات كبيرة للغاية أمرًا مطلوبًا بشكل عام لتحقيق أداء متميز على مجموعات البيانات الصغيرة نسبيًا. في هذه الورقة، نُظهر أن مشفرات الفيديو المقنعة (VideoMAE) هي متعلمات فعالة للبيانات للتمثيل المسبق للفيديو ذاتي الإشراف (SSVP). نستلهم من ImageMAE الذي تم طرحه مؤخرًا ونقترح تصميمات مخصصة لإخفاء أنبوب الفيديو وإعادة بنائه. اتضح أن هذه التصميمات البسيطة فعالة في التغلب على تسرب المعلومات الناجم عن الارتباط الزمني أثناء إعادة بناء الفيديو. توصلنا إلى ثلاثة نتائج مهمة حول SSVP: (1) لا يزال معدل الإخفاء المرتفع للغاية (أي 90% إلى 95%) يحقق أداءً جيدًا لنموذج VideoMAE. يسمح محتوى الفيديو المتكرر زمنيًا بنسبة إخفاء أعلى من تلك المستخدمة في الصور. (2) يحقق VideoMAE نتائج رائعة في مجموعات بيانات صغيرة جدًا (أي حوالي 3000-4000 فيديو) دون استخدام أي بيانات إضافية. ويرجع ذلك جزئيًا إلى مهمة إعادة بناء الفيديو الصعبة لفرض تعلم البنية عالية المستوى. (3) يُظهر VideoMAE أن جودة البيانات أكثر أهمية من كمية البيانات لـ SSVP. يعد التحول في المجال بين مجموعات بيانات التدريب المسبق والمجموعات المستهدفة من القضايا المهمة في SSVP. ومن الجدير بالذكر أن نموذج VideoMAE الخاص بنا مع العمود الفقري ViT الأساسي يمكن أن يحقق 83.9% على Kinects-400 و75.3% على Something-Something V2 و90.8% على UCF101 و61.1% على HMDB51 دون استخدام أي بيانات إضافية.*

<img src="https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/transformers/model_doc/videomae_architecture.jpeg"
alt="drawing" width="600"/>

<small>التدريب المسبق لـ VideoMAE. مأخوذة من <a href="https://arxiv.org/abs/2203.12602">الورقة الأصلية</a>.</small>

تمت المساهمة بهذا النموذج بواسطة [nielsr](https://huggingface.co/nielsr).
يمكن العثور على الكود الأصلي [هنا](https://github.com/MCG-NJU/VideoMAE).

## استخدام Scaled Dot Product Attention (SDPA)
تتضمن PyTorch مشغل اهتمام المنتج النقطي المميز (SDPA) الأصلي كجزء من `torch.nn.functional`. تشمل هذه الوظيفة عدة تطبيقات يمكن تطبيقها اعتمادًا على المدخلات والأجهزة المستخدمة. راجع [الوثائق الرسمية](https://pytorch.org/docs/stable/generated/torch.nn.functional.scaled_dot_product_attention.html)
أو صفحة [GPU Inference](https://huggingface.co/docs/transformers/main/en/perf_infer_gpu_one#pytorch-scaled-dot-product-attention)
لمزيد من المعلومات.

يتم استخدام SDPA بشكل افتراضي لـ `torch>=2.1.1` عند توفر التطبيق، ولكن يمكنك أيضًا تعيين
`attn_implementation="sdpa"` في `from_pretrained()` لطلب استخدام SDPA بشكل صريح.

```py
from transformers import VideoMAEForVideoClassification
model = VideoMAEForVideoClassification.from_pretrained("MCG-NJU/videomae-base-finetuned-kinetics", attn_implementation="sdpa", torch_dtype=torch.float16)
...
```

للحصول على أفضل التحسينات، نوصي بتحميل النموذج بنصف الدقة (على سبيل المثال `torch.float16` أو `torch.bfloat16`).

على معيار محلي (A100-40GB، PyTorch 2.3.0، نظام التشغيل Ubuntu 22.04) مع `float32` ونموذج `MCG-NJU/videomae-base-finetuned-kinetics`، رأينا التحسينات التالية أثناء الاستدلال.

| حجم الدفعة | متوسط وقت الاستدلال (مللي ثانية)، وضع Eager | متوسط وقت الاستدلال (مللي ثانية)، نموذج SDPA | تسريع، SDPA / Eager (x) |
|--------------|-------------------------------------------|-------------------------------------------|------------------------------|
| 1 | 37 | 10 | 3.7 |
| 2 | 24 | 18 | 1.33 |
| 4 | 43 | 32 | 1.34 |
| 8 | 84 | 60 | 1.4 |

## الموارد
فيما يلي قائمة بموارد Hugging Face الرسمية وموارد المجتمع (مشار إليها بـ 🌎) لمساعدتك في البدء باستخدام VideoMAE. إذا
كنت مهتمًا بتقديم مورد لإدراجه هنا، فالرجاء فتح طلب سحب Pull Request وسنراجعه! يجب أن يُظهر المورد بشكل مثالي شيئًا جديدًا بدلاً من تكرار مورد موجود.

**تصنيف الفيديو**
- [دفتر ملاحظات](https://github.com/huggingface/notebooks/blob/main/examples/video_classification.ipynb) يُظهر كيفية
ضبط نموذج VideoMAE على مجموعة بيانات مخصصة.
- [دليل مهمة تصنيف الفيديو](../tasks/video_classification)
- [مساحة 🤗](https://huggingface.co/spaces/sayakpaul/video-classification-ucf101-subset) تُظهر كيفية إجراء الاستدلال باستخدام نموذج تصنيف الفيديو.

## VideoMAEConfig
[[autodoc]] VideoMAEConfig

## VideoMAEFeatureExtractor

[[autodoc]] VideoMAEFeatureExtractor
- __call__

## VideoMAEImageProcessor

[[autodoc]] VideoMAEImageProcessor
- preprocess

## VideoMAEModel

[[autodoc]] VideoMAEModel
- forward

## VideoMAEForPreTraining

يتضمن `VideoMAEForPreTraining` فك التشفير في الأعلى للتدريب المسبق ذاتي الإشراف.

[[autodoc]] transformers.VideoMAEForPreTraining
- forward

## VideoMAEForVideoClassification

[[autodoc]] transformers.VideoMAEForVideoClassification
- forward