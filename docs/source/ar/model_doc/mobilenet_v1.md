# MobileNet V1

## نظرة عامة

تم اقتراح نموذج MobileNet في [MobileNets: Efficient Convolutional Neural Networks for Mobile Vision Applications](https://arxiv.org/abs/1704.04861) بواسطة Andrew G. Howard, Menglong Zhu, Bo Chen, Dmitry Kalenichenko, Weijun Wang, Tobias Weyand, Marco Andreetto, Hartwig Adam.

الملخص من الورقة هو ما يلي:

*نقدم فئة من النماذج الفعالة تسمى MobileNets لتطبيقات الرؤية المتنقلة والمدمجة. تستند MobileNets إلى بنية مبسطة تستخدم التلافيف قابلة للفصل بعمق لبناء شبكات عصبية عميقة خفيفة الوزن. نقدم اثنين من المعلمات الفائقة العالمية البسيطة التي تُوازن بكفاءة بين الكمون والدقة. تسمح هذه المعلمات الفائقة لمُنشئ النموذج باختيار الحجم المناسب للنموذج لتطبيقه بناءً على قيود المشكلة. نقدم تجارب مكثفة على مقايضات الموارد والدقة ونظهر أداءً قويًا مقارنة بالنماذج الشائعة الأخرى على تصنيف ImageNet. ثم نثبت فعالية MobileNets عبر مجموعة واسعة من التطبيقات والاستخدامات بما في ذلك اكتشاف الأشياء، والتصنيف الدقيق، وسمات الوجه، والتحديد الجغرافي واسع النطاق.*

تمت المساهمة بهذا النموذج من قبل [matthijs](https://huggingface.co/Matthijs). يمكن العثور على الكود والأوزان الأصلية [هنا](https://github.com/tensorflow/models/blob/master/research/slim/nets/mobilenet_v1.md).

## نصائح الاستخدام

- تتم تسمية نقاط التفتيش باسم **mobilenet_v1_ *depth* _ *size***، على سبيل المثال **mobilenet_v1_1.0_224**، حيث **1.0** هو مضاعف العمق (يُشار إليه أحيانًا باسم "alpha" أو مضاعف العرض) و**224** هو دقة صور الإدخال التي تم تدريب النموذج عليها.

- على الرغم من أن نقطة التفتيش مدربة على صور بحجم محدد، إلا أن النموذج سيعمل على الصور بأي حجم. أصغر حجم صورة مدعوم هو 32x32.

- يمكن للمرء استخدام [`MobileNetV1ImageProcessor`] لتحضير الصور للنموذج.

- تم تدريب نقاط تفتيش تصنيف الصور المتاحة مسبقًا على [ImageNet-1k](https://huggingface.co/datasets/imagenet-1k) (يشار إليها أيضًا باسم ILSVRC 2012، وهي مجموعة من 1.3 مليون صورة و1000 فئة). ومع ذلك، فإن النموذج يتنبأ بـ 1001 فئة: 1000 فئة من ImageNet بالإضافة إلى فئة "خلفية" إضافية (الفهرس 0).

- تستخدم نقاط التفتيش TensorFlow الأصلية قواعد ترميز مختلفة عن PyTorch، مما يتطلب من النموذج تحديد مقدار الترميز في وقت الاستدلال، حيث يعتمد ذلك على حجم صورة الإدخال. لاستخدام سلوك الترميز PyTorch الأصلي، قم بإنشاء [`MobileNetV1Config`] باستخدام `tf_padding = False`.

الميزات غير المدعومة:

- تخرج [`MobileNetV1Model`] إصدارًا مجمعًا عالميًا من الحالة الأخيرة المخفية. في النموذج الأصلي، من الممكن استخدام طبقة تجميع متوسط 7x7 مع قفزة 2 بدلاً من التجميع العالمي. بالنسبة للإدخالات الأكبر، فإن هذا يعطي إخراجًا مجمعًا أكبر من بكسل 1x1. لا يدعم التنفيذ الخاص بـ HuggingFace ذلك.

- من غير الممكن حاليًا تحديد `output_stride`. بالنسبة لخطوات الإخراج الأصغر، يستدعي النموذج الأصلي التلافيف المنتفخة لمنع تقليل الدقة المكانية بشكل أكبر. دقة إخراج نموذج HuggingFace هي دائمًا 32.

- تتضمن نقاط تفتيش TensorFlow الأصلية نماذج كمية. لا ندعم هذه النماذج لأنها تتضمن عمليات "FakeQuantization" إضافية لإلغاء تكمية الأوزان.

- من الشائع استخراج الإخراج من الطبقات النقطية عند المؤشرات 5 و11 و12 و13 لأغراض المصب. باستخدام `output_hidden_states=True` يعيد إخراج من جميع الطبقات المتوسطة. لا توجد حاليًا طريقة للحد من ذلك إلى طبقات محددة.

## الموارد

قائمة بموارد Hugging Face الرسمية والمجتمعية (مشار إليها برمز 🌎) لمساعدتك في البدء باستخدام MobileNetV1.

<PipelineTag pipeline="image-classification"/>

- [`MobileNetV1ForImageClassification`] مدعوم بواسطة [نص البرنامج النصي](https://github.com/huggingface/transformers/tree/main/examples/pytorch/image-classification) و [دفتر الملاحظات](https://colab.research.google.com/github/huggingface/notebooks/blob/main/examples/image_classification.ipynb) هذا.

- راجع أيضًا: [دليل مهام تصنيف الصور](../tasks/image_classification)

إذا كنت مهتمًا بتقديم مورد لإدراجه هنا، فالرجاء فتح طلب سحب وسنقوم بمراجعته! يجب أن يُظهر المورد بشكل مثالي شيئًا جديدًا بدلاً من تكرار مورد موجود.

## MobileNetV1Config

[[autodoc]] MobileNetV1Config

## MobileNetV1FeatureExtractor

[[autodoc]] MobileNetV1FeatureExtractor

- preprocess

## MobileNetV1ImageProcessor

[[autodoc]] MobileNetV1ImageProcessor

- preprocess

## MobileNetV1Model

[[autodoc]] MobileNetV1Model

- forward

## MobileNetV1ForImageClassification

[[autodoc]] MobileNetV1ForImageClassification

- forward