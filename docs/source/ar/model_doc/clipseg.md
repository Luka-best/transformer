# CLIPSeg

## نظرة عامة
اقترح نموذج CLIPSeg في [Image Segmentation Using Text and Image Prompts](https://arxiv.org/abs/2112.10003) بواسطة تيمو لوديكي وألكسندر إيكر. يضيف CLIPSeg فك تشفير بسيطًا أعلى نموذج CLIP مجمد للتجزئة الصفرية والتجزئة الصورة الواحدة.

المستخلص من الورقة هو ما يلي:

*يتم عادةً معالجة تجزئة الصورة عن طريق تدريب نموذج لمجموعة ثابتة من فئات الكائنات. إن دمج فئات إضافية أو استفسارات أكثر تعقيدًا لاحقًا مكلف لأنه يتطلب إعادة تدريب النموذج على مجموعة بيانات تشمل هذه التعبيرات. نقترح هنا نظامًا يمكنه إنشاء تجزئات الصور بناءً على مطالبات تعسفية في وقت الاختبار. يمكن أن يكون المطالبة إما نصًا أو صورة. يمكّننا هذا النهج من إنشاء نموذج موحد (تم تدريبه مرة واحدة) لثلاث مهام تجزئة شائعة، والتي تأتي مع تحديات متميزة: تجزئة تعبير الإحالة، وتجزئة الصور الصفرية، وتجزئة الصور الواحدة.

نعتمد على نموذج CLIP كعمود فقري نقوم بتوسيع نطاقه باستخدام فك تشفير يعتمد على المحول الذي يمكّن التنبؤ الكثيف. بعد التدريب على إصدار موسع من مجموعة بيانات PhraseCut، يقوم نظامنا بتوليد خريطة تجزئة ثنائية لصورة بناءً على مطالبة نصية حرة أو على صورة إضافية تعبر عن الاستعلام. نقوم بتحليل متغيرات مختلفة من مطالبات الصور اللاحقة هذه بالتفصيل. يسمح هذا الإدخال الهجين الجديد بالتكيف الديناميكي ليس فقط مع مهام التجزئة الثلاث المذكورة أعلاه، ولكن مع أي مهمة تجزئة ثنائية يمكن صياغة استعلام نصي أو صورة لها. وأخيرًا، نجد أن نظامنا يتكيف جيدًا مع الاستفسارات العامة التي تنطوي على إمكانات أو خصائص*.

<img src="https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/transformers/model_doc/clipseg_architecture.png" alt="drawing" width="600"/>

<small>نظرة عامة على CLIPSeg. مأخوذة من <a href="https://arxiv.org/abs/2112.10003">الورقة الأصلية</a>.</small>

تمت المساهمة بهذا النموذج من قبل [nielsr](https://huggingface.co/nielsr). يمكن العثور على الكود الأصلي [هنا](https://github.com/timojl/clipseg).

## نصائح الاستخدام

- [`CLIPSegForImageSegmentation`] يضيف فك تشفير أعلى [`CLIPSegModel`]. هذا الأخير متطابق مع [`CLIPModel`].
- [`CLIPSegForImageSegmentation`] يمكنه إنشاء تجزئات الصور بناءً على مطالبات تعسفية في وقت الاختبار. يمكن أن يكون المطالبة إما نصًا (مقدمًا إلى النموذج على أنه `input_ids`) أو صورة (مقدمة إلى النموذج على أنها `conditional_pixel_values`). يمكنك أيضًا توفير تضمينات شرطية مخصصة (مقدمة إلى النموذج على أنها `conditional_embeddings`).

## الموارد

قائمة بموارد Hugging Face الرسمية وموارد المجتمع (المشار إليها بـ 🌎) لمساعدتك في البدء باستخدام CLIPSeg. إذا كنت مهتمًا بتقديم مورد لإدراجه هنا، فيرجى فتح طلب سحب وسنراجعه! يجب أن يوضح المورد بشكل مثالي شيء جديد بدلاً من تكرار مورد موجود.

<PipelineTag pipeline="image-segmentation"/>

- دفتر ملاحظات يوضح [تجزئة الصور الصفرية باستخدام CLIPSeg](https://github.com/NielsRogge/Transformers-Tutorials/blob/master/CLIPSeg/Zero_shot_image_segmentation_with_CLIPSeg.ipynb).

## CLIPSegConfig

[[autodoc]] CLIPSegConfig

- from_text_vision_configs

## CLIPSegTextConfig

[[autodoc]] CLIPSegTextConfig

## CLIPSegVisionConfig

[[autodoc]] CLIPSegVisionConfig

## CLIPSegProcessor

[[autodoc]] CLIPSegProcessor

## CLIPSegModel

[[autodoc]] CLIPSegModel

- forward
- get_text_features
- get_image_features

## CLIPSegTextModel

[[autodoc]] CLIPSegTextModel

- forward

## CLIPSegVisionModel

[[autodoc]] CLIPSegVisionModel

- forward

## CLIPSegForImageSegmentation

[[autodoc]] CLIPSegForImageSegmentation

- forward