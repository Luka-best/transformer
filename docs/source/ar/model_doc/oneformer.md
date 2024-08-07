# OneFormer

## نظرة عامة
تم اقتراح نموذج OneFormer في ورقة بحثية بعنوان [OneFormer: One Transformer to Rule Universal Image Segmentation](https://arxiv.org/abs/2211.06220) بواسطة Jitesh Jain وآخرون. OneFormer هو إطار عمل شامل لتجزئة الصور يمكن تدريبه على مجموعة بيانات بانوبتيك واحدة لأداء مهام التجزئة الدلالية والتجزئة مثيل والتجزئة الشاملة. يستخدم OneFormer رمز المهمة لتوجيه النموذج نحو المهمة قيد التركيز، مما يجعل البنية موجهة بالمهمة للتدريب وديناميكية المهمة للاستدلال.

![OneFormer Teaser](https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/transformers/model_doc/oneformer_teaser.png)

ملخص الورقة البحثية هو كما يلي:

> "توحيد تجزئة الصور ليس بمفهوم جديد. وتشمل المحاولات السابقة لتوحيد تجزئة الصور في العقود الماضية تحليل المشاهد والتجزئة الشاملة، وفي الآونة الأخيرة، معماريات بانوبتيك الجديدة. ومع ذلك، فإن مثل هذه المعماريات البانوبتيكية لا توحد حقًا تجزئة الصور لأنها تحتاج إلى تدريب فردي على التجزئة الدلالية أو تجزئة مثيل أو التجزئة الشاملة لتحقيق أفضل أداء. في الوضع المثالي، يجب تدريب الإطار الشامل حقًا مرة واحدة فقط وتحقيق أداء حالة ثابتة عبر جميع مهام تجزئة الصور الثلاثة. ولهذه الغاية، نقترح OneFormer، وهو إطار عمل شامل لتجزئة الصور يوحد التجزئة مع تصميم تدريب متعدد المهام. أولاً، نقترح استراتيجية تدريب مشتركة مشروطة بالمهمة تتيح التدريب على حقائق كل مجال (التجزئة الدلالية وتجزئة مثيل والتجزئة الشاملة) ضمن عملية تدريب متعددة المهام واحدة. ثانيًا، نقدم رمز مهمة لشرط نموذجنا على المهمة قيد التنفيذ، مما يجعل نموذجنا ديناميكيًا للمهمة لدعم التدريب والاستدلال متعدد المهام. ثالثًا، نقترح استخدام خسارة تباينية استعلام-نص أثناء التدريب لإنشاء تمييزات أفضل بين المهام والطبقات. من الجدير بالذكر أن نموذج OneFormer الفردي الخاص بنا يفوق نماذج Mask2Former المتخصصة عبر جميع مهام التجزئة الثلاثة على ADE20k وCityScapes وCOCO، على الرغم من تدريب الأخير على كل مهمة من المهام الثلاثة بشكل فردي بثلاثة أضعاف الموارد. مع ظهور العمود الفقري ConvNeXt وDiNAT، نشهد المزيد من التحسينات في الأداء. نعتقد أن OneFormer يمثل خطوة مهمة نحو جعل تجزئة الصور أكثر شمولاً وإتاحة."

توضح الصورة أدناه بنية OneFormer. مأخوذة من [الورقة البحثية الأصلية](https://arxiv.org/abs/2211.06220).

![OneFormer Architecture](https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/transformers/model_doc/oneformer_architecture.png)

تمت المساهمة بهذا النموذج من قبل [Jitesh Jain](https://huggingface.co/praeclarumjj3). يمكن العثور على الكود الأصلي [هنا](https://github.com/SHI-Labs/OneFormer).

## نصائح الاستخدام

- يتطلب OneFormer مدخلين أثناء الاستدلال: *الصورة* و*رمز المهمة*.
- أثناء التدريب، يستخدم OneFormer فقط التعليقات التوضيحية البانوبتيكية.
- إذا كنت تريد تدريب النموذج في بيئة موزعة عبر عدة عقد، فيجب تحديث وظيفة `get_num_masks` داخل فئة `OneFormerLoss` في `modeling_oneformer.py`. عند التدريب على عدة عقد، يجب تعيين هذا إلى متوسط عدد الأقنعة المستهدفة عبر جميع العقد، كما هو موضح في التنفيذ الأصلي [هنا](https://github.com/SHI-Labs/OneFormer/blob/33ebb56ed34f970a30ae103e786c0cb64c653d9a/oneformer/modeling/criterion.py#L287).
- يمكن استخدام [`OneFormerProcessor`] لتحضير صور الإدخال ومدخلات المهام للنموذج وأهداف النموذج الاختيارية. يدمج [`OneformerProcessor`] [`OneFormerImageProcessor`] و [`CLIPTokenizer`] في مثيل واحد لتحضير الصور وتشفير مدخلات المهام.
- للحصول على التجزئة النهائية، اعتمادًا على المهمة، يمكنك استدعاء [`~OneFormerProcessor.post_process_semantic_segmentation`] أو [`~OneFormerImageProcessor.post_process_instance_segmentation`] أو [`~OneFormerImageProcessor.post_process_panoptic_segmentation`]. يمكن حل المهام الثلاث جميعها باستخدام إخراج [`OneFormerForUniversalSegmentation`]، وتقبل التجزئة الشاملة حجة `label_ids_to_fuse` الاختيارية لدمج مثيلات الكائن المستهدف (مثل السماء) معًا.

## الموارد

قائمة بموارد Hugging Face الرسمية وموارد المجتمع (المشار إليها بـ 🌎) لمساعدتك في البدء باستخدام OneFormer.

- يمكن العثور على دفاتر الملاحظات التوضيحية المتعلقة بالاستدلال + الضبط الدقيق على بيانات مخصصة [هنا](https://github.com/NielsRogge/Transformers-Tutorials/tree/master/OneFormer).

إذا كنت مهتمًا بتقديم مورد لإدراجه هنا، فيرجى فتح طلب سحب وسنراجعه.

يجب أن يوضح المورد بشكل مثالي شيئًا جديدًا بدلاً من تكرار مورد موجود.

## المخرجات الخاصة بـ OneFormer

[[autodoc]] models.oneformer.modeling_oneformer.OneFormerModelOutput

[[autodoc]] models.oneformer.modeling_oneformer.OneFormerForUniversalSegmentationOutput

## OneFormerConfig

[[autodoc]] OneFormerConfig

## OneFormerImageProcessor

[[autodoc]] OneFormerImageProcessor

- preprocess
- encode_inputs
- post_process_semantic_segmentation
- post_process_instance_segmentation
- post_process_panoptic_segmentation

## OneFormerProcessor

[[autodoc]] OneFormerProcessor

## OneFormerModel

[[autodoc]] OneFormerModel

- forward

## OneFormerForUniversalSegmentation

[[autodoc]] OneFormerForUniversalSegmentation

- forward