# YOLOS

## نظرة عامة

اقترح نموذج YOLOS في ورقة بحثية بعنوان "You Only Look at One Sequence: Rethinking Transformer in Vision through Object Detection" بواسطة Yuxin Fang وآخرون. يستلهم YOLOS فكرته من DETR، ويقترح الاستفادة من محول الرؤية (ViT) البسيط للكشف عن الأجسام. وقد تبين أن محول الترميز فقط بحجم القاعدة يمكن أن يحقق 42 AP على COCO، وهو ما يشبه أداء DETR وأطر العمل الأكثر تعقيدًا مثل Faster R-CNN.

فيما يلي الملخص المستخرج من الورقة البحثية:

*هل يمكن لمحول Transformer أن يؤدي التعرف على المستوى ثنائي الأبعاد للأجسام والمناطق من منظور تسلسل نقي إلى تسلسل مع معرفة قليلة بهيكل الفضاء ثنائي الأبعاد؟ للإجابة على هذا السؤال، نقدم "You Only Look at One Sequence (YOLOS)"، وهي سلسلة من نماذج الكشف عن الأجسام المستندة إلى محول الرؤية الأساسي مع أقل عدد ممكن من التعديلات، وأولويات المناطق، وكذلك الانحيازات الاستقرائية لمهمة الهدف. ووجدنا أن YOLOS الذي تم تدريبه مسبقًا على مجموعة بيانات ImageNet-1k ذات الحجم المتوسط فقط يمكن أن يحقق أداءً تنافسيًا للغاية في معيار COCO الصعب للكشف عن الأجسام، على سبيل المثال، يمكن لـ YOLOS-Base المأخوذ مباشرة من بنية BERT-Base تحقيق 42.0 box AP على COCO val. كما نناقش تأثيرات ومحدوديات مخططات التدريب المسبق الحالية واستراتيجيات توسيع نطاق النموذج لمحول Transformer في الرؤية من خلال YOLOS.*

<img src="https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/yolos_architecture.png" alt="drawing" width="600"/>

<small>هندسة YOLOS. مأخوذة من <a href="https://arxiv.org/abs/2106.00666">الورقة البحثية الأصلية</a>.</small>

تمت المساهمة بهذا النموذج بواسطة [nielsr](https://huggingface.co/nielsr). يمكن العثور على الكود الأصلي [هنا](https://github.com/hustvl/YOLOS).

## استخدام Scaled Dot Product Attention (SDPA)

تتضمن PyTorch مشغل اهتمام المنتج النقطي المميز (SDPA) الأصلي كجزء من `torch.nn.functional`. تشمل هذه الوظيفة عدة تنفيذات يمكن تطبيقها اعتمادًا على المدخلات والأجهزة المستخدمة. راجع [الوثائق الرسمية](https://pytorch.org/docs/stable/generated/torch.nn.functional.scaled_dot_product_attention.html) أو صفحة [GPU Inference](https://huggingface.co/docs/transformers/main/en/perf_infer_gpu_one#pytorch-scaled-dot-product-attention) لمزيد من المعلومات.

يتم استخدام SDPA بشكل افتراضي لـ `torch>=2.1.1` عندما يكون التنفيذ متاحًا، ولكن يمكنك أيضًا تعيين `attn_implementation="sdpa"` في `from_pretrained()` لطلب استخدام SDPA بشكل صريح.

```py
from transformers import AutoModelForObjectDetection
model = AutoModelForObjectDetection.from_pretrained("hustvl/yolos-base", attn_implementation="sdpa", torch_dtype=torch.float16)
...
```

للحصول على أفضل التحسينات في السرعة، نوصي بتحميل النموذج بنصف الدقة (مثل `torch.float16` أو `torch.bfloat16`).

على معيار قياس محلي (A100-40GB، PyTorch 2.3.0، نظام التشغيل Ubuntu 22.04) مع `float32` ونموذج `hustvl/yolos-base`، لاحظنا التحسينات في السرعة التالية أثناء الاستنتاج.

| حجم الدفعة | متوسط وقت الاستنتاج (ميلي ثانية)، وضع Eager | متوسط وقت الاستنتاج (ميلي ثانية)، نموذج SDPA | تسريع، SDPA / Eager (x) |
|--------------|-------------------------------------------|-------------------------------------------|------------------------------|
| 1 | 106 | 76 | 1.39 |
| 2 | 154 | 90 | 1.71 |
| 4 | 222 | 116 | 1.91 |
| 8 | 368 | 168 | 2.19 |

## الموارد

فيما يلي قائمة بموارد Hugging Face الرسمية وموارد المجتمع (مشار إليها بـ 🌎) لمساعدتك في البدء باستخدام YOLOS.

<PipelineTag pipeline="object-detection"/>

- يمكن العثور على جميع دفاتر الملاحظات التوضيحية التي توضح الاستدلال + الضبط الدقيق [`YolosForObjectDetection`] على مجموعة بيانات مخصصة [هنا](https://github.com/NielsRogge/Transformers-Tutorials/tree/master/YOLOS).
- يمكن العثور على النصوص البرمجية للضبط الدقيق [`YolosForObjectDetection`] باستخدام [`Trainer`] أو [Accelerate](https://huggingface.co/docs/accelerate/index) [هنا](https://github.com/huggingface/transformers/tree/main/examples/pytorch/object-detection).
- راجع أيضًا: [دليل مهام الكشف عن الأجسام](../tasks/object_detection)

إذا كنت مهتمًا بتقديم مورد لإدراجه هنا، فيرجى فتح طلب سحب وسنراجعه! يجب أن يوضح المورد بشكل مثالي شيء جديد بدلاً من تكرار مورد موجود.

<Tip>

استخدم [`YolosImageProcessor`] لتحضير الصور (والأهداف الاختيارية) للنموذج. على عكس [DETR](detr)، لا يتطلب YOLOS إنشاء `pixel_mask`.

</Tip>

## YolosConfig

[[autodoc]] YolosConfig

## YolosImageProcessor

[[autodoc]] YolosImageProcessor

- preprocess
- pad
- post_process_object_detection

## YolosFeatureExtractor

[[autodoc]] YolosFeatureExtractor

- __call__
- pad
- post_process_object_detection

## YolosModel

[[autodoc]] YolosModel

- forward

## YolosForObjectDetection

[[autodoc]] YolosForObjectDetection

- forward