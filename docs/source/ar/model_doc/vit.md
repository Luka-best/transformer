# محول الرؤية (ViT)

## نظرة عامة

اقترح نموذج محول الرؤية (ViT) في [صورة تستحق 16x16 كلمات: محولات للتعرف على الصور على نطاق واسع](https://arxiv.org/abs/2010.11929) بواسطة Alexey Dosovitskiy، Lucas Beyer، Alexander Kolesnikov، Dirk Weissenborn، Xiaohua Zhai، Thomas Unterthiner، Mostafa Dehghani، Matthias Minderer، Georg Heigold، Sylvain Gelly، Jakob Uszkoreit، Neil Houlsby. وهي أول ورقة تنجح في تدريب محول تشفير على ImageNet، وتحقيق نتائج جيدة جدًا مقارنة بالتصميمات المعمارية للشبكات التلافيفية المألوفة.

الملخص من الورقة هو ما يلي:

*بينما أصبحت بنية المحول المعياري معيارًا فعليًا لمهام معالجة اللغة الطبيعية، لا تزال تطبيقاته في رؤية الكمبيوتر محدودة. في الرؤية، يتم تطبيق الانتباه إما بالاقتران مع الشبكات التلافيفية، أو استخدامه لاستبدال مكونات معينة من الشبكات التلافيفية مع الحفاظ على هيكلها العام في مكانه. نُظهر أن هذا الاعتماد على الشبكات التلافيفية ليس ضروريًا وأن محولًا نقيًا مطبقًا مباشرةً على تسلسلات من رقع الصور يمكن أن يحقق أداءً جيدًا جدًا في مهام تصنيف الصور. عندما يتم التدريب المسبق على كميات كبيرة من البيانات ونقلها إلى العديد من معايير التعرف على الصور متوسطة الحجم أو صغيرة الحجم (ImageNet، CIFAR-100، VTAB، إلخ)، يحقق محول الرؤية (ViT) نتائج ممتازة مقارنة بشبكات التلافيف المتقدمة مع الحاجة إلى موارد حوسبة أقل بكثير للتدريب.*

<img src="https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/transformers/model_doc/vit_architecture.jpg" alt="drawing" width="600"/>

<small>هندسة ViT. مأخوذة من <a href="https://arxiv.org/abs/2010.11929">الورقة الأصلية.</a></small>

بعد محول الرؤية الأصلي، تم إجراء بعض الأعمال اللاحقة:

- [DeiT](deit) (محولات الصور الفعالة من حيث البيانات) بواسطة Facebook AI. نماذج DeiT هي محولات رؤية مقطرة.
كما أصدر مؤلفو DeiT نماذج ViT المدربة بكفاءة أكبر، والتي يمكنك توصيلها مباشرةً في [`ViTModel`] أو [`ViTForImageClassification`]. هناك 4 متغيرات متاحة (في 3 أحجام مختلفة): *facebook/deit-tiny-patch16-224*، *facebook/deit-small-patch16-224*، *facebook/deit-base-patch16-224* و *facebook/deit-base-patch16-384*. يرجى ملاحظة أنه يجب استخدام [`DeiTImageProcessor`] لتحضير الصور للنموذج.

- [BEiT](beit) (التدريب المسبق لـ BERT لمحولات الصور) بواسطة Microsoft Research. تتفوق نماذج BEiT على المحولات البصرية المُدربة المسبقة الخاضعة للإشراف باستخدام طريقة ذاتية الإشراف مستوحاة من BERT (نمذجة الصور المقنعة) وتعتمد على VQ-VAE.

- DINO (طريقة للتدريب الذاتي الخاضع للإشراف لمحولات الرؤية) بواسطة Facebook AI. تُظهر محولات الرؤية المدربة باستخدام طريقة DINO خصائص مثيرة للاهتمام لم يسبق رؤيتها مع النماذج التلافيفية. فهي قادرة على تجزئة الكائنات، دون أن تكون مدربة على ذلك من قبل. يمكن العثور على نقاط تفتيش DINO على [المركز](https://huggingface.co/models?other=dino).

- [MAE](vit_mae) (المشفرات الذاتية المقنعة) بواسطة Facebook AI. من خلال التدريب المسبق لمحولات الرؤية لإعادة بناء قيم البكسل لنسبة كبيرة (75%) من الرقع المقنعة (باستخدام بنية مشفر فك تشفير غير متماثلة)، يُظهر المؤلفون أن هذه الطريقة البسيطة تتفوق على التدريب المسبق الخاضع للإشراف بعد الضبط الدقيق.

تمت المساهمة بهذا النموذج بواسطة [nielsr](https://huggingface.co/nielsr). يمكن العثور على الكود الأصلي (المكتوب في JAX) [هنا](https://github.com/google-research/vision_transformer).

يرجى ملاحظة أننا قمنا بتحويل الأوزان من مكتبة Ross Wightman's [timm](https://github.com/rwightman/pytorch-image-models)، الذي قام بالفعل بتحويل الأوزان من JAX إلى PyTorch. تعود الفضل إليه!

## نصائح الاستخدام

- لتغذية الصور إلى محول الترميز، يتم تقسيم كل صورة إلى تسلسل من رقع ثابتة الحجم وغير متداخلة، والتي يتم تضمينها خطيًا بعد ذلك. يتم إضافة رمز [CLS] للعمل كممثِل للصورة بأكملها، والذي يمكن استخدامه للتصنيف. يضيف المؤلفون أيضًا تضمين الموضع المطلق، ويغذون تسلسل المتجهات الناتج إلى محول ترميز قياسي.

- نظرًا لأن محول الرؤية يتوقع أن يكون لكل صورة نفس الحجم (الدقة)، فيمكن استخدام [`ViTImageProcessor`] لإعادة تحجيم (أو إعادة تحجيم) الصور وتطبيعها للنموذج.

- ينعكس كل من دقة الرقع ودقة الصورة المستخدمة أثناء التدريب المسبق أو الضبط الدقيق في اسم كل نقطة تفتيش. على سبيل المثال، يشير `google/vit-base-patch16-224` إلى بنية ذات حجم أساسي بدقة رقعة 16x16 ودقة ضبط دقيق 224x224. يمكن العثور على جميع نقاط التفتيش على [المركز](https://huggingface.co/models?search=vit).

- نقاط التفتيش المتاحة إما (1) مُدربة مسبقًا على [ImageNet-21k](http://www.image-net.org/) (مجموعة من 14 مليون صورة و21 ألف فئة) فقط، أو (2) أيضًا ضبط دقيق على [ImageNet](http://www.image-net.org/challenges/LSVRC/2012/) (يشار إليها أيضًا باسم ILSVRC 2012، مجموعة من 1.3 مليون صورة و1000 فئة).

- تم التدريب المسبق لمحول الرؤية باستخدام دقة 224x224. أثناء الضبط الدقيق، يكون من المفيد غالبًا استخدام دقة أعلى من التدريب المسبق [(Touvron et al.)، 2019](https://arxiv.org/abs/1906.06423)، [(Kolesnikov et al.)، 2020](https://arxiv.org/abs/1912.11370). لأداء الضبط الدقيق بدقة أعلى، يقوم المؤلفون بالاستيفاء الخطي لتضمين الموضع المُدرب مسبقًا، وفقًا لموقعه في الصورة الأصلية.

- يتم الحصول على أفضل النتائج باستخدام التدريب المسبق الخاضع للإشراف، وهو ما لا يحدث في NLP. كما أجرى المؤلفون تجربة باستخدام هدف تدريب مسبق ذاتي الإشراف، وهو التنبؤ بالرقعة المقنعة (مستوحى من نمذجة اللغة المقنعة). مع هذا النهج، يحقق نموذج ViT-B/16 الأصغر حجمًا دقة 79.9% على ImageNet، وهو تحسن كبير بنسبة 2% للتدريب من الصفر، ولكنه لا يزال أقل بنسبة 4% من التدريب المسبق الخاضع للإشراف.

### استخدام الانتباه الموزون بنقط المنتج (SDPA)

تتضمن PyTorch مشغل اهتمام بنقط المنتج الموزون (SDPA) كجزء من `torch.nn.functional`. تشمل هذه الدالة عدة تنفيذات يمكن تطبيقها اعتمادًا على المدخلات والأجهزة المستخدمة. راجع [الوثائق الرسمية](https://pytorch.org/docs/stable/generated/torch.nn.functional.scaled_dot_product_attention.html) أو صفحة [GPU Inference](https://huggingface.co/docs/transformers/main/en/perf_infer_gpu_one#pytorch-scaled-dot-product-attention) لمزيد من المعلومات.

يتم استخدام SDPA بشكل افتراضي لـ `torch>=2.1.1` عندما يكون التنفيذ متاحًا، ولكن يمكنك أيضًا تعيين `attn_implementation="sdpa"` في `from_pretrained()` لطلب استخدام SDPA صراحةً.

```py
from transformers import ViTForImageClassification
model = ViTForImageClassification.from_pretrained("google/vit-base-patch16-224", attn_implementation="sdpa", torch_dtype=torch.float16)
...
```

للحصول على أفضل تسريع، نوصي بتحميل النموذج بنصف الدقة (على سبيل المثال `torch.float16` أو `torch.bfloat16`).

على معيار محلي (A100-40GB، PyTorch 2.3.0، نظام تشغيل Ubuntu 22.04) مع `float32` ونموذج `google/vit-base-patch16-224`، رأينا تسريع الاستدلال التالي.

| حجم الدفعة | متوسط وقت الاستدلال (ميلي ثانية)، وضع Eager | متوسط وقت الاستدلال (ميلي ثانية)، نموذج SDPA | تسريع، SDPA / Eager (x) |
|--------------|-------------------------------------------|-------------------------------------------|------------------------------|
| 1 | 7 | 6 | 1.17 |
| 2 | 8 | 6 | 1.33 |
| 4 | 8 | 6 | 1.33 |
| 8 | 8 | 6 | 1.33 |

## الموارد

يمكن العثور على دفاتر الملاحظات التوضيحية المتعلقة بالاستدلال وكذلك الضبط الدقيق لـ ViT على بيانات مخصصة [هنا](https://github.com/NielsRogge/Transformers-Tutorials/tree/master/VisionTransformer).

قائمة بموارد Hugging Face الرسمية وموارد المجتمع (المشار إليها بـ 🌎) لمساعدتك في البدء مع ViT. إذا كنت مهتمًا بتقديم مورد لإدراجه هنا، فيرجى فتح طلب سحب وسنراجعه! يجب أن يوضح المورد بشكل مثالي شيء جديد بدلاً من تكرار مورد موجود.

`ViTForImageClassification` مدعوم من:

<PipelineTag pipeline="image-classification"/>

- منشور مدونة حول [الضبط الدقيق لـ ViT لتصنيف الصور باستخدام محولات Hugging Face](https://huggingface.co/blog/fine-tune-vit)

- منشور مدونة حول [تصنيف الصور باستخدام محولات Hugging Face و`Keras`](https://www.philschmid.de/image-classification-huggingface-transformers-keras)

- دفتر ملاحظات حول [الضبط الدقيق لتصنيف الصور باستخدام محولات Hugging Face](https://github.com/huggingface/notebooks/blob/main/examples/image_classification.ipynb)

- دفتر ملاحظات حول كيفية [الضبط الدقيق لمحول الرؤية على CIFAR-10 باستخدام المدرب Hugging Face](https://github.com/NielsRogge/Transformers-Tutorials/blob/master/VisionTransformer/Fine_tuning_the_Vision_Transformer_on_CIFAR_10_with_the_%F0%9F%A4%97_Trainer.ipynb)

- دفتر ملاحظات حول كيفية [الضبط الدقيق لمحول الرؤية على CIFAR-10 باستخدام PyTorch Lightning](https://github.com/NielsRogge/Transformers-Tutorials/blob/master/VisionTransformer/Fine_tuning_the_Vision_Transformer_on_CIFAR_10_with_PyTorch_Lightning.ipynb)

⚗️ التحسين

- منشور مدونة حول كيفية [تسريع محول الرؤية (ViT) باستخدام الضبط الآلي باستخدام Optimum](https://www.philschmid.de/optimizing-vision-transformer)

⚡️ الاستدلال

- دفتر ملاحظات حول [عرض توضيحي سريع: محول الرؤية (ViT) بواسطة Google Brain](https://github.com/NielsRogge/Transformers-Tutorials/blob/master/VisionTransformer/Quick_demo_of_HuggingFace_version_of_Vision_Transformer_inference.ipynb)

🚀 النشر

- منشور مدونة حول [نشر نماذج الرؤية TensorFlow في Hugging Face باستخدام TF Serving](https://huggingface.co/blog/tf-serving-vision)

- منشور مدونة حول [نشر محول الرؤية Hugging Face على Vertex AI](https://huggingface.co/blog/deploy-vertex-ai)

- منشور مدونة حول [نشر محول الرؤية Hugging Face على Kubernetes مع TF Serving](https://huggingface.co/blog/deploy-tfserving-kubernetes)

## ViTConfig

[[autodoc]] ViTConfig

## ViTFeatureExtractor

[[autodoc]] ViTFeatureExtractor

- __call__

## ViTImageProcessor

[[autodoc]] ViTImageProcessor

- preprocess

## ViTImageProcessorFast

[[autodoc]] ViTImageProcessorFast

- preprocess

<frameworkcontent>

<pt>

## ViTModel

[[autodoc]] ViTModel

- forward

## ViTForMaskedImageModeling

[[autodoc]] ViTForMaskedImageModeling

- forward

## ViTForImageClassification

[[autodoc]] ViTForImageClassification

- forward

</pt>

<tf>

## TFViTModel

[[autodoc]] TFViTModel

- call

## TFViTForImageClassification

[[autodoc]] TFViTForImageClassification

- call

</tf>

<jax>

## FlaxVitModel

[[autodoc]] FlaxViTModel

- __call__

## FlaxViTForImageClassification

[[autodoc]] FlaxViTForImageClassification

- __call__

</jax>

</frameworkcontent>