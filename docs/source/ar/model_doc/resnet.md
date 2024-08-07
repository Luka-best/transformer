# ResNet

## نظرة عامة

تم اقتراح نموذج ResNet في ورقة "Deep Residual Learning for Image Recognition" بواسطة Kaiming He وآخرون. ويتبع تنفيذنا التغييرات الطفيفة التي أجرتها Nvidia، حيث نطبق `stride=2` للتصغير في طبقة التحويل '3x3' في عنق الزجاجة وليس في طبقة '1x1' الأولى. ويشار إلى هذا عادة باسم "ResNet v1.5".

قدمت ResNet اتصالات باقية، والتي تسمح بتدريب الشبكات مع عدد غير مسبوق من الطبقات (حتى 1000). وفازت ResNet بمسابقة ILSVRC & COCO لعام 2015، والتي تعد معلمًا مهمًا في رؤية الكمبيوتر.

وفيما يلي الملخص المستخرج من الورقة:

*من الصعب تدريب الشبكات العصبية العميقة. نقدم إطارًا للتعلم الباقي لتخفيف تدريب الشبكات التي تكون أعمق بكثير من تلك المستخدمة سابقًا. نعيد صياغة الطبقات صراحةً على أنها دوال باقية التعلم مع الإشارة إلى مدخلات الطبقة، بدلاً من دالات غير مرجعية. نقدم أدلة تجريبية شاملة تُظهر أن هذه الشبكات الباقية أسهل في التحسين، ويمكنها اكتساب الدقة من العمق المتزايد بشكل كبير. وعلى مجموعة بيانات ImageNet، نقيم الشبكات الباقية بعمق يصل إلى 152 طبقة - أي 8 مرات أعمق من شبكات VGG ولكنها لا تزال ذات تعقيد أقل. حققت مجموعة من هذه الشبكات الباقية خطأ بنسبة 3.57% على مجموعة اختبار ImageNet. وفازت هذه النتيجة بالمركز الأول في مسابقة ILSVRC 2015 للتصنيف. كما نقدم تحليلًا لـ CIFAR-10 مع 100 و1000 طبقة.*

*يعد عمق التمثيلات ذو أهمية مركزية للعديد من مهام التعرف البصري. وبسبب تمثيلاتنا العميقة للغاية فقط، نحصل على تحسن نسبي بنسبة 28% في مجموعة بيانات COCO للكشف عن الأشياء. الشبكات الباقية العميقة هي أساس مشاركاتنا في مسابقتي ILSVRC & COCO 2015، حيث فزنا أيضًا بالمراكز الأولى في مهام الكشف عن ImageNet وتحديد موقعها، والكشف عن COCO، والتجزئة COCO.*

يوضح الشكل أدناه بنية ResNet. مأخوذة من [الورقة الأصلية](https://arxiv.org/abs/1512.03385).

<img width="600" src="https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/resnet_architecture.png"/>

تمت المساهمة بهذا النموذج بواسطة [Francesco](https://huggingface.co/Francesco). تمت إضافة إصدار TensorFlow من هذا النموذج بواسطة [amyeroberts](https://huggingface.co/amyeroberts). يمكن العثور على الكود الأصلي [هنا](https://github.com/KaimingHe/deep-residual-networks).

## الموارد

قائمة بموارد Hugging Face الرسمية والمجتمعية (مشار إليها بـ 🌎) لمساعدتك في البدء باستخدام ResNet.

<PipelineTag pipeline="image-classification"/>

- [`ResNetForImageClassification`] مدعوم بواسطة [نص البرنامج النصي](https://github.com/huggingface/transformers/tree/main/examples/pytorch/image-classification) و [دفتر الملاحظات](https://colab.research.google.com/github/huggingface/notebooks/blob/main/examples/image_classification.ipynb) هذا.

- راجع أيضًا: [دليل مهمة التصنيف الصوري](../tasks/image_classification)

إذا كنت مهتمًا بتقديم مورد لإدراجه هنا، فيرجى فتح طلب سحب وسنراجعه! يجب أن يُظهر المورد بشكل مثالي شيئًا جديدًا بدلاً من تكرار مورد موجود.

## ResNetConfig

[[autodoc]] ResNetConfig

<frameworkcontent>
<pt>

## ResNetModel

[[autodoc]] ResNetModel

- forward

## ResNetForImageClassification

[[autodoc]] ResNetForImageClassification

- forward

</pt>
<tf>

## TFResNetModel

[[autodoc]] TFResNetModel

- call

## TFResNetForImageClassification

[[autodoc]] TFResNetForImageClassification

- call

</tf>
<jax>

## FlaxResNetModel

[[autodoc]] FlaxResNetModel

- __call__

## FlaxResNetForImageClassification

[[autodoc]] FlaxResNetForImageClassification

- __call__

</jax>
</frameworkcontent>