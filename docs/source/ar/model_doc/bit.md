# Big Transfer (BiT)

## نظرة عامة

اقتُرح نموذج BiT في ورقة "Big Transfer (BiT): General Visual Representation Learning" من قبل Alexander Kolesnikov و Lucas Beyer و Xiaohua Zhai و Joan Puigcerver و Jessica Yung و Sylvain Gelly و Neil Houlsby.

BiT هي وصفة بسيطة لزيادة حجم التدريب المسبق لتصميمات [ResNet](resnet)-like (تحديدًا، ResNetv2). وتؤدي هذه الطريقة إلى تحسينات كبيرة في التعلم بالنقل.

ملخص الورقة هو كما يلي:

*يُحسِّن نقل التمثيلات المُدربة مسبقًا من كفاءة العينات ويبسط ضبط فرط المعلمات عند تدريب الشبكات العصبية العميقة للرؤية. نعيد النظر في نموذج التدريب المسبق على مجموعات البيانات المُشرفة الكبيرة وضبط دقة النموذج على مهمة مستهدفة. نقوم بزيادة حجم التدريب المسبق، ونقترح وصفة بسيطة نسميها Big Transfer (BiT). من خلال الجمع بين بعض المكونات المختارة بعناية، ونقل باستخدام قاعدة بسيطة، نحقق أداءً قويًا في أكثر من 20 مجموعة بيانات. يعمل BiT بشكل جيد عبر مجموعة واسعة بشكل مدهش من أنظمة البيانات - من مثال واحد لكل فئة إلى 1 مليون مثال إجمالي. يحقق BiT دقة أعلى-1 بنسبة 87.5٪ على ILSVRC-2012، و 99.4٪ على CIFAR-10، و 76.3٪ على مقياس Visual Task Adaptation Benchmark (VTAB) المكون من 19 مهمة. وفيما يتعلق بمجموعات البيانات الصغيرة، يحصل BiT على 76.8٪ على ILSVRC-2012 مع 10 أمثلة لكل فئة، و 97.0٪ على CIFAR-10 مع 10 أمثلة لكل فئة. نقوم بتحليل مفصل للمكونات الرئيسية التي تؤدي إلى أداء نقل عالي.*

تمت المساهمة بهذا النموذج من قبل [nielsr](https://huggingface.co/nielsr).

يمكن العثور على الكود الأصلي [هنا](https://github.com/google-research/big_transfer).

## نصائح الاستخدام

- تُعد نماذج BiT مكافئة لتصميم ResNetv2 من حيث البنية، باستثناء ما يلي: 1) يتم استبدال جميع طبقات التوحيد المعياري للدفعات بـ [التوحيد المعياري للمجموعات](https://arxiv.org/abs/1803.08494)، 2) يتم استخدام [توحيد أوزان](https://arxiv.org/abs/1903.10520) الطبقات التلافيفية. يُظهر المؤلفون أن الجمع بين الاثنين مفيد للتدريب باستخدام أحجام دفعات كبيرة، وله تأثير كبير على التعلم بالنقل.

## الموارد

قائمة بموارد Hugging Face الرسمية وموارد المجتمع (المشار إليها بـ 🌎) لمساعدتك في البدء باستخدام BiT.

<PipelineTag pipeline="image-classification"/>

- [`BitForImageClassification`] مدعوم بواسطة [نص البرنامج النصي](https://github.com/huggingface/transformers/tree/main/examples/pytorch/image-classification) و [دفتر الملاحظات](https://colab.research.google.com/github/huggingface/notebooks/blob/main/examples/image_classification.ipynb) هذا.

- راجع أيضًا: [دليل مهمة تصنيف الصور](../tasks/image_classification)

إذا كنت مهتمًا بتقديم مورد لإدراجه هنا، فيرجى فتح طلب سحب وسنراجعه! يجب أن يُظهر المورد في الوضع المثالي شيئًا جديدًا بدلاً من تكرار مورد موجود.

## BitConfig

[[autodoc]] BitConfig

## BitImageProcessor

[[autodoc]] BitImageProcessor

- preprocess

## BitModel

[[autodoc]] BitModel

- forward

## BitForImageClassification

[[autodoc]] BitForImageClassification

- forward