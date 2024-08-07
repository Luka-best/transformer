# Hybrid Vision Transformer (ViT Hybrid)

<Tip warning={true}>
تم وضع هذا النموذج في وضع الصيانة فقط، ولن نقبل أي طلبات سحب (PRs) جديدة لتغيير شفرته. إذا واجهتك أي مشكلات أثناء تشغيل هذا النموذج، يرجى إعادة تثبيت الإصدار الأخير الذي يدعم هذا النموذج: v4.40.2. يمكنك القيام بذلك عن طريق تشغيل الأمر التالي: `pip install -U transformers==4.40.2`.
</Tip>

## نظرة عامة
تم اقتراح نموذج Hybrid Vision Transformer (ViT) في الورقة البحثية [An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale](https://arxiv.org/abs/2010.11929) بواسطة Alexey Dosovitskiy و Lucas Beyer و Alexander Kolesnikov و Dirk Weissenborn و Xiaohua Zhai و Thomas Unterthiner و Mostafa Dehghani و Matthias Minderer و Georg Heigold و Sylvain Gelly و Jakob Uszkoreit و Neil Houlsby. وهي أول ورقة بحثية تقوم بتدريب محول Transformer encoder بنجاح على ImageNet، وحققت نتائج جيدة جدًا مقارنة بالتصميمات المعمارية الضمنية. يعد ViT hybrid متغيرًا بسيطًا من [محول الرؤية العادي](vit)، وذلك من خلال الاستفادة من العمود الفقري للشبكة العصبية التلافيفية (Convolutional Neural Network) (بشكل محدد، [BiT](bit)) والتي يتم استخدام ميزاتها كـ "رموز" أولية لمحول Transformer.

مقدمة الورقة البحثية هي كما يلي:

*بينما أصبحت بنية Transformer المعمارية هي المعيار الفعلي لمهام معالجة اللغة الطبيعية، إلا أن تطبيقاتها في رؤية الكمبيوتر لا تزال محدودة. في الرؤية، يتم تطبيق الانتباه إما بالاقتران مع الشبكات العصبية التلافيفية، أو استخدامها لاستبدال مكونات معينة من الشبكات العصبية التلافيفية مع الحفاظ على هيكلها العام في مكانه. نحن نوضح أن هذا الاعتماد على الشبكات العصبية التلافيفية ليس ضروريًا وأن محولًا نقيًا يتم تطبيقه مباشرةً على تسلسلات من رقع الصور يمكن أن يعمل بشكل جيد جدًا في مهام تصنيف الصور. عندما يتم تدريب محول الرؤية (ViT) مسبقًا على كميات كبيرة من البيانات ونقلها إلى العديد من معايير التعرف على الصور متوسطة الحجم أو صغيرة الحجم (ImageNet و CIFAR-100 و VTAB، وما إلى ذلك)، فإنه يحقق نتائج ممتازة مقارنة بشبكات التلفيف الالتفافية المتقدمة بينما يتطلب موارد حسابية أقل بكثير للتدريب.*

تمت المساهمة بهذا النموذج من قبل [nielsr](https://huggingface.co/nielsr). يمكن العثور على الشفرة الأصلية (المكتوبة في JAX) [هنا](https://github.com/google-research/vision_transformer).

## استخدام Scaled Dot Product Attention (SDPA)

تتضمن PyTorch مشغل الانتباه المنتشر المنتج النقطي المقياس كجزء من `torch.nn.functional`. تشمل هذه الدالة عدة تنفيذات يمكن تطبيقها اعتمادًا على المدخلات وأجهزة الأجهزة المستخدمة. راجع [الوثائق الرسمية](https://pytorch.org/docs/stable/generated/torch.nn.functional.scaled_dot_product_attention.html) أو صفحة [GPU Inference](https://huggingface.co/docs/transformers/main/en/perf_infer_gpu_one#pytorch-scaled-dot-product-attention) لمزيد من المعلومات.

يتم استخدام SDPA بشكل افتراضي لـ `torch>=2.1.1` عندما يكون التنفيذ متاحًا، ولكن يمكنك أيضًا تعيين `attn_implementation="sdpa"` في `from_pretrained()` لطلب استخدام SDPA بشكل صريح.

```
from transformers import ViTHybridForImageClassification
model = ViTHybridForImageClassification.from_pretrained("google/vit-hybrid-base-bit-384", attn_implementation="sdpa", torch_dtype=torch.float16)
...
```

للحصول على أفضل التحسينات في السرعة، نوصي بتحميل النموذج بنصف الدقة (على سبيل المثال `torch.float16` أو `torch.bfloat16`).

على معيار قياس محلي (A100-40GB، PyTorch 2.3.0، نظام التشغيل Ubuntu 22.04) مع `float32` ونموذج `google/vit-hybrid-base-bit-384`، رأينا التحسينات في السرعة التالية أثناء الاستنتاج.

| حجم الدفعة | متوسط وقت الاستنتاج (ميلي ثانية)، وضع Eager | متوسط وقت الاستنتاج (ميلي ثانية)، نموذج SDPA | تسريع، SDPA / Eager (x) |
|--------------|-------------------------------------------|-------------------------------------------|------------------------------|
| 1 | 29 | 18 | 1.61 |
| 2 | 26 | 18 | 1.44 |
| 4 | 25 | 18 | 1.39 |
| 8 | 34 | 24 | 1.42 |

## الموارد

فيما يلي قائمة بموارد Hugging Face الرسمية وموارد المجتمع (المشار إليها بـ 🌎) لمساعدتك في البدء باستخدام ViT Hybrid.

<PipelineTag pipeline="image-classification"/>

- [`ViTHybridForImageClassification`] مدعوم بواسطة [نص برمجي توضيحي](https://github.com/huggingface/transformers/tree/main/examples/pytorch/image-classification) و [دفتر ملاحظات](https://colab.research.google.com/github/huggingface/notebooks/blob/main/examples/image_classification.ipynb).
- راجع أيضًا: [دليل مهام تصنيف الصور](../tasks/image_classification)

إذا كنت مهتمًا بتقديم مورد لإدراجه هنا، فيرجى فتح طلب سحب (Pull Request) وسنقوم بمراجعته! يجب أن يوضح المورد بشكل مثالي شيء جديد بدلاً من تكرار مورد موجود.

## ViTHybridConfig

[[autodoc]] ViTHybridConfig

## ViTHybridImageProcessor

[[autodoc]] ViTHybridImageProcessor

- preprocess

## ViTHybridModel

[[autodoc]] ViTHybridModel

- forward

## ViTHybridForImageClassification

[[autodoc]] ViTHybridForImageClassification

- forward