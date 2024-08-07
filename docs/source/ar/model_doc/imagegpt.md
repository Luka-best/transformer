# ImageGPT

## نظرة عامة

تم اقتراح نموذج ImageGPT في [Generative Pretraining from Pixels](https://openai.com/blog/image-gpt) بواسطة Mark Chen, Alec Radford, Rewon Child, Jeffrey Wu, Heewoo Jun, David Luan, Ilya Sutskever. ImageGPT (iGPT) هو نموذج مشابه لـ GPT-2 تم تدريبه للتنبؤ بقيمة البكسل التالي، مما يسمح بتوليد الصور غير المشروطة والمشروطة.

الملخص من الورقة هو ما يلي:

> *مستوحى من التقدم في تعلم التمثيل غير الخاضع للإشراف للغة الطبيعية، نحن نبحث ما إذا كانت النماذج المماثلة يمكن أن تتعلم تمثيلات مفيدة للصور. نقوم بتدريب محول تسلسلي للتنبؤ التلقائي بالبكسل، دون دمج معرفة بنية الإدخال ثنائية الأبعاد. على الرغم من التدريب على ImageNet منخفض الدقة بدون ملصقات، وجدنا أن نموذجًا بنطاق GPT-2 يتعلم تمثيلات صورة قوية كما هو مقاس بواسطة الاستجواب الخطي والضبط الدقيق والتصنيف منخفض البيانات. على CIFAR-10، نحقق دقة 96.3٪ باستخدام مسبار خطي، متجاوزًا شبكة ResNet واسعة النطاق الخاضعة للإشراف، ودقة 99.0٪ باستخدام الضبط الدقيق الكامل، مما يتطابق مع أفضل النماذج المسبقة التدريب الخاضعة للإشراف. نحن أيضًا تنافسية مع المعايير ذاتية الإشراف على ImageNet عند استبدال البكسلات لترميز VQVAE، وتحقيق 69.0٪ دقة أعلى-1 على مسبار خطي لميزاتنا.*

<img src="https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/imagegpt_architecture.png" alt="drawing" width="600"/>

<small> ملخص النهج. مأخوذ من [الورقة الأصلية](https://cdn.openai.com/papers/Generative_Pretraining_from_Pixels_V2.pdf). </small>

تمت المساهمة بهذا النموذج بواسطة [nielsr](https://huggingface.co/nielsr)، بناءً على [هذه القضية](https://github.com/openai/image-gpt/issues/7). يمكن العثور على الكود الأصلي [هنا](https://github.com/openai/image-gpt).

## نصائح الاستخدام

- ImageGPT هو نفسه تقريبًا مثل [GPT-2](gpt2)، باستثناء استخدام دالة تنشيط مختلفة (وهي "quick gelu")، ولا تقوم طبقات التطبيع الطبقي بمركز متوسط المدخلات. كما أن ImageGPT لا يحتوي على تضمين إدخال وإخراج مربوط.

- نظرًا لأن متطلبات الوقت والذاكرة لآلية اهتمام المحولات تتناسب تربيعيًا مع طول التسلسل، قام المؤلفون بتدريب ImageGPT مسبقًا على دقات إدخال أصغر، مثل 32x32 و64x64. ومع ذلك، فإن إدخال تسلسل من 32x32x3=3072 رمزًا من 0..255 في محول لا يزال كبيرًا جدًا. لذلك، طبق المؤلفون التجميع k-means على قيم البكسل (R,G,B) مع k=512. بهذه الطريقة، لدينا تسلسل يبلغ طوله 32*32 = 1024، ولكنه الآن من الأعداد الصحيحة في النطاق 0..511. لذلك، نقوم بتقليص طول التسلسل على حساب مصفوفة تضمين أكبر. وبعبارة أخرى، يبلغ حجم مفردات ImageGPT 512، + 1 لعلامة "بداية الجملة" (SOS) الخاصة، والتي يتم استخدامها في بداية كل تسلسل. يمكن للمرء استخدام [`ImageGPTImageProcessor`] لتحضير الصور للنموذج.

- على الرغم من التدريب المسبق تمامًا بدون إشراف (أي بدون استخدام أي ملصقات)، فإن ImageGPT ينتج ميزات صورة جيدة الأداء مفيدة للمهام اللاحقة، مثل تصنيف الصور. أظهر المؤلفون أن الميزات الموجودة في منتصف الشبكة هي الأكثر أداءً، ويمكن استخدامها كما هي لتدريب نموذج خطي (مثل نموذج الانحدار اللوجستي sklearn على سبيل المثال). يُشار إلى هذا أيضًا باسم "الاستجواب الخطي". يمكن الحصول على الميزات بسهولة عن طريق تمرير الصورة أولاً عبر النموذج، ثم تحديد `output_hidden_states=True`، ثم تجميع المتوسط للدول المخفية في أي طبقة تريدها.

- بدلاً من ذلك، يمكن للمرء مواصلة الضبط الدقيق للنموذج بالكامل على مجموعة بيانات تابعة، على غرار BERT. للقيام بذلك، يمكنك استخدام [`ImageGPTForImageClassification`].

- يأتي ImageGPT بأحجام مختلفة: هناك ImageGPT-small، وImageGPT-medium، وImageGPT-large. قام المؤلفون أيضًا بتدريب متغير XL، لكنهم لم يطلقوه. يتم تلخيص الاختلافات في الحجم في الجدول التالي:

| **متغير النموذج** | **الأعماق** | **الأحجام المخفية** | **حجم فك تشفير المخفية** | **بارامترات (م)** | **ImageNet-1k Top 1** |
|---|---|---|---|---|---|
| MiT-b0 | [2, 2, 2, 2] | [32, 64, 160, 256] | 256 | 3.7 | 70.5 |
| MiT-b1 | [2, 2, 2, 2] | [64, 128, 320, 512] | 256 | 14.0 | 78.7 |
| MiT-b2 | [3, 4, 6, 3] | [64, 128, 320, 512] | 768 | 25.4 | 81.6 |
| MiT-b3 | [3, 4, 18, 3] | [64, 128, 320, 512] | 768 | 45.2 | 83.1 |
| MiT-b4 | [3, 8, 27, 3] | [64, 128, 320, 512] | 768 | 62.6 | 83.6 |
| MiT-b5 | [3, 6, 40, 3] | [64, 128, 320, 512] | 768 | 82.0 | 83.8 |

## الموارد

قائمة بموارد Hugging Face الرسمية وموارد المجتمع (المشار إليها بـ 🌎) لمساعدتك في البدء باستخدام ImageGPT.

<PipelineTag pipeline="image-classification"/>

- يمكن العثور على دفاتر الملاحظات التوضيحية لـ ImageGPT [هنا](https://github.com/NielsRogge/Transformers-Tutorials/tree/master/ImageGPT).
- [`ImageGPTForImageClassification`] مدعوم بواسطة [نص البرنامج النصي](https://github.com/huggingface/transformers/tree/main/examples/pytorch/image-classification) و [دفتر الملاحظات](https://colab.research.google.com/github/huggingface/notebooks/blob/main/examples/image_classification.ipynb) هذا.
- راجع أيضًا: [دليل مهام تصنيف الصور](../tasks/image_classification)

إذا كنت مهتمًا بتقديم مورد لإدراجه هنا، فالرجاء فتح طلب سحب وسنراجعه! يجب أن يُظهر المورد بشكل مثالي شيئًا جديدًا بدلاً من تكرار مورد موجود.

## ImageGPTConfig

[[autodoc]] ImageGPTConfig

## ImageGPTFeatureExtractor

[[autodoc]] ImageGPTFeatureExtractor

- __call__

## ImageGPTImageProcessor

[[autodoc]] ImageGPTImageProcessor

- preprocess

## ImageGPTModel

[[autodoc]] ImageGPTModel

- forward

## ImageGPTForCausalImageModeling

[[autodoc]] ImageGPTForCausalImageModeling

- forward

## ImageGPTForImageClassification

[[autodoc]] ImageGPTForImageClassification

- forward