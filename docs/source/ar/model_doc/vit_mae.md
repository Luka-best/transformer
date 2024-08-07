# ViTMAE

## نظرة عامة

اقترح نموذج ViTMAE في [Masked Autoencoders Are Scalable Vision Learners](https://arxiv.org/abs/2111.06377v2) بواسطة Kaiming He وآخرون. توضح الورقة أنه من خلال التدريب المسبق لـ Vision Transformer (ViT) لإعادة بناء قيم البكسل للرقع المُقنعة، يمكن الحصول على نتائج بعد الضبط الدقيق تتفوق على التدريب المُشرف.

الملخص من الورقة هو كما يلي:

*توضح هذه الورقة أن برامج الترميز التلقائي المقنعة (MAE) هي متعلمات رؤية ذاتية الإشراف قابلة للتطوير. إن نهجنا MAE بسيط: نقوم بإخفاء رقع عشوائية من صورة الإدخال وإعادة بناء بكسلات الصورة الناقصة. ويستند إلى تصميمين أساسيين. أولاً، نقوم بتطوير بنية ترميز فك ترميز غير متماثلة، مع ترميز يعمل فقط على المجموعة المرئية من الرقع (دون رموز القناع)، إلى جانب فك تشفير خفيف الوزن يقوم بإعادة بناء الصورة الأصلية من التمثيل المخفي ورموز القناع. ثانيًا، وجدنا أن إخفاء نسبة عالية من صورة الإدخال، على سبيل المثال 75%، ينتج عنه مهمة ذاتية الإشراف غير تافهة وذات معنى. يمكّننا الجمع بين هذين التصميمين من تدريب نماذج كبيرة بكفاءة وفعالية: فنحن نسرع التدريب (بمعدل 3 مرات أو أكثر) ونحسن الدقة. يسمح لنا نهجنا القابل للتطوير بتعلم نماذج عالية السعة والتي يتم تعميمها بشكل جيد: على سبيل المثال، يحقق نموذج ViT-Huge الأساسي أفضل دقة (87.8%) بين الطرق التي تستخدم بيانات ImageNet-1K فقط. ويتفوق الأداء المنقول في المهام اللاحقة على التدريب المُشرف ويظهر سلوكًا واعدًا في النطاق.*

<img src="https://user-images.githubusercontent.com/11435359/146857310-f258c86c-fde6-48e8-9cee-badd2b21bd2c.png"
alt="drawing" width="600"/>

<small>بنية MAE. مأخوذة من <a href="https://arxiv.org/abs/2111.06377">الورقة الأصلية.</a> </small>

تمت المساهمة بهذا النموذج بواسطة [nielsr](https://huggingface.co/nielsr). تمت المساهمة في إصدار TensorFlow من النموذج بواسطة [sayakpaul](https://github.com/sayakpaul) و [ariG23498](https://github.com/ariG23498) (مساهمة متساوية). يمكن العثور على الكود الأصلي [هنا](https://github.com/facebookresearch/mae).

## نصائح الاستخدام

- MAE (الترميز التلقائي المقنع) هي طريقة للتعلم الذاتي المسبق لـ Vision Transformers (ViTs). هدف التدريب المسبق بسيط نسبيًا: من خلال إخفاء جزء كبير (75%) من رقع الصورة، يجب على النموذج إعادة بناء قيم البكسل الخام. يمكن استخدام [`ViTMAEForPreTraining`] لهذا الغرض.

- بعد التدريب المسبق، يتم "إلقاء" فك التشفير المستخدم لإعادة بناء البكسلات، ويتم استخدام الترميز للضبط الدقيق/الفحص الخطي. وهذا يعني أنه بعد الضبط الدقيق، يمكنك توصيل الأوزان مباشرة في [`ViTForImageClassification`].

- يمكن استخدام [`ViTImageProcessor`] لإعداد الصور للنموذج. راجع أمثلة الكود لمزيد من المعلومات.

- لاحظ أن ترميز MAE يستخدم فقط لترميز الرقع المرئية. ثم يتم دمج الرقع المشفرة مع رموز القناع، والتي يأخذها فك التشفير (الذي يتكون أيضًا من كتل المحول) كإدخال. كل رمز قناع هو متجه مشترك ومُتعلم يشير إلى وجود رقعة مفقودة يجب التنبؤ بها. تتم إضافة تضمينات الموضع sin/cos الثابتة لكل من إدخال الترميز وفك التشفير.

- للحصول على فهم مرئي لكيفية عمل MAEs، يمكنك الاطلاع على هذا [المنشور](https://keras.io/examples/vision/masked_image_modeling/).

### استخدام Scaled Dot Product Attention (SDPA)

تتضمن PyTorch مشغل اهتمام المنتج النقطي المُدرج بشكل طبيعي كجزء من `torch.nn.functional`. تشمل هذه الدالة عدة تنفيذات يمكن تطبيقها اعتمادًا على المدخلات والأجهزة المستخدمة. راجع [الوثائق الرسمية](https://pytorch.org/docs/stable/generated/torch.nn.functional.scaled_dot_product_attention.html)
أو [صفحة الاستدلال GPU](https://huggingface.co/docs/transformers/main/en/perf_infer_gpu_one#pytorch-scaled-dot-product-attention)
لمزيد من المعلومات.

يتم استخدام SDPA بشكل افتراضي لـ `torch>=2.1.1` عندما يكون التنفيذ متاحًا، ولكن يمكنك أيضًا تعيين `attn_implementation="sdpa"` في `from_pretrained()` لطلب استخدام SDPA بشكل صريح.

```py
from transformers import ViTMAEModel
model = ViTMAEModel.from_pretrained("facebook/vit-mae-base", attn_implementation="sdpa", torch_dtype=torch.float16)
...
```

للحصول على أفضل سرعات، نوصي بتحميل النموذج بنصف الدقة (على سبيل المثال `torch.float16` أو `torch.bfloat16`).

على معيار محلي (A100-40GB، PyTorch 2.3.0، نظام التشغيل Ubuntu 22.04) مع `float32` ونموذج `facebook/vit-mae-base`، رأينا سرعات التالية خلال الاستدلال.

| حجم الدفعة | متوسط وقت الاستدلال (مللي ثانية)، وضع Eager | متوسط وقت الاستدلال (مللي ثانية)، نموذج SDPA | تسريع، SDPA / Eager (x) |
|--------------|-------------------------------------------|-------------------------------------------|------------------------------|
| 1 | 11 | 6 | 1.83 |
| 2 | 8 | 6 | 1.33 |
| 4 | 8 | 6 | 1.33 |
| 8 | 8 | 6 | 1.33 |

## الموارد

قائمة بموارد Hugging Face الرسمية وموارد المجتمع (مشار إليها بـ 🌎) لمساعدتك في البدء باستخدام ViTMAE.

- [`ViTMAEForPreTraining`] مدعوم بواسطة [نص برمجي توضيحي](https://github.com/huggingface/transformers/tree/main/examples/pytorch/image-pretraining)، مما يتيح لك تدريب النموذج من الصفر/مواصلة تدريب النموذج على بيانات مخصصة.

- يمكن العثور على دفتر ملاحظات يوضح كيفية تصور قيم البكسل المعاد بناؤها مع [`ViTMAEForPreTraining`] [هنا](https://github.com/NielsRogge/Transformers-Tutorials/blob/master/ViTMAE/ViT_MAE_visualization_demo.ipynb).

إذا كنت مهتمًا بتقديم مورد لإدراجه هنا، فالرجاء فتح طلب سحب وسنراجعه! يجب أن يوضح المورد بشكل مثالي شيئًا جديدًا بدلاً من تكرار مورد موجود.

## ViTMAEConfig

[[autodoc]] ViTMAEConfig

<frameworkcontent>
<pt>

## ViTMAEModel

[[autodoc]] ViTMAEModel

- forward

## ViTMAEForPreTraining

[[autodoc]] transformers.ViTMAEForPreTraining

- forward

</pt>
<tf>

## TFViTMAEModel

[[autodoc]] TFViTMAEModel

- call

## TFViTMAEForPreTraining

[[autodoc]] transformers.TFViTMAEForPreTraining

- call

</tf>
</frameworkcontent>