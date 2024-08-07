# DETR

## نظرة عامة

اقتُرح نموذج DETR في ورقة "End-to-End Object Detection with Transformers" بواسطة Nicolas Carion وآخرين. يتكون نموذج DETR من شبكة عصبية تعاقبية تليها محول تشفير وفك تشفير يمكن تدريبهما من البداية إلى النهاية للكشف عن الأشياء. إنه يبسط كثيرًا من تعقيدات النماذج مثل Faster-R-CNN وMask-R-CNN، والتي تستخدم أشياء مثل اقتراحات المناطق، وإجراءات القمع غير القصوى، وتوليد المراسي. علاوة على ذلك، يمكن أيضًا توسيع نموذج DETR بشكل طبيعي لأداء التجزئة الشاملة، وذلك ببساطة عن طريق إضافة رأس قناع أعلى مخرجات فك التشفير.

مقتطف من الورقة البحثية على النحو التالي:

> "نقدم طريقة جديدة تنظر إلى الكشف عن الأشياء كمشكلة تنبؤ مجموعة مباشرة. يبسط نهجنا خط أنابيب الكشف، مما يزيل فعليًا الحاجة إلى العديد من المكونات المصممة يدويًا مثل إجراءات القمع غير القصوى أو توليد المرساة التي تشفر صراحة معرفتنا المسبقة بالمهمة. المكونات الرئيسية للإطار الجديد، المسمى محول الكشف أو DETR، هي خسارة عالمية قائمة على المجموعة تجبر التنبؤات الفريدة من خلال المطابقة الثنائية، وبنية محول الترميز وفك الترميز. بالنظر إلى مجموعة صغيرة ثابتة من استفسارات الكائن المُعلم، يُجري DETR استدلالًا حول علاقات الأشياء وسياق الصورة العالمي لإخراج مجموعة التنبؤات النهائية بالتوازي. النموذج الجديد مفهوميًا بسيط ولا يتطلب مكتبة متخصصة، على عكس العديد من الكاشفات الحديثة الأخرى. يُظهر DETR دقة وأداء وقت التشغيل على قدم المساواة مع خط الأساس Faster RCNN الراسخ والمحسّن جيدًا في مجموعة بيانات COCO الصعبة للكشف عن الأشياء. علاوة على ذلك، يمكن تعميم DETR بسهولة لإنتاج التجزئة الشاملة بطريقة موحدة. نُظهر أنه يتفوق بشكل كبير على خطوط الأساس التنافسية."

تمت المساهمة بهذا النموذج من قبل [nielsr](https://huggingface.co/nielsr). يمكن العثور على الكود الأصلي [هنا](https://github.com/facebookresearch/detr).

## كيف يعمل DETR

فيما يلي ملخص يوضح كيفية عمل [`~transformers.DetrForObjectDetection`].

أولاً، يتم إرسال صورة عبر شبكة عصبية تعاقبية مُعلمة مسبقًا (في الورقة، يستخدم المؤلفون ResNet-50/ResNet-101). لنفترض أننا أضفنا أيضًا بُعد الدفعة. وهذا يعني أن المدخلات إلى الشبكة العصبية التعاقبية هي مصفوفة ذات شكل `(batch_size، 3، height، width)`، مع افتراض أن الصورة تحتوي على 3 قنوات لونية (RGB). تقوم الشبكة العصبية التعاقبية بإخراج خريطة ميزات ذات دقة أقل، عادةً ذات شكل `(batch_size، 2048، height/32، width/32)`. يتم بعد ذلك إسقاطها لمطابقة البعد المخفي لمحول DETR، والذي يكون `256` بشكل افتراضي، باستخدام طبقة `nn.Conv2D`. لذا، لدينا الآن مصفوفة ذات شكل `(batch_size، 256، height/32، width/32)`. بعد ذلك، يتم تسطيح خريطة الميزات وتعديلها للحصول على مصفوفة ذات شكل `(batch_size، seq_len، d_model)` = `(batch_size، width/32*height/32، 256)`. لذا، فإن أحد الاختلافات مع نماذج معالجة اللغات الطبيعية هو أن طول التسلسل أطول من المعتاد، ولكن مع `d_model` أصغر (والذي يكون عادةً 768 أو أعلى في نماذج معالجة اللغات الطبيعية).

بعد ذلك، يتم إرسال هذا إلى المشفر، مما يؤدي إلى إخراج `encoder_hidden_states` بنفس الشكل (يمكن اعتبارها ميزات صورة). بعد ذلك، يتم إرسال ما يسمى بـ **استعلامات الكائن** عبر فك التشفير. هذه مصفوفة ذات شكل `(batch_size، num_queries، d_model)`، مع `num_queries` يتم تعيينها عادةً إلى 100 وإعدادها إلى الصفر. هذه المدخلات هي ترميزات موضع مُعلمة يشير إليها المؤلفون باستعلامات الكائن، وعلى غرار المشفر، يتم إضافتها إلى إدخال كل طبقة اهتمام. سيبحث كل استعلام كائن عن كائن معين في الصورة. يقوم فك التشفير بتحديث هذه الترميزات من خلال طبقات اهتمام ذاتية واهتمام بتشفير وفك تشفير متعددة لإخراج `decoder_hidden_states` بنفس الشكل: `(batch_size، num_queries، d_model)`. بعد ذلك، يتم إضافة رأسين لأعلى للكشف عن الأشياء: طبقة خطية لتصنيف كل استعلام كائن إلى أحد الأشياء أو "لا شيء"، وMLP للتنبؤ بحدود الإحداثيات لكل استعلام.

يتم تدريب النموذج باستخدام **خسارة المطابقة الثنائية**: لذا ما نفعله بالفعل هو مقارنة الفئات المتنبأ بها + حدود الإحداثيات لكل من استعلامات N = 100 مع التعليقات التوضيحية الأرضية الحقيقة، مع توسيع نطاقها إلى نفس الطول N (لذا، إذا كانت الصورة تحتوي على 4 أشياء فقط، فستحتوي 96 تعليق توضيحي فقط على "لا شيء" كفئة و"لا حدود إحداثيات" كحدود إحداثيات). يتم استخدام خوارزمية المطابقة الهنغارية للعثور على خريطة واحدة لواحدة مثالية لكل من الاستعلامات N والتعليقات N. بعد ذلك، يتم استخدام الانحدار اللوغاريتمي (للطبقات) ومزيج خطي من L1 و [خسارة IoU العامة](https://giou.stanford.edu/) (لحدود الإحداثيات) لتحسين معلمات النموذج.

يمكن توسيع نموذج DETR بشكل طبيعي لأداء التجزئة الشاملة (التي توحد التجزئة الدلالية وتجزئة المثيل). يضيف [`~transformers.DetrForSegmentation`] رأس قناع أعلى [`~transformers.DetrForObjectDetection`]. يمكن تدريب رأس القناع إما بشكل مشترك، أو في عملية من خطوتين، حيث يتم أولاً تدريب نموذج [`~transformers.DetrForObjectDetection`] للكشف عن حدود الإحداثيات حول كل من "الأشياء" (المثيلات) و"الأشياء" (أشياء الخلفية مثل الأشجار والطرق والسماء)، ثم يتم تجميد جميع الأوزان وتدريب رأس القناع فقط لمدة 25 حقبة. تجريبياً، تعطي هاتان المقاربتان نتائج مماثلة. لاحظ أن التنبؤ بالحدود مطلوب لإمكانية التدريب، حيث يتم حساب المطابقة الهنغارية باستخدام المسافات بين الحدود.

## نصائح الاستخدام

- يستخدم نموذج DETR ما يسمى بـ **استعلامات الكائن** للكشف عن الأشياء في صورة. يحدد عدد الاستعلامات العدد الأقصى للأشياء التي يمكن اكتشافها في صورة واحدة، وهو مضبوط على 100 بشكل افتراضي (راجع معلمة `num_queries` من [`~transformers.DetrConfig`]). لاحظ أنه من الجيد أن يكون هناك بعض المرونة (في COCO، استخدم المؤلفون 100، في حين أن العدد الأقصى للأشياء في صورة COCO هو ~70).

- يقوم فك تشفير نموذج DETR بتحديث ترميزات الاستعلام بالتوازي. هذا يختلف عن نماذج اللغة مثل GPT-2، والتي تستخدم فك تشفير ذاتي الرجوع بدلاً من ذلك. وبالتالي، لا يتم استخدام قناع اهتمام سببي.

- يضيف نموذج DETR ترميزات الموضع إلى الحالات المخفية في كل طبقة اهتمام ذاتي واهتمام متعدد قبل إسقاطها إلى استعلامات ومفاتيح. بالنسبة لترميزات موضع الصورة، يمكن للمرء أن يختار بين ترميزات موضع ثابتة أو تعلمية. بشكل افتراضي، يتم ضبط معلمة `position_embedding_type` من [`~transformers.DetrConfig`] على `"sine"`.

- أثناء التدريب، وجد مؤلفو نموذج DETR أنه من المفيد استخدام خسائر مساعدة في فك التشفير، خاصة لمساعدة النموذج على إخراج العدد الصحيح من الأشياء لكل فئة. إذا قمت بتعيين معلمة `auxiliary_loss` من [`~transformers.DetrConfig`] إلى `True`، فسيتم إضافة شبكات عصبية أمامية وخسائر هنغارية بعد كل طبقة فك تشفير (مع مشاركة FFNs للمعلمات).

- إذا كنت تريد تدريب النموذج في بيئة موزعة عبر عدة عقد، فيجب عليك تحديث متغير _num_boxes_ في فئة _DetrLoss_ من _modeling_detr.py_. عند التدريب على عدة عقد، يجب تعيين هذا إلى متوسط عدد الصناديق المستهدفة عبر جميع العقد، كما هو موضح في التنفيذ الأصلي [هنا](https://github.com/facebookresearch/detr/blob/a54b77800eb8e64e3ad0d8237789fcbf2f8350c5/models/detr.py#L227-L232).

- يمكن تهيئة [`~transformers.DetrForObjectDetection`] و [`~transformers.DetrForSegmentation`] بأي شبكة عصبية تعاقبية متوفرة في [مكتبة timm](https://github.com/rwightman/pytorch-image-models). يمكن تهيئة نموذج مع شبكة عصبية تعاقبية MobileNet على سبيل المثال عن طريق تعيين سمة `backbone` من [`~transformers.DetrConfig`] إلى `"tf_mobilenetv3_small_075"`، ثم تهيئة النموذج باستخدام هذا التكوين.

- يقوم نموذج DETR بتغيير حجم الصور المدخلة بحيث يكون الجانب الأقصر على الأقل عددًا معينًا من البكسلات في حين أن الأطول هو 1333 بكسل كحد أقصى. أثناء التدريب، يتم استخدام زيادة حجم المقياس بحيث يكون الجانب الأقصر عشوائيًا على الأقل 480 بكسل وكحد أقصى 800 بكسل. أثناء الاستدلال، يتم تعيين الجانب الأقصر إلى 800. يمكن استخدام [`~transformers.DetrImageProcessor`] لإعداد الصور (والتعليقات التوضيحية الاختيارية بتنسيق COCO) للنموذج. نظرًا لهذا التغيير في الحجم، يمكن أن يكون للصور في دفعة أحجام مختلفة. يحل نموذج DETR هذه المشكلة عن طريق إضافة صور إلى الحجم الأكبر في دفعة، وعن طريق إنشاء قناع بكسل يشير إلى البكسلات الحقيقية/الوسادات. بدلاً من ذلك، يمكن للمرء أيضًا تحديد دالة تجميع مخصصة من أجل تجميع الصور معًا، باستخدام [`~transformers.DetrImageProcessor.pad_and_create_pixel_mask`].

- سيحدد حجم الصور مقدار الذاكرة المستخدمة، وبالتالي سيحدد `batch_size`. يُنصح باستخدام حجم دفعة يبلغ 2 لكل GPU. راجع [خيط GitHub](https://github.com/facebookresearch/detr/issues/150) هذا لمزيد من المعلومات.

هناك ثلاث طرق لتهيئة نموذج DETR (حسب تفضيلك):

الخيار 1: تهيئة نموذج DETR بأوزان مُعلمة مسبقًا للنموذج بالكامل

```py
>>> from transformers import DetrForObjectDetection

>>> model = DetrForObjectDetection.from_pretrained("facebook/detr-resnet-50")
```

الخيار 2: تهيئة نموذج DETR بأوزان مُعلمة مسبقًا للشبكة العصبية التعاقبية، ولكن بأوزان مُعلمة مسبقًا لمحول الترميز وفك الترميز

```py
>>> from transformers import DetrConfig, DetrForObjectDetection

>>> config = DetrConfig()
>>> model = DetrForObjectDetection(config)
```

الخيار 3: تهيئة نموذج DETR بأوزان مُعلمة مسبقًا للشبكة العصبية التعاقبية + محول الترميز وفك الترميز

```py
>>> config = DetrConfig(use_pretrained_backbone=False)
>>> model = DetrForObjectDetection(config)
```

كملخص، ضع في اعتبارك الجدول التالي:

| المهمة | الكشف عن الأشياء | تجزئة المثيل | التجزئة الشاملة |
|------|------------------|-----------------------|-----------------------|
| **الوصف** | التنبؤ بحدود الإحداثيات وتصنيفات الفئات حول الأشياء في صورة | التنبؤ بأقنعة حول الأشياء (أي المثيلات) في صورة | التنبؤ بأقنعة حول كل من الأشياء (أي المثيلات) وكذلك "الأشياء" (أي أشياء الخلفية مثل الأشجار والطرق) في صورة |
| **النموذج** | [`~transformers.DetrForObjectDetection`] | [`~transformers.DetrForSegmentation`] | [`~transformers.DetrForSegmentation`] |
| **مجموعة البيانات النموذجية** | COCO detection | COCO detection، COCO panoptic | COCO panoptic |
| **تنسيق التعليقات التوضيحية لتوفيرها إلى** [`~transformers.DetrImageProcessor`] | {'image_id': `int`، 'annotations': `List [Dict]`} كل Dict عبارة عن تعليق توضيحي لكائن COCO | {'image_id': `int`، 'annotations': `List [Dict]`} (في حالة الكشف عن COCO) أو {'file_name': `str`، 'image_id': `int`، 'segments_info': `List [Dict]`} (في حالة COCO panoptic) | {'file_name': `str`، 'image_id': `int`، 'segments_info': `List [Dict]`} و masks_path (مسار إلى الدليل الذي يحتوي على ملفات PNG للأقنعة) |
| **ما بعد المعالجة** (أي تحويل إخراج النموذج إلى تنسيق Pascal VOC) | [`~transformers.DetrImageProcessor.post_process`] | [`~transformers.DetrImageProcessor.post_process_segmentation`] | [`~transformers.DetrImageProcessor.post_process_segmentation`]`، [`~transformers.DetrImageProcessor.post_process_panoptic`] |
| **المقيمون** | `CocoEvaluator` مع `iou_types="bbox"` | `CocoEvaluator` مع `iou_types="bbox"` أو `"segm"` | `CocoEvaluator` مع `iou_tupes="bbox"` أو `"segm"`، `PanopticEvaluator` |

باختصار، يجب إعداد البيانات بتنسيق COCO detection أو COCO panoptic، ثم استخدام [`~transformers.DetrImageProcessor`] لإنشاء `pixel_values`، `pixel_mask`، والتعليقات التوضيحية الاختيارية `labels`، والتي يمكن بعد ذلك استخدامها لتدريب (أو ضبط دقيق) نموذج. للتقويم، يجب أولاً تحويل مخرجات النموذج باستخدام إحدى طرق ما بعد المعالجة من [`~transformers.DetrImageProcessor`]. يمكن بعد ذلك توفير هذه المخرجات إلى `CocoEvaluator` أو `PanopticEvaluator`، والتي تتيح لك حساب مقاييس مثل متوسط الدقة (mAP) والجودة الشاملة (PQ). يتم تنفيذ هذه الكائنات في [المستودع الأصلي](https://github.com/facebookresearch/detr). راجع [دفاتر الملاحظات التوضيحية](https://github.com/NielsRogge/Transformers-Tutorials/tree/master/DETR) للحصول على مزيد من المعلومات حول التقييم.
## الموارد

قائمة بموارد Hugging Face الرسمية وموارد المجتمع (يشار إليها برمز 🌎) لمساعدتك في البدء مع DETR.
<PipelineTag pipeline="object-detection"/>

- يمكن العثور على جميع دفاتر الملاحظات التوضيحية للمثال التي توضح الضبط الدقيق لـ [`DetrForObjectDetection`] و [`DetrForSegmentation`] على مجموعة بيانات مخصصة [هنا](https://github.com/NielsRogge/Transformers-Tutorials/tree/master/DETR).

- يمكن العثور على البرامج النصية للضبط الدقيق لـ [`DetrForObjectDetection`] باستخدام [`Trainer`] أو [Accelerate](https://huggingface.co/docs/accelerate/index) [هنا](https://github.com/huggingface/transformers/tree/main/examples/pytorch/object-detection).

- راجع أيضًا: [دليل مهام الكشف عن الأشياء](../tasks/object_detection).

إذا كنت مهتمًا بتقديم مورد لإدراجه هنا، فيرجى فتح طلب سحب وسنقوم بمراجعته! ويفضل أن يظهر المورد شيئًا جديدًا بدلاً من تكرار مورد موجود.

## DetrConfig

[[autodoc]] DetrConfig

## DetrImageProcessor

[[autodoc]] DetrImageProcessor

- preprocess

- post_process_object_detection

- post_process_semantic_segmentation

- post_process_instance_segmentation

- post_process_panoptic_segmentation

## DetrFeatureExtractor

[[autodoc]] DetrFeatureExtractor

- __call__

- post_process_object_detection

- post_process_semantic_segmentation

- post_process_instance_segmentation

- post_process_panoptic_segmentation

## المخرجات الخاصة بـ DETR

[[autodoc]] models.detr.modeling_detr.DetrModelOutput

[[autodoc]] models.detr.modeling_detr.DetrObjectDetectionOutput

[[autodoc]] models.detr.modeling_detr.DetrSegmentationOutput

## DetrModel

[[autodoc]] DetrModel

- forward

## DetrForObjectDetection

[[autodoc]] DetrForObjectDetection

- forward

## DetrForSegmentation

[[autodoc]] DetrForSegmentation

- forward