# RegNet

## نظرة عامة

اقترح نموذج RegNet في ورقة "تصميم مساحات تصميم الشبكات" من قبل إيليا رادوسافوفيتش، وراج براتيك كوساراجو، وروس جيرشيك، وكايمينغ هي، وبيتر دولار.

يصمم المؤلفون مساحات بحث لأداء البحث المعماري للشبكات العصبية. حيث يبدأون من مساحة بحث ذات أبعاد عالية ويقللون تدريجيًا من مساحة البحث من خلال التطبيق التجريبي للقيود بناءً على أفضل النماذج أداءً التي تم أخذ عينات منها بواسطة مساحة البحث الحالية.

ملخص الورقة هو كما يلي:

"في هذا العمل، نقدم نموذجًا جديدًا لتصميم الشبكات. هدفنا هو المساعدة في تقدم فهم تصميم الشبكة واستكشاف مبادئ التصميم التي تعمم عبر الإعدادات. بدلاً من التركيز على تصميم حالات شبكة فردية، نقوم بتصميم مساحات تصميم الشبكة التي تحدد بارامترات مجموعات الشبكات. العملية الشاملة مماثلة لتصميم الشبكات اليدوي الكلاسيكي، ولكنها مرفوعة إلى مستوى مساحة التصميم. باستخدام منهجيتنا، نستكشف الجانب الهيكلي لتصميم الشبكة ونصل إلى مساحة تصميم منخفضة الأبعاد تتكون من شبكات منتظمة وبسيطة نسميها RegNet. البصيرة الأساسية لمعلمة RegNet بسيطة بشكل مدهش: يمكن تفسير العروض والعمق للشبكات الجيدة بواسطة دالة خطية كمية. نقوم بتحليل مساحة تصميم RegNet ونصل إلى نتائج مثيرة للاهتمام لا تتطابق مع الممارسة الحالية لتصميم الشبكة. توفر مساحة تصميم RegNet شبكات بسيطة وسريعة تعمل بشكل جيد عبر مجموعة واسعة من أنظمة الفلوب. في ظل إعدادات التدريب المماثلة والعمليات العائمة المماثلة، تفوق نماذج RegNet نماذج EfficientNet الشهيرة بينما تكون أسرع 5 مرات على وحدات معالجة الرسومات."

ساهم في هذا النموذج [فرانشيسكو](https://huggingface.co/Francesco). تمت المساهمة في نسخة TensorFlow من النموذج من قبل [sayakpaul](https://huggingface.co/sayakpaul) و [ariG23498](https://huggingface.co/ariG23498).

يمكن العثور على الكود الأصلي [هنا](https://github.com/facebookresearch/pycls).

النموذج الضخم 10B من "التعلم الذاتي للإشراف على الميزات المرئية في البرية" ، المدرب على مليار صورة من Instagram، متاح على [hub](https://huggingface.co/facebook/regnet-y-10b-seer).

## الموارد

قائمة بموارد Hugging Face الرسمية وموارد المجتمع (المشار إليها بـ 🌎) لمساعدتك في البدء باستخدام RegNet.

<PipelineTag pipeline="image-classification"/>

- [`RegNetForImageClassification`] مدعوم بواسطة [نص البرنامج النصي](https://github.com/huggingface/transformers/tree/main/examples/pytorch/image-classification) و [دفتر الملاحظات](https://colab.research.google.com/github/huggingface/notebooks/blob/main/examples/image_classification.ipynb) هذا.

- راجع أيضًا: [دليل مهام التصنيف الصوري](../tasks/image_classification)

إذا كنت مهتمًا بتقديم مورد لإدراجه هنا، فالرجاء فتح طلب سحب وسنراجعه! يجب أن يوضح المورد في الوضع المثالي شيئًا جديدًا بدلاً من تكرار مورد موجود.

## RegNetConfig

[[autodoc]] RegNetConfig

<frameworkcontent>
<pt>

## RegNetModel

[[autodoc]] RegNetModel

- forward

## RegNetForImageClassification

[[autodoc]] RegNetForImageClassification

- forward

</pt>
<tf>

## TFRegNetModel

[[autodoc]] TFRegNetModel

- call

## TFRegNetForImageClassification

[[autodoc]] TFRegNetForImageClassification

- call

</tf>
<jax>

## FlaxRegNetModel

[[autodoc]] FlaxRegNetModel

- __call__

## FlaxRegNetForImageClassification

[[autodoc]] FlaxRegNetForImageClassification

- __call__

</jax>
</frameworkcontent>