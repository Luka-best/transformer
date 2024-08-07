# محول اهتمام الحي المتمدد 

## نظرة عامة 

اقترح DiNAT في [محول اهتمام الحي المتمدد](https://arxiv.org/abs/2209.15001)
بواسطة علي حساني وهامفري شي.

يوسع NAT من خلال إضافة نمط اهتمام الحي المتمدد لالتقاط السياق العالمي،
ويظهر تحسينات أداء كبيرة عليه.

المستخلص من الورقة هو ما يلي:

> "تحول المحولات بسرعة إلى إحدى أكثر بنيات التعلم العميق تطبيقًا عبر الطرائق والمجالات والمهام. في الرؤية، بالإضافة إلى الجهود المستمرة في المحولات العادية، اكتسبت المحولات الهرمية أيضًا اهتمامًا كبيرًا، بفضل أدائها وسهولة دمجها في الأطر الحالية. عادةً ما تستخدم هذه النماذج آليات اهتمام محلية، مثل اهتمام الحي المنزلق أو اهتمام النافذة المنزلق لمحول Swin. في حين أن الاهتمام المحلي فعال في تقليل التعقيد التربيعي للاهتمام الذاتي، إلا أنه يضعف اثنتين من أكثر خصائص الاهتمام الذاتي المرغوبة: نمذجة التبعية البعيدة المدى، ومجال الاستقبال العالمي. في هذه الورقة، نقدم اهتمام الحي المتمدد (DiNA)، وهو امتداد طبيعي ومرن وفعال لـ NA يمكنه التقاط سياق عالمي أكثر وتوسيع حقول الاستقبال بشكل أسي دون أي تكلفة إضافية. يكمل اهتمام NA المحلي واهتمام DiNA العالمي النادر بعضهما البعض، وبالتالي نقدم محول اهتمام الحي المتمدد (DiNAT)، وهو محول رؤية هرمي جديد مبني على كليهما. تتمتع متغيرات DiNAT بتحسينات كبيرة على خطوط الأساس القوية مثل NAT وSwin وConvNeXt.

> إن نموذجنا الكبير أسرع ويتفوق على نظيره Swin بنسبة 1.5% box AP في اكتشاف كائن COCO، و1.3% mask AP في تجزئة مثيل COCO، و1.1% mIoU في تجزئة المشهد لـ ADE20K.

> وبالاقتران بأطر جديدة، فإن متغيرنا الكبير هو نموذج التجزئة الشاملة الجديد للدولة في الفن على COCO (58.2 PQ) وADE20K (48.5 PQ)، ونموذج تجزئة المثيل على Cityscapes (44.5 AP) وADE20K (35.4 AP) (بدون بيانات إضافية). كما أنه يتطابق مع أحدث النماذج المتخصصة في التجزئة الدلالية على ADE20K (58.2 mIoU)، ويحتل المرتبة الثانية على Cityscapes (84.5 mIoU) (بدون بيانات إضافية).

<img
src="https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/dilated-neighborhood-attention-pattern.jpg"
alt="drawing" width="600"/>

<small> اهتمام الحي مع قيم التمدد المختلفة.
مأخوذة من <a href="https://arxiv.org/abs/2209.15001">الورقة الأصلية</a>.</small>

تمت المساهمة بهذا النموذج من قبل [علي حساني](https://huggingface.co/alihassanijr).
يمكن العثور على الكود الأصلي [هنا](https://github.com/SHI-Labs/Neighborhood-Attention-Transformer).

## نصائح الاستخدام

يمكن استخدام DiNAT كـ *عمود فقري*. عندما `output_hidden_states = True`،
سيخرج كلا من `hidden_states` و`reshaped_hidden_states`. تحتوي `reshaped_hidden_states` على شكل `(batch، num_channels، height، width)` بدلاً من `(batch_size، height، width، num_channels)`.

ملاحظات:

- يعتمد DiNAT على تنفيذ اهتمام الحي واهتمام الحي المتمدد من [NATTEN](https://github.com/SHI-Labs/NATTEN/).
  يمكنك تثبيته باستخدام العجلات المسبقة البناء لـ Linux بالرجوع إلى [shi-labs.com/natten](https://shi-labs.com/natten)، أو البناء على نظامك عن طريق تشغيل `pip install natten`.
  لاحظ أن هذا الأمر سيستغرق وقتًا طويلاً لتجميع NATTEN ولا يدعم أجهزة Windows بعد.
- حجم التصحيح 4 هو الحجم الوحيد المدعوم في الوقت الحالي.

## الموارد

قائمة بموارد Hugging Face الرسمية وموارد المجتمع (مشار إليها بـ 🌎) لمساعدتك في البدء باستخدام DiNAT.

<PipelineTag pipeline="image-classification"/>

- [`DinatForImageClassification`] مدعوم بواسطة [نص البرنامج النصي](https://github.com/huggingface/transformers/tree/main/examples/pytorch/image-classification) و [دفتر الملاحظات](https://colab.research.google.com/github/huggingface/notebooks/blob/main/examples/image_classification.ipynb) هذا.
- راجع أيضًا: [دليل مهمة تصنيف الصور](../tasks/image_classification)

إذا كنت مهتمًا بتقديم مورد لإدراجه هنا، فالرجاء فتح طلب سحب وسنراجعه! يجب أن يُظهر المورد بشكل مثالي شيئًا جديدًا بدلاً من تكرار مورد موجود.

## DinatConfig

[[autodoc]] DinatConfig

## DinatModel

[[autodoc]] DinatModel

- forword

## DinatForImageClassification

[[autodoc]] DinatForImageClassification

- forword