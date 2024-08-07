# SegFormer

## نظرة عامة

اقترح نموذج SegFormer في ورقة "SegFormer: Simple and Efficient Design for Semantic Segmentation with Transformers" بواسطة Enze Xie وآخرون. يتكون النموذج من ترميز Transformer هرمي ورأس فك تشفير خفيف الوزن يعتمد بالكامل على MLP لتحقيق نتائج ممتازة في معايير تصنيف الصور مثل ADE20K وCityscapes.

الملخص من الورقة هو ما يلي:

> "نقدم SegFormer، وهو إطار عمل لتصنيف الصور البسيط والفعال والقوي الذي يوحد المحولات مع فك ترميز الإدراك متعدد الطبقات (MLP) خفيف الوزن. يتميز SegFormer بميزتين جذابتين: 1) يتكون SegFormer من ترميز محول هرمي هيكلي جديد ينتج ميزات متعددة المقاييس. لا يحتاج إلى ترميز الموضع، وبالتالي يتجنب الاستيفاء لرموز الموضعية التي تؤدي إلى انخفاض الأداء عندما يختلف القرار عند الاختبار عن التدريب. 2) يتجنب SegFormer فك الترميز المعقد. يقوم فك ترميز MLP المقترح بتجميع المعلومات من طبقات مختلفة، وبالتالي الجمع بين كل من الاهتمام المحلي والعالمي لتصيير تمثيلات قوية. نُظهر أن هذا التصميم البسيط والخفيف هو المفتاح لتصنيف الكفاءة على المحولات. نقوم بزيادة مقياس نهجنا للحصول على سلسلة من النماذج من SegFormer-B0 إلى SegFormer-B5، مما يحقق أداءً وكفاءة أفضل بكثير من النظائر السابقة. على سبيل المثال، يحقق SegFormer-B4 نسبة 50.3% mIoU على ADE20K مع 64 مليون معامل، وهو أصغر 5 مرات وأفضل بنسبة 2.2% من الطريقة الأفضل السابقة. ويحقق نموذجنا الأفضل، SegFormer-B5، نسبة 84.0% mIoU على مجموعة التحقق من Cityscapes ويظهر متانة ممتازة للتصنيف الصفري على Cityscapes-C."

يوضح الشكل أدناه بنية SegFormer. مأخوذة من الورقة الأصلية.

![بنية SegFormer](https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/segformer_architecture.png)

تمت المساهمة بهذا النموذج بواسطة [nielsr](https://huggingface.co/nielsr). تمت المساهمة في إصدار TensorFlow من النموذج بواسطة [sayakpaul](https://huggingface.co/sayakpaul). يمكن العثور على الكود الأصلي [هنا](https://github.com/NVlabs/SegFormer).

## نصائح الاستخدام

- يتكون SegFormer من ترميز محول هرمي ورأس فك تشفير خفيف الوزن يعتمد بالكامل على MLP. [`SegformerModel`] هو ترميز المحول الهرمي (الذي يشار إليه أيضًا في الورقة باسم Mix Transformer أو MiT). يضيف [`SegformerForSemanticSegmentation`] رأس فك تشفير MLP بالكامل لأداء التصنيف الدلالي للصور. بالإضافة إلى ذلك، هناك [`SegformerForImageClassification`] الذي يمكن استخدامه - كما هو متوقع - لتصنيف الصور. قام مؤلفو SegFormer أولاً بتدريب المحول الترميزي مسبقًا على ImageNet-1k لتصنيف الصور. بعد ذلك، يقومون بحذف رأس التصنيف، واستبداله برأس فك تشفير MLP. بعد ذلك، يقومون بتدريب النموذج بالكامل على ADE20K وCityscapes وCOCO-stuff، والتي تعد معايير مرجعية مهمة لتصنيف الصور. يمكن العثور على جميع نقاط التفتيش على [المركز](https://huggingface.co/models?other=segformer).

- أسرع طريقة للبدء مع SegFormer هي التحقق من [دفاتر الملاحظات التوضيحية](https://github.com/NielsRogge/Transformers-Tutorials/tree/master/SegFormer) (التي تعرض كل من الاستدلال والتدريب الدقيق على البيانات المخصصة). يمكن للمرء أيضًا الاطلاع على [منشور المدونة](https://huggingface.co/blog/fine-tune-segformer) الذي يقدم SegFormer ويوضح كيفية ضبطه بدقة على بيانات مخصصة.

- يجب أن يشير مستخدمو TensorFlow إلى [هذا المستودع](https://github.com/deep-diver/segformer-tf-transformers) الذي يوضح الاستدلال والضبط الدقيق خارج الصندوق.

- يمكن للمرء أيضًا الاطلاع على [هذا العرض التوضيحي التفاعلي على Hugging Face Spaces](https://huggingface.co/spaces/chansung/segformer-tf-transformers) لتجربة نموذج SegFormer على الصور المخصصة.

- يعمل SegFormer مع أي حجم إدخال، حيث يقوم بتقسيم الإدخال ليكون قابلاً للقسمة على `config.patch_sizes`.

- يمكن للمرء استخدام [`SegformerImageProcessor`] لإعداد الصور وخرائط التجزئة المقابلة للنموذج. لاحظ أن معالج الصور هذا أساسي إلى حد ما ولا يتضمن جميع عمليات زيادة البيانات المستخدمة في الورقة الأصلية. يمكن العثور على خطوط المعالجة المسبقة الأصلية (لمجموعة بيانات ADE20k على سبيل المثال) [هنا](https://github.com/NVlabs/SegFormer/blob/master/local_configs/_base_/datasets/ade20k_repeat.py). تتمثل أهم خطوة للمعالجة المسبقة في اقتصاص الصور وخرائط التجزئة عشوائيًا وإضافتها إلى نفس الحجم، مثل 512x512 أو 640x640، ثم يتم تطبيعها.

- هناك شيء إضافي يجب مراعاته وهو أنه يمكن تهيئة [`SegformerImageProcessor`] باستخدام `do_reduce_labels` على `True` أو `False`. في بعض مجموعات البيانات (مثل ADE20k)، يتم استخدام الفهرس 0 في خرائط التجزئة المشروحة للخلفية. ومع ذلك، لا تتضمن مجموعة بيانات ADE20k فئة "الخلفية" في علاماتها البالغ عددها 150. لذلك، يتم استخدام `do_reduce_labels` لخفض جميع العلامات بمقدار 1، والتأكد من عدم حساب أي خسارة لفئة "الخلفية" (أي أنها تستبدل 0 في الخرائط المشروحة بـ 255، وهو *ignore_index* لدالة الخسارة المستخدمة بواسطة [`SegformerForSemanticSegmentation`]). ومع ذلك، تستخدم مجموعات بيانات أخرى الفهرس 0 كفئة خلفية وتتضمن هذه الفئة كجزء من جميع العلامات. في هذه الحالة، يجب تعيين `do_reduce_labels` على `False`، حيث يجب أيضًا حساب الخسارة لفئة الخلفية.

- مثل معظم النماذج، يأتي SegFormer بأحجام مختلفة، يمكن العثور على تفاصيلها في الجدول أدناه (مأخوذ من الجدول 7 من [الورقة الأصلية](https://arxiv.org/abs/2105.15203)).

| **متغير النموذج** | **الأعماق**    | **أحجام المخفية**    | **حجم مخفي فك الترميز** | **المعلمات (م)** | **ImageNet-1k Top 1** |
| :---------------: | ------------- | ------------------- | :---------------------: | :------------: | :-------------------: |
| MiT-b0            | [2، 2، 2، 2]  | [32، 64، 160، 256]  | 256                     | 3.7            | 70.5                  |
| MiT-b1            | [2، 2، 2، 2]  | [64، 128، 320، 512] | 256                     | 14.0           | 78.7                  |
| MiT-b2            | [3، 4، 6، 3]  | [64، 128، 320، 512] | 768                     | 25.4           | 81.6                  |
| MiT-b3            | [3، 4، 18، 3] | [64، 128، 320، 512] | 768                     | 45.2           | 83.1                  |
| MiT-b4            | [3، 8، 27، 3] | [64، 128، 320، 512] | 768                     | 62.6           | 83.6                  |
| MiT-b5            | [3، 6، 40، 3] | [64، 128، 320، 512] | 768                     | 82.0           | 83.8                  |

لاحظ أن MiT في الجدول أعلاه يشير إلى العمود الفقري لترميز المحول المختلط المقدم في SegFormer. للحصول على نتائج SegFormer على مجموعات بيانات التجزئة مثل ADE20k، راجع [الورقة](https://arxiv.org/abs/2105.15203).

## الموارد

قائمة بموارد Hugging Face الرسمية وموارد المجتمع (مشار إليها بـ 🌎) لمساعدتك في البدء باستخدام SegFormer.

- [`SegformerForImageClassification`] مدعوم بواسطة [نص البرنامج النصي التوضيحي](https://github.com/huggingface/transformers/tree/main/examples/pytorch/image-classification) و [دفتر الملاحظات](https://colab.research.google.com/github/huggingface/notebooks/blob/main/examples/image_classification.ipynb).

- [دليل مهام تصنيف الصور](../tasks/image_classification)

التصنيف الدلالي:

- [`SegformerForSemanticSegmentation`] مدعوم بواسطة [نص البرنامج النصي التوضيحي](https://github.com/huggingface/transformers/tree/main/examples/pytorch/semantic-segmentation).

- يمكن العثور على مدونة حول الضبط الدقيق لـ SegFormer على مجموعة بيانات مخصصة [هنا](https://huggingface.co/blog/fine-tune-segformer).

- يمكن العثور على المزيد من دفاتر الملاحظات التوضيحية حول SegFormer (الاستدلال + الضبط الدقيق على مجموعة بيانات مخصصة) [هنا](https://github.com/NielsRogge/Transformers-Tutorials/tree/master/SegFormer).

- [`TFSegformerForSemanticSegmentation`] مدعوم بواسطة [دفتر الملاحظات التوضيحي هذا](https://github.com/huggingface/notebooks/blob/main/examples/semantic_segmentation-tf.ipynb).

- [دليل مهام التجزئة الدلالية](../tasks/semantic_segmentation)

إذا كنت مهتمًا بتقديم مورد لإدراجه هنا، فالرجاء فتح طلب سحب وسنراجعه! يجب أن يوضح المورد في الوضع المثالي شيئًا جديدًا بدلاً من تكرار مورد موجود.

## SegformerConfig

[[autodoc]] SegformerConfig

## SegformerFeatureExtractor

[[autodoc]] SegformerFeatureExtractor

- __call__

- post_process_semantic_segmentation

## SegformerImageProcessor

[[autodoc]] SegformerImageProcessor

- preprocess

- post_process_semantic_segmentation

<frameworkcontent>
<pt>

## SegformerModel

[[autodoc]] SegformerModel

- forward

## SegformerDecodeHead

[[autodoc]] SegformerDecodeHead

- forward

## SegformerForImageClassification

[[autodoc]] SegformerForImageClassification

- forward

## SegformerForSemanticSegmentation

[[autodoc]] SegformerForSemanticSegmentation

- forward

</pt>
<tf>

## TFSegformerDecodeHead

[[autodoc]] TFSegformerDecodeHead

- call

## TFSegformerModel

[[autodoc]] TFSegformerModel

- call

## TFSegformerForImageClassification

[[autodoc]] TFSegformerForImageClassification

- call

## TFSegformerForSemanticSegmentation

[[autodoc]] TFSegformerForSemanticSegmentation

- call

</tf>
</frameworkcontent>