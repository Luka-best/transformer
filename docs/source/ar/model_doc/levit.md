# LeViT

## نظرة عامة
اقترح نموذج LeViT في [LeViT: تقديم المحولات إلى محولات الرؤية](https://arxiv.org/abs/2104.01136) بواسطة Ben Graham, وAlaaeldin El-Nouby, وHugo Touvron, وPierre Stock, وArmand Joulin, وHervé Jégou, وMatthijs Douze. يحسن LeViT [Vision Transformer (ViT)](vit) في الأداء والكفاءة من خلال بعض الاختلافات المعمارية مثل خرائط التنشيط ذات الدقة المنخفضة في المحولات وإدخال تحيز الانتباه لدمج المعلومات الموضعية.

المستخلص من الورقة هو ما يلي:

*نصمم عائلة من هندسات تصنيف الصور التي تحقق التوازن الأمثل بين الدقة والكفاءة في نظام السرعة العالية. تستفيد أعمالنا من النتائج الحديثة في البنى المعتمدة على الانتباه، والتي تتمتع بالقدرة التنافسية على أجهزة المعالجة المتوازية للغاية. نعيد النظر في المبادئ المستمدة من الأدبيات الواسعة حول الشبكات العصبية التلافيفية لتطبيقها على المحولات، وخاصة خرائط التنشيط ذات الدقة المنخفضة. كما نقدم تحيز الانتباه، وهي طريقة جديدة لدمج المعلومات الموضعية في محولات الرؤية. ونتيجة لذلك، نقترح LeViT: شبكة عصبية هجينة لتصنيف الصور ذات الاستدلال السريع.

نأخذ في الاعتبار تدابير مختلفة للكفاءة على منصات الأجهزة المختلفة، وذلك لتعكس على أفضل وجه مجموعة واسعة من سيناريوهات التطبيق. وتؤكد تجاربنا المستفيضة صحة خياراتنا الفنية وتظهر أنها مناسبة لمعظم البنى. بشكل عام، يتفوق LeViT بشكل كبير على شبكات التلافيف ومحولات الرؤية الحالية فيما يتعلق بمقايضة السرعة/الدقة. على سبيل المثال، عند دقة ImageNet بنسبة 80%، يكون LeViT أسرع بخمس مرات من EfficientNet على وحدة المعالجة المركزية.*

<img src="https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/levit_architecture.png" alt="drawing" width="600"/>

<small>هندسة LeViT. مأخوذة من <a href="https://arxiv.org/abs/2104.01136">الورقة الأصلية</a>.</small>

تمت المساهمة بهذا النموذج بواسطة [anugunj](https://huggingface.co/anugunj). يمكن العثور على الكود الأصلي [هنا](https://github.com/facebookresearch/LeViT).

## نصائح الاستخدام

- مقارنة بـ ViT، تستخدم نماذج LeViT رأس تقطير إضافي للتعلم الفعال من المعلم (والذي، في ورقة LeViT، هو نموذج مشابه لـ ResNet). يتم تعلم رأس التقطير من خلال الانتشار الخلفي تحت إشراف نموذج مشابه لـ ResNet. كما يستلهمون الإلهام من شبكات التلفيف العصبية لاستخدام خرائط تنشيط ذات دقة متناقصة لزيادة الكفاءة.

- هناك طريقتان لضبط النماذج المقطرة، إما (1) بالطريقة الكلاسيكية، عن طريق وضع رأس تنبؤ فقط أعلى حالة الإخفاء النهائية وعدم استخدام رأس التقطير، أو (2) عن طريق وضع رأس تنبؤ ورأس تقطير أعلى حالة الإخفاء النهائية. في هذه الحالة، يتم تدريب رأس التنبؤ باستخدام الانتشارية العادية بين تنبؤ الرأس والملصق الأرضي، في حين يتم تدريب رأس التقطير التنبؤي باستخدام التقطير الصعب (الانتشارية بين تنبؤ رأس التقطير والملصق الذي تنبأ به المعلم). في وقت الاستدلال، يتم أخذ متوسط التنبؤ بين كلا الرأسين كتنبؤ نهائي. (2) يُطلق عليه أيضًا "الضبط الدقيق مع التقطير"، لأنه يعتمد على معلم تم ضبطه بالفعل على مجموعة البيانات النهائية. من حيث النماذج، (1) يقابل [`LevitForImageClassification`] و (2) يقابل [`LevitForImageClassificationWithTeacher`].

- تم ضبط جميع نقاط التحقق الصادرة مسبقًا والضبط الدقيق على [ImageNet-1k](https://huggingface.co/datasets/imagenet-1k) (يشار إليها أيضًا باسم ILSVRC 2012، وهي عبارة عن مجموعة من 1.3 مليون صورة و1000 فئة). لم يتم استخدام أي بيانات خارجية. وهذا يتعارض مع نموذج ViT الأصلي، والذي استخدم بيانات خارجية مثل مجموعة بيانات JFT-300M/Imagenet-21k للضبط المسبق.

- أصدر مؤلفو LeViT 5 نماذج LeViT مدربة، والتي يمكنك توصيلها مباشرة في [`LevitModel`] أو [`LevitForImageClassification`]. تم استخدام تقنيات مثل زيادة البيانات والتحسين والتنظيم لمحاكاة التدريب على مجموعة بيانات أكبر بكثير (مع استخدام ImageNet-1k فقط للضبط المسبق). المتغيرات الخمسة المتاحة هي (جميعها مدربة على صور بحجم 224x224): *facebook/levit-128S*، *facebook/levit-128*، *facebook/levit-192*، *facebook/levit-256* و*facebook/levit-384*. لاحظ أنه يجب استخدام [`LevitImageProcessor`] لتحضير الصور للنموذج.

- يدعم [`LevitForImageClassificationWithTeacher`] حاليًا الاستدلال فقط وليس التدريب أو الضبط الدقيق.

- يمكنك الاطلاع على دفاتر الملاحظات التجريبية المتعلقة بالاستدلال وكذلك الضبط الدقيق على البيانات المخصصة [هنا](https://github.com/NielsRogge/Transformers-Tutorials/tree/master/VisionTransformer) (يمكنك فقط استبدال [`ViTFeatureExtractor`] بـ [`LevitImageProcessor`] و [`ViTForImageClassification`] بـ [`LevitForImageClassification`] أو [`LevitForImageClassificationWithTeacher`]).

## الموارد

قائمة بموارد Hugging Face الرسمية وموارد المجتمع (المشار إليها بـ 🌎) لمساعدتك في البدء باستخدام LeViT.

<PipelineTag pipeline="image-classification"/>

- [`LevitForImageClassification`] مدعوم بواسطة [نص البرنامج النصي](https://github.com/huggingface/transformers/tree/main/examples/pytorch/image-classification) و [دفتر الملاحظات](https://colab.research.google.com/github/huggingface/notebooks/blob/main/examples/image_classification.ipynb) هذا.

- راجع أيضًا: [دليل مهام تصنيف الصور](../tasks/image_classification)

إذا كنت مهتمًا بتقديم مورد لإدراجه هنا، فالرجاء فتح طلب سحب وسنراجعه! يجب أن يُظهر المورد بشكل مثالي شيئًا جديدًا بدلاً من تكرار مورد موجود.

## LevitConfig

[[autodoc]] LevitConfig

## LevitFeatureExtractor

[[autodoc]] LevitFeatureExtractor

- __call__

## LevitImageProcessor

[[autodoc]] LevitImageProcessor

- preprocess

## LevitModel

[[autodoc]] LevitModel

- forward

## LevitForImageClassification

[[autodoc]] LevitForImageClassification

- forward

## LevitForImageClassificationWithTeacher

[[autodoc]] LevitForImageClassificationWithTeacher

- forward