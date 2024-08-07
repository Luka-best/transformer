# BEiT

## نظرة عامة
اقترح Hangbo Bao و Li Dong و Furu Wei نموذج BEiT في ورقتهم البحثية بعنوان "BEiT: BERT Pre-Training of Image Transformers". مستوحى من BERT، تعد BEiT أول ورقة بحثية تجعل التعلم الذاتي المسبق لـ Vision Transformers (ViTs) يتفوق على التعلم المُراقب المسبق. بدلاً من تدريب النموذج مسبقًا للتنبؤ بفئة الصورة (كما هو الحال في ورقة ViT الأصلية)، يتم تدريب نماذج BEiT مسبقًا للتنبؤ بالرموز المرئية من كتاب الرموز الخاص بنموذج DALL-E من OpenAI بالنظر إلى الرقع المقنعة.

ملخص الورقة البحثية هو كما يلي:

"نقدم نموذج تمثيل الرؤية ذاتي الإشراف BEiT، والذي يعني Bidirectional Encoder representation from Image Transformers. واقتداءً بنموذج BERT الذي تم تطويره في مجال معالجة اللغات الطبيعية، نقترح مهمة نمذجة الصور المقنعة لتدريب نماذج Vision Transformers مسبقًا. على وجه التحديد، لكل صورة في مرحلة ما قبل التدريب لدينا وجهتا نظر، أي رقع الصور (مثل 16x16 بكسل)، والرموز المرئية (أي الرموز المتقطعة). أولاً، نقوم "بتقسيم" الصورة الأصلية إلى رموز مرئية. ثم نقوم بتعمية بعض رقع الصور بشكل عشوائي وإدخالها في محول الترميز. يتمثل الهدف من مرحلة ما قبل التدريب في استعادة الرموز المرئية الأصلية بناءً على رقع الصور المعيبة. بعد مرحلة ما قبل التدريب لـ BEiT، نقوم بتعديل دقيق لمعلمات النموذج مباشرة على مهام التدفق السفلي عن طريق إضافة طبقات المهام فوق المشفر المُدرب مسبقًا. تُظهر النتائج التجريبية على تصنيف الصور والتجزئة الدلالية أن نموذجنا يحقق نتائج تنافسية مع طرق التدريب المسبق السابقة. على سبيل المثال، يحقق BEiT بحجم قاعدة دقة 83.2٪ على ImageNet-1K، متغلبًا بشكل كبير على تدريب DeiT من الصفر (81.8٪) بنفس الإعداد. علاوة على ذلك، يحصل BEiT بحجم كبير على 86.3٪ باستخدام ImageNet-1K فقط، متفوقًا حتى على ViT-L مع التدريب الخاضع للإشراف على ImageNet-22K (85.2٪)".

تمت المساهمة بهذا النموذج من قبل [nielsr](https://huggingface.co/nielsr). تمت المساهمة بإصدار JAX/FLAX من هذا النموذج بواسطة [kamalkraj](https://huggingface.co/kamalkraj). يمكن العثور على الكود الأصلي [هنا](https://github.com/microsoft/unilm/tree/master/beit).

## نصائح الاستخدام

- تعد نماذج BEiT محولات رؤية عادية، ولكنها مدربة ذاتيًا بدلاً من التدريب الخاضع للإشراف. إنها تتفوق على كل من النموذج الأصلي (ViT) وكذلك محولات الصور الفعالة للبيانات (DeiT) عند ضبطها الدقيق على ImageNet-1K و CIFAR-100. يمكنك الاطلاع على دفاتر الملاحظات التجريبية المتعلقة بالاستدلال وكذلك الضبط الدقيق على البيانات المخصصة [هنا](https://github.com/NielsRogge/Transformers-Tutorials/tree/master/VisionTransformer) (يمكنك ببساطة استبدال [`ViTFeatureExtractor`] بـ [`BeitImageProcessor`] و [`ViTForImageClassification`] بـ [`BeitForImageClassification`]).

- هناك أيضًا دفتر ملاحظات توضيحي متاح يوضح كيفية دمج محول رموز الصور الخاص بنموذج DALL-E مع BEiT لأداء نمذجة الصور المقنعة. يمكنك العثور عليه [هنا](https://github.com/NielsRogge/Transformers-Tutorials/tree/master/BEiT).

- نظرًا لأن نماذج BEiT تتوقع أن يكون لكل صورة نفس الحجم (الدقة)، فيمكن استخدام [`BeitImageProcessor`] لتصغير حجم الصور (أو تغيير مقياسها) وتطبيعها للنموذج.

- يتم عكس كل من دقة الرقع ودقة الصورة المستخدمة أثناء التدريب المسبق أو الضبط الدقيق في اسم كل نقطة تفتيش. على سبيل المثال، يشير `microsoft/beit-base-patch16-224` إلى بنية بحجم قاعدة بدقة رقعة 16x16 ودقة ضبط دقيق 224x224. يمكن العثور على جميع نقاط التفتيش على [المركز](https://huggingface.co/models?search=microsoft/beit).

- نقاط التفتيش المتاحة هي إما (1) مدربة مسبقًا على ImageNet-22k (مجموعة من 14 مليون صورة و 22 ألف فئة)، أو (2) أيضًا ضبط دقيق على ImageNet-22k أو (3) أيضًا ضبط دقيق على ImageNet-1k (المعروف أيضًا باسم ILSVRC 2012، وهو عبارة عن مجموعة من 1.3 مليون صورة و 1000 فئة).

- يستخدم BEiT تضمينات الموضع النسبي، مستوحاة من نموذج T5. خلال مرحلة ما قبل التدريب، قام المؤلفون بمشاركة الانحياز الموضعي النسبي بين طبقات الاهتمام الذاتي المتعددة. خلال الضبط الدقيق، يتم تهيئة انحياز الموضع النسبي لكل طبقة باستخدام انحياز الموضع النسبي المشترك الذي تم الحصول عليه بعد مرحلة ما قبل التدريب. لاحظ أنه إذا أراد المرء تدريب نموذج من الصفر، فيجب عليه إما تعيين `use_relative_position_bias` أو `use_relative_position_bias` من [`BeitConfig`] إلى `True` لإضافة تضمينات الموضع.

<img src="https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/transformers/model_doc/beit_architecture.jpg" alt="drawing" width="600"/>

<small> مرحلة ما قبل التدريب BEiT. مأخوذة من <a href="https://arxiv.org/abs/2106.08254">الورقة البحثية الأصلية.</a> </small>

## الموارد

قائمة بموارد Hugging Face الرسمية وموارد المجتمع (المشار إليها بـ 🌎) لمساعدتك في البدء باستخدام BEiT.

<PipelineTag pipeline="image-classification"/>

- [`BeitForImageClassification`] مدعوم بواسطة [نص برمجي توضيحي](https://github.com/huggingface/transformers/tree/main/examples/pytorch/image-classification) و [دفتر ملاحظات](https://colab.research.google.com/github/huggingface/notebooks/blob/main/examples/image_classification.ipynb).

- راجع أيضًا: [دليل مهام تصنيف الصور](../tasks/image_classification)

**التجزئة الدلالية**

- [دليل مهام التجزئة الدلالية](../tasks/semantic_segmentation)

إذا كنت مهتمًا بتقديم مورد لإدراجه هنا، فالرجاء فتح طلب سحب Pull Request وسنقوم بمراجعته! يجب أن يُظهر المورد المثالي شيئًا جديدًا بدلاً من تكرار مورد موجود.

## المخرجات المحددة لـ BEiT

[[autodoc]] models.beit.modeling_beit.BeitModelOutputWithPooling

[[autodoc]] models.beit.modeling_flax_beit.FlaxBeitModelOutputWithPooling

## BeitConfig

[[autodoc]] BeitConfig

## BeitFeatureExtractor

[[autodoc]] BeitFeatureExtractor

- __call__

- post_process_semantic_segmentation

## BeitImageProcessor

[[autodoc]] BeitImageProcessor

- preprocess

- post_process_semantic_segmentation

<frameworkcontent>
<pt>

## BeitModel

[[autodoc]] BeitModel

- forward

## BeitForMaskedImageModeling

[[autodoc]] BeitForMaskedImageModeling

- forward

## BeitForImageClassification

[[autodoc]] BeitForImageClassification

- forward

## BeitForSemanticSegmentation

[[autodoc]] BeitForSemanticSegmentation

- forward

</pt>
<jax>

## FlaxBeitModel

[[autodoc]] FlaxBeitModel

- __call__

## FlaxBeitForMaskedImageModeling

[[autodoc]] FlaxBeitForMaskedImageModeling

- __call__

## FlaxBeitForImageClassification

[[autodoc]] FlaxBeitForImageClassification

- __call__

</jax>
</frameworkcontent>