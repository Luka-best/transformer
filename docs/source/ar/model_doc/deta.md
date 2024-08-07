# DETA

> هذا النموذج في وضع الصيانة فقط، ولا نقبل أي طلبات سحب جديدة لتغيير شفرته. إذا واجهتك أي مشكلات أثناء تشغيل هذا النموذج، يرجى إعادة تثبيت الإصدار الأخير الذي يدعم هذا النموذج: v4.40.2. يمكنك القيام بذلك عن طريق تشغيل الأمر التالي: `pip install -U transformers==4.40.2`.

## نظرة عامة

اقترح نموذج DETA في ورقة بحثية بعنوان [NMS Strikes Back](https://arxiv.org/abs/2212.06137) من قبل Jeffrey Ouyang-Zhang وJang Hyun Cho وXingyi Zhou وPhilipp Krähenbühl.

يحسن DETA (اختصار لـ Detection Transformers with Assignment) [Deformable DETR](deformable_detr) عن طريق استبدال مطابقة Hungarian الثنائية المتماثلة بخسارة تعيين التسميات من واحد إلى كثير المستخدمة في أجهزة الكشف التقليدية مع الحد الأقصى لقمع غير أقصى (NMS). يؤدي هذا إلى مكاسب كبيرة تصل إلى 2.5 mAP.

الملخص من الورقة هو كما يلي:

> يحول محول الكشف (DETR) الاستعلامات مباشرة إلى كائنات فريدة من خلال استخدام المطابقة الثنائية المتماثلة أثناء التدريب ويمكّن الكشف عن الكائنات من النهاية إلى النهاية. مؤخرًا، تفوقت هذه النماذج على أجهزة الكشف التقليدية على COCO بأسلوب لا يمكن إنكاره. ومع ذلك، فإنها تختلف عن أجهزة الكشف التقليدية في العديد من التصميمات، بما في ذلك بنية النموذج وجداول التدريب، وبالتالي فإن فعالية المطابقة المتماثلة غير مفهومة تمامًا. في هذا العمل، نجري مقارنة صارمة بين المطابقة المتماثلة لـ Hungarian في DETRs وتعيينات التسميات من واحد إلى كثير في أجهزة الكشف التقليدية مع الإشراف غير الأقصى الأقصى (NMS). ومما يثير الدهشة أننا نلاحظ أن التعيينات من واحد إلى كثير مع NMS تتفوق باستمرار على المطابقة المتماثلة القياسية في نفس الإعداد، مع مكسب كبير يصل إلى 2.5 mAP. حقق مكتشفنا الذي يدرب Deformable-DETR مع تعيين التسمية المستندة إلى IoU 50.2 COCO mAP في غضون 12 فترة (جدول 1x) مع العمود الفقري ResNet50، متفوقًا على جميع أجهزة الكشف التقليدية أو القائمة على المحول الموجودة في هذا الإعداد. على مجموعات بيانات متعددة وجداول ومعماريات، نُظهر باستمرار أن المطابقة الثنائية غير ضرورية لمحولات الكشف القابلة للأداء. علاوة على ذلك، نعزو نجاح محولات الكشف إلى بنية المحول التعبيري.

<img src="https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/transformers/model_doc/deta_architecture.jpg" alt="drawing" width="600"/>

<small>نظرة عامة على DETA. مأخوذة من <a href="https://arxiv.org/abs/2212.06137">الورقة الأصلية</a>.</small>

تمت المساهمة بهذا النموذج من قبل [nielsr](https://huggingface.co/nielsr). يمكن العثور على الكود الأصلي [هنا](https://github.com/jozhang97/DETA).

## الموارد

قائمة بموارد Hugging Face الرسمية وموارد المجتمع (المشار إليها بـ 🌎) لمساعدتك في البدء باستخدام DETA.

- يمكن العثور على دفاتر الملاحظات التوضيحية لـ DETA [هنا](https://github.com/NielsRogge/Transformers-Tutorials/tree/master/DETA).
- يمكن العثور على البرامج النصية لتدريب النماذج الدقيقة [`DetaForObjectDetection`] مع [`Trainer`] أو [Accelerate](https://huggingface.co/docs/accelerate/index) [هنا](https://github.com/huggingface/transformers/tree/main/examples/pytorch/object-detection).
- راجع أيضًا: [دليل مهام الكشف عن الأشياء](../tasks/object_detection).

إذا كنت مهتمًا بتقديم مورد لإدراجه هنا، فالرجاء فتح طلب سحب وسنراجعه! يجب أن يُظهر المورد المثالي شيئًا جديدًا بدلاً من تكرار مورد موجود.

## DetaConfig

[[autodoc]] DetaConfig

## DetaImageProcessor

[[autodoc]] DetaImageProcessor

- preprocess
- post_process_object_detection

## DetaModel

[[autodoc]] DetaModel

- forward

## DetaForObjectDetection

[[autodoc]] DetaForObjectDetection

- forward