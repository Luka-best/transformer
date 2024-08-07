# محول الانتباه المجاور

<Tip warning={true}>  
هذا النموذج في وضع الصيانة فقط، ولا نقبل أي طلبات سحب جديدة لتغيير شفرته.
إذا واجهتك أي مشكلات أثناء تشغيل هذا النموذج، يرجى إعادة تثبيت الإصدار الأخير الذي يدعم هذا النموذج: v4.40.2.
يمكنك القيام بذلك عن طريق تشغيل الأمر التالي: `pip install -U transformers==4.40.2`.  
</Tip>

## نظرة عامة

اقتُرح NAT في [محول الانتباه المجاور](https://arxiv.org/abs/2204.07143)
من قبل علي حساني، وستيفن والتون، وجيا تشن لي، وشين لي، وهامفري شي.
إنه محول رؤية هرمي يعتمد على انتباه الجوار، وهو نمط انتباه ذاتي للنافذة المنزلقة.
المقتطف من الورقة هو كما يلي:

*نقدم Neighborhood Attention (NA)، وهو أول آلية انتباه منزلق فعالة وقابلة للتطوير للرؤية.
NA هي عملية لكل بكسل، وتحديد موقع الاهتمام الذاتي (SA) لأقرب بكسلات مجاورة، وبالتالي فهو يتمتع
تعقيد خطي للوقت والمساحة مقارنة بالتعقيد التربيعي لـ SA. يسمح نمط النافذة المنزلقة لمجال استقبال NA
بالنمو دون الحاجة إلى تحولات بكسل إضافية، ويحافظ على التكافؤ الترجمي، على عكس
محول نافذة الاهتمام الذاتي (WSA) في محول Swin. نقوم بتطوير NATTEN (Neighborhood Attention Extension)، وهي حزمة Python
مع نوى C++ و CUDA فعالة، والتي تسمح لـ NA بالعمل بشكل أسرع بنسبة تصل إلى 40% من WSA في Swin مع استخدام ما يصل إلى 25% أقل
الذاكرة. نقدم أيضًا محول الانتباه المجاور (NAT)، وهو تصميم محول هرمي جديد يعتمد على NA
التي تعزز أداء تصنيف الصور والرؤية لأسفل البئر. النتائج التجريبية على NAT تنافسية؛
يصل NAT-Tiny إلى 83.2% دقة أعلى على ImageNet، و 51.4% mAP على MS-COCO و 48.4% mIoU على ADE20K، وهو ما يمثل 1.9%
تحسين دقة ImageNet، و 1.0% mAP لـ COCO، و 2.6% mIoU لـ ADE20K على نموذج Swin بحجم مماثل. *

<img
src="https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/neighborhood-attention-pattern.jpg"
alt="drawing" width="600"/>

<small> انتباه الجوار مقارنة بأنماط الاهتمام الأخرى.
مأخوذ من <a href="https://arxiv.org/abs/2204.07143">الورقة الأصلية</a>.</small>

تمت المساهمة بهذا النموذج من قبل [علي حساني](https://huggingface.co/alihassanijr).
يمكن العثور على الكود الأصلي [هنا](https://github.com/SHI-Labs/Neighborhood-Attention-Transformer).

## نصائح الاستخدام

- يمكن للمرء استخدام واجهة برمجة التطبيقات [`AutoImageProcessor`] لتحضير الصور للنموذج.
- يمكن استخدام NAT كـ *عمود فقري*. عندما `output_hidden_states = True`،
سيقوم بإخراج كل من `hidden_states` و `reshaped_hidden_states`.
يكون لـ `reshaped_hidden_states` شكل `(batch، num_channels، height، width)` بدلاً من
`(batch_size، height، width، num_channels)`.

ملاحظات:

- يعتمد NAT على تنفيذ [NATTEN](https://github.com/SHI-Labs/NATTEN/) لانتباه الجوار.
يمكنك تثبيته بعجلات مسبقة البناء لنظام Linux عن طريق الرجوع إلى [shi-labs.com/natten](https://shi-labs.com/natten)،
أو قم بالبناء على نظامك عن طريق تشغيل `pip install natten`.
يرجى ملاحظة أن هذا الأخير سيستغرق وقتًا طويلاً لتجميع NATTEN. لا تدعم NATTEN أجهزة Windows بعد.
- حجم التصحيح 4 هو الوحيد المدعوم في الوقت الحالي.

## الموارد

قائمة بموارد Hugging Face الرسمية وموارد المجتمع (مشار إليها برمز 🌎) لمساعدتك في البدء باستخدام NAT.

<PipelineTag pipeline="image-classification"/>

- مدعوم من [`NatForImageClassification`] بواسطة [نص برمجي توضيحي](https://github.com/huggingface/transformers/tree/main/examples/pytorch/image-classification) و [دفتر الملاحظات](https://colab.research.google.com/github/huggingface/notebooks/blob/main/examples/image_classification.ipynb).
- راجع أيضًا: [دليل مهام تصنيف الصور](../tasks/image_classification)

إذا كنت مهتمًا بتقديم مورد لإدراجه هنا، فالرجاء فتح طلب سحب وسنراجعه! يجب أن يوضح المورد بشكل مثالي شيء جديد بدلاً من تكرار مورد موجود.

## NatConfig

[[autodoc]] NatConfig

## NatModel

[[autodoc]] NatModel

- forward

## NatForImageClassification

[[autodoc]] NatForImageClassification

- forward