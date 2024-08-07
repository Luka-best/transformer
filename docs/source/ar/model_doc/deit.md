# DeiT

## نظرة عامة
اقترح نموذج DeiT في ورقة "تدريب محولات الصور الفعالة من حيث البيانات والتدريس من خلال الانتباه" بواسطة Hugo Touvron وآخرون. أظهرت محولات الرؤية (ViT) التي تم تقديمها في ورقة Dosovitskiy et al. أن أحدًا يمكنه مطابقة أو حتى التفوق على شبكات عصبية تلافيفية موجودة باستخدام محول تشفير (شبيه بـ BERT). ومع ذلك، تطلبت نماذج ViT التي تم تقديمها في تلك الورقة التدريب على بنية تحتية مكلفة لعدة أسابيع، باستخدام بيانات خارجية. تعد محولات DeiT (محولات الصور الفعالة من حيث البيانات) محولات يتم تدريبها بكفاءة أكبر لتصنيف الصور، حيث تتطلب كمية أقل بكثير من البيانات وموارد الحوسبة مقارنة بنماذج ViT الأصلية.

المقتطف من الورقة هو كما يلي:

*أظهرت مؤخرًا أن الشبكات العصبية التي تعتمد فقط على الانتباه يمكنها معالجة مهام فهم الصور مثل تصنيف الصور. ومع ذلك، يتم تدريب هذه المحولات المرئية باستخدام مئات الملايين من الصور باستخدام بنية تحتية مكلفة، مما يحد من اعتمادها. في هذا العمل، نقوم بإنشاء محول خالٍ من الضربات التنافسية عن طريق التدريب على ImageNet فقط. نقوم بتدريبها على جهاز كمبيوتر واحد في أقل من 3 أيام. يحقق محول الرؤية المرجعي الخاص بنا (86 مليون معلمة) دقة أعلى-1 تبلغ 83.1٪ (تقييم القطع الفردي) على ImageNet دون أي بيانات خارجية. والأهم من ذلك، أننا نقدم استراتيجية المعلم-الطالب محددة لمحولات. يعتمد على رمز التقطير الذي يضمن أن يتعلم الطالب من المعلم من خلال الانتباه. نُظهر أهمية هذا التقطير القائم على الرمز، خاصة عند استخدام شبكة عصبية تلافيفية كمعلم. يؤدي بنا ذلك إلى الإبلاغ عن نتائج تنافسية مع الشبكات العصبية التلافيفية لكل من ImageNet (حيث نحصل على دقة تصل إلى 85.2٪) وعند نقلها إلى مهام أخرى. نشارك الرمز والنماذج الخاصة بنا.*

تمت المساهمة بهذا النموذج بواسطة [nielsr](https://huggingface.co/nielsr). تمت إضافة إصدار TensorFlow من هذا النموذج بواسطة [amyeroberts](https://huggingface.co/amyeroberts).

## نصائح الاستخدام
- مقارنة بـ ViT، تستخدم نماذج DeiT ما يسمى رمز التقطير للتعلم بشكل فعال من معلم (والذي، في ورقة DeiT، هو نموذج مثل ResNet). يتم تعلم رمز التقطير من خلال الانتشار الخلفي، عن طريق التفاعل مع رمز الفئة ورموز التصحيح من خلال طبقات الاهتمام الذاتي.
- هناك طريقتان لضبط النماذج المقطرة، إما (1) بالطريقة الكلاسيكية، عن طريق وضع رأس تنبؤ فقط أعلى حالة الإخفاء النهائية لرموز الفئة وعدم استخدام إشارة التقطير، أو (2) عن طريق وضع رأس تنبؤ أعلى كل من رمز الفئة ورمز التقطير. في هذه الحالة، يتم تدريب رأس التنبؤ [CLS] باستخدام التناظر المتقاطع العادي بين تنبؤ الرأس والملصق الصحيح، في حين يتم تدريب رأس التقطير التنبؤي باستخدام التقطير الصعب (التناظم المتقاطع بين تنبؤ رأس التقطير والملصق الذي يتوقعه المعلم). في وقت الاستدلال، يتم أخذ متوسط التنبؤ بين كلا الرأسين كتنبؤ نهائي. (2) يُطلق عليه أيضًا "الضبط الدقيق مع التقطير"، لأنه يعتمد على معلم تم ضبطه بالفعل على مجموعة البيانات النهائية. من حيث النماذج، (1) يقابل [`DeiTForImageClassification`] و (2) يقابل [`DeiTForImageClassificationWithTeacher`].
- لاحظ أن المؤلفين أيضًا حاولوا التقطير الناعم لـ (2) (في هذه الحالة، يتم تدريب رأس التنبؤ بالتقطير باستخدام انحراف كولباك-لايبلير لمطابقة الإخراج الناعم للمعلم)، ولكن التقطير الصعب أعطى أفضل النتائج.
- تم إجراء جميع عمليات التحقق من الصحة المفرج عنها مسبقًا والضبط الدقيق على ImageNet-1k فقط. لم يتم استخدام أي بيانات خارجية. هذا على النقيض من نموذج ViT الأصلي، والذي استخدم بيانات خارجية مثل مجموعة بيانات JFT-300M/Imagenet-21k للضبط الأولي.
- أصدر مؤلفو DeiT أيضًا نماذج ViT المدربة بكفاءة أكبر، والتي يمكنك توصيلها مباشرة في [`ViTModel`] أو [`ViTForImageClassification`]. تم استخدام تقنيات مثل زيادة البيانات والتحسين والتنظيم لمحاكاة التدريب على مجموعة بيانات أكبر بكثير (مع استخدام ImageNet-1k فقط للضبط الأولي). هناك 4 متغيرات متاحة (في 3 أحجام مختلفة): *facebook/deit-tiny-patch16-224*، *facebook/deit-small-patch16-224*، *facebook/deit-base-patch16-224* و *facebook/deit-base-patch16-384*. لاحظ أنه يجب استخدام [`DeiTImageProcessor`] لتحضير الصور للنموذج.

### استخدام الانتباه المنتج المرجح بالنقاط (SDPA)
يتضمن PyTorch مشغل اهتمام منتج مرجح بالنقاط (SDPA) أصلي كجزء من `torch.nn.functional`. تشمل هذه الدالة عدة تنفيذات يمكن تطبيقها اعتمادًا على المدخلات والأجهزة المستخدمة. راجع [الوثائق الرسمية](https://pytorch.org/docs/stable/generated/torch.nn.functional.scaled_dot_product_attention.html) أو صفحة [GPU Inference](https://huggingface.co/docs/transformers/main/en/perf_infer_gpu_one#pytorch-scaled-dot-product-attention) لمزيد من المعلومات.

يتم استخدام SDPA بشكل افتراضي لـ `torch>=2.1.1` عندما يكون التنفيذ متاحًا، ولكن يمكنك أيضًا تعيين `attn_implementation="sdpa"` في `from_pretrained()` لطلب استخدام SDPA بشكل صريح.

```
from transformers import DeiTForImageClassification
model = DeiTForImageClassification.from_pretrained("facebook/deit-base-distilled-patch16-224", attn_implementation="sdpa", torch_dtype=torch.float16)
...
```

للحصول على أفضل التحسينات، نوصي بتحميل النموذج بنصف الدقة (على سبيل المثال `torch.float16` أو `torch.bfloat16`).

في معيار محلي (A100-40GB، PyTorch 2.3.0، نظام التشغيل Ubuntu 22.04) مع `float32` ونموذج `facebook/deit-base-distilled-patch16-224`، رأينا تسريعًا التالي أثناء الاستدلال.

| حجم الدفعة | متوسط وقت الاستدلال (مللي ثانية)، وضع Eager | متوسط وقت الاستدلال (مللي ثانية)، نموذج SDPA | تسريع، SDPA / Eager (x) |
|--------------|-------------------------------------------|-------------------------------------------|------------------------------|
| 1 | 8 | 6 | 1.33 |
| 2 | 9 | 6 | 1.5 |
| 4 | 9 | 6 | 1.5 |
| 8 | 8 | 6 | 1.33 |

## الموارد
قائمة بموارد Hugging Face الرسمية وموارد المجتمع (مشار إليها بـ 🌎) لمساعدتك في البدء باستخدام DeiT.

- [`DeiTForImageClassification`] مدعوم بواسطة [نص البرنامج النصي](https://github.com/huggingface/transformers/tree/main/examples/pytorch/image-classification) و [دفتر الملاحظات](https://colab.research.google.com/github/huggingface/notebooks/blob/main/examples/image_classification.ipynb) هذا.
- راجع أيضًا: [دليل مهام تصنيف الصور](../tasks/image_classification)

بالإضافة إلى ذلك:

- [`DeiTForMaskedImageModeling`] مدعوم بواسطة [نص البرنامج النصي](https://github.com/huggingface/transformers/tree/main/examples/pytorch/image-pretraining) هذا.

إذا كنت مهتمًا بتقديم مورد لإدراجه هنا، فلا تتردد في فتح طلب سحب وسنراجعه! يجب أن يُظهر المورد المثالي شيئًا جديدًا بدلاً من تكرار مورد موجود.

## DeiTConfig

[[autodoc]] DeiTConfig

## DeiTFeatureExtractor

[[autodoc]] DeiTFeatureExtractor

- __call__

## DeiTImageProcessor

[[autodoc]] DeiTImageProcessor

- preprocess

<frameworkcontent>
<pt>

## DeiTModel

[[autodoc]] DeiTModel

- forward

## DeiTForMaskedImageModeling

[[autodoc]] DeiTForMaskedImageModeling

- forward

## DeiTForImageClassification

[[autodoc]] DeiTForImageClassification

- forward

## DeiTForImageClassificationWithTeacher

[[autodoc]] DeiTForImageClassificationWithTeacher

- forward

</pt>
<tf>

## TFDeiTModel

[[autodoc]] TFDeiTModel

- call

## TFDeiTForMaskedImageModeling

[[autodoc]] TFDeiTForMaskedImageModeling

- call

## TFDeiTForImageClassification

[[autodoc]] TFDeiTForImageClassification

- call

## TFDeiTForImageClassificationWithTeacher

[[autodoc]] TFDeiTForImageClassificationWithTeacher

- call

</tf>

</frameworkcontent>