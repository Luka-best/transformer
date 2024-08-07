# MobileNet V2

## نظرة عامة

اقترح نموذج MobileNet في [MobileNetV2: Inverted Residuals and Linear Bottlenecks](https://arxiv.org/abs/1801.04381) بواسطة Mark Sandler, Andrew Howard, Menglong Zhu, Andrey Zhmoginov, Liang-Chieh Chen.

الملخص من الورقة هو ما يلي:

> "في هذه الورقة، نصف بنية جوال جديدة، MobileNetV2، والتي تحسن أداء الطراز الجوال الرائد في العديد من المهام والمعايير، وكذلك عبر طيف من أحجام النماذج المختلفة. كما نصف الطرق الفعالة لتطبيق هذه النماذج المتنقلة على اكتشاف الكائنات في إطار عمل جديد نسميه SSDLite. بالإضافة إلى ذلك، نوضح كيفية بناء نماذج التجزئة الدلالية للجوال من خلال شكل مخفض من DeepLabv3 والذي نسميه Mobile DeepLabv3.

> تستند بنية MobileNetV2 على بنية بقايا مقلوبة حيث تكون طبقات عنق الزجاجة الضيقة هي المدخلات والمخرجات من كتلة البقايا، على عكس نماذج البقايا التقليدية التي تستخدم تمثيلات موسعة في المدخلات. يستخدم MobileNetV2 عمليات الضرب المعمقة خفيفة الوزن لتصفية الميزات في طبقة التوسيع الوسيطة. بالإضافة إلى ذلك، نجد أنه من المهم إزالة اللاخطيات في الطبقات الضيقة من أجل الحفاظ على قوة التمثيل. نثبت أن هذا يحسن الأداء ويقدم بديهية أدت إلى هذا التصميم. وأخيرًا، يسمح نهجنا بفك اقتران مجالات الإدخال/الإخراج من تعبيرية التحويل، مما يوفر إطار عمل مناسب لمزيد من التحليل. نقيس أدائنا على تصنيف ImageNet، وCOCO object detection، وVOC image segmentation. نقيم المقايضات بين الدقة، وعدد العمليات التي تقاس بواسطة الضربات الإضافية (MAdd)، وكذلك عدد المعلمات."

ساهم بهذا النموذج [matthijs](https://huggingface.co/Matthijs). يمكن العثور على الكود والأوزان الأصلية [هنا للنموذج الرئيسي](https://github.com/tensorflow/models/tree/master/research/slim/nets/mobilenet) و[هنا لـ DeepLabV3+](https://github.com/tensorflow/models/tree/master/research/deeplab).

## نصائح الاستخدام

- تسمى نقاط التفتيش **mobilenet_v2_*depth*_*size***، على سبيل المثال **mobilenet_v2_1.0_224**، حيث **1.0** هو مضاعف العمق (يشار إليه أحيانًا باسم "alpha" أو مضاعف العرض) و**224** هو دقة صور الإدخال التي تم تدريب النموذج عليها.

- على الرغم من أن نقطة التفتيش مدربة على صور بحجم محدد، إلا أن النموذج سيعمل على صور بأي حجم. أصغر حجم صورة مدعوم هو 32x32.

- يمكن للمرء استخدام [`MobileNetV2ImageProcessor`] لتحضير الصور للنموذج.

- تم تدريب نقاط التفتيش للتصنيف الصوري المتاحة مسبقًا على [ImageNet-1k](https://huggingface.co/datasets/imagenet-1k) (يشار إليها أيضًا باسم ILSVRC 2012، وهي مجموعة من 1.3 مليون صورة و1000 فئة). ومع ذلك، يتنبأ النموذج بـ 1001 فئة: 1000 فئة من ImageNet بالإضافة إلى فئة "خلفية" إضافية (الفهرس 0).

- يستخدم نموذج التجزئة الدلالية رأس [DeepLabV3+](https://arxiv.org/abs/1802.02611). تم تدريب نقاط التفتيش للتجزئة الدلالية المتاحة مسبقًا على [PASCAL VOC](http://host.robots.ox.ac.uk/pascal/VOC/).

- تستخدم نقاط التفتيش TensorFlow الأصلية قواعد تراص مختلفة عن PyTorch، مما يتطلب من النموذج تحديد مقدار التراص في وقت الاستدلال، حيث يعتمد ذلك على حجم صورة الإدخال. لاستخدام سلوك التراص PyTorch الأصلي، قم بإنشاء [`MobileNetV2Config`] مع `tf_padding = False`.

الميزات غير المدعومة:

- تخرج [`MobileNetV2Model`] إصدارًا مجمعًا عالميًا من الحالة المخفية الأخيرة. في النموذج الأصلي، يمكن استخدام طبقة تجميع متوسط مع نافذة ثابتة بحجم 7x7 وخطوة 1 بدلاً من التجميع العالمي. بالنسبة للمدخلات الأكبر من حجم الصورة الموصى به، فإن هذا يعطي إخراجًا مجمعًا أكبر من 1x1. لا يدعم تنفيذ Hugging Face ذلك.

- تتضمن نقاط تفتيش TensorFlow الأصلية نماذج كمية. لا ندعم هذه النماذج لأنها تتضمن عمليات "FakeQuantization" إضافية لإلغاء تكمية الأوزان.

- من الشائع استخراج الإخراج من طبقات التوسيع عند المؤشرات 10 و13، وكذلك الإخراج من طبقة الضرب النهائي 1x1، لأغراض المصب. باستخدام `output_hidden_states=True` يعيد الإخراج من جميع الطبقات المتوسطة. لا توجد حاليًا طريقة للحد من ذلك إلى طبقات محددة.

- لا يستخدم رأس DeepLabV3+ للتجزئة الدلالية طبقة الضرب النهائية من العمود الفقري، ولكن يتم حساب هذه الطبقة على أي حال. لا توجد حاليًا طريقة لإخبار [`MobileNetV2Model`] بالطبقة التي يجب تشغيلها.

## الموارد

قائمة بموارد Hugging Face الرسمية والمجتمعية (المشار إليها بـ 🌎) لمساعدتك في البدء باستخدام MobileNetV2.

<PipelineTag pipeline="image-classification"/>

- [`MobileNetV2ForImageClassification`] مدعوم بواسطة [نص البرنامج النصي](https://github.com/huggingface/transformers/tree/main/examples/pytorch/image-classification) و[دفتر الملاحظات](https://colab.research.google.com/github/huggingface/notebooks/blob/main/examples/image_classification.ipynb) هذا.

- راجع أيضًا: [دليل مهام التصنيف الصوري](../tasks/image_classification)

**التجزئة الدلالية**

- [دليل مهام التجزئة الدلالية](../tasks/semantic_segmentation)

إذا كنت مهتمًا بتقديم مورد لإدراجه هنا، فالرجاء فتح طلب سحب وسنراجعه! يجب أن يوضح المورد بشكل مثالي شيء جديد بدلاً من تكرار مورد موجود.

## MobileNetV2Config

[[autodoc]] MobileNetV2Config

## MobileNetV2FeatureExtractor

[[autodoc]] MobileNetV2FeatureExtractor

- preprocess

- post_process_semantic_segmentation

## MobileNetV2ImageProcessor

[[autodoc]] MobileNetV2ImageProcessor

- preprocess

- post_process_semantic_segmentation

## MobileNetV2Model

[[autodoc]] MobileNetV2Model

- forward

## MobileNetV2ForImageClassification

[[autodoc]] MobileNetV2ForImageClassification

- forward

## MobileNetV2ForSemanticSegmentation

[[autodoc]] MobileNetV2ForSemanticSegmentation

- forward