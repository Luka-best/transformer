# ConvNeXt V2

## نظرة عامة

اقترح نموذج ConvNeXt V2 في ورقة "ConvNeXt V2: التصميم المشترك وتوسيع شبكات التحويل مع برامج الترميز الذاتية القناع" بقلم سانجهيون وو، وشوبهيك ديبناث، ورونجهانج هو، وزينلي تشن، وزوانج ليو، وإن سو كيون، وساينينج شي.

ConvNeXt V2 هو نموذج قائم على الشبكات العصبية الالتفافية الخالصة (ConvNet)، مستوحى من تصميم محولات الرؤية، وهو خلف لـ [ConvNeXT](convnext).

الملخص من الورقة هو كما يلي:

*دفعًا من خلال التحسينات المعمارية وأطر تعلم التمثيل الأفضل، شهد مجال التعرف المرئي تحديثًا سريعًا وتعزيز الأداء في أوائل العقد الأول من القرن الحادي والعشرين. على سبيل المثال، أظهرت شبكات الالتفاف الحديثة، التي يمثلها ConvNeXt، أداءً قويًا في سيناريوهات مختلفة. في حين صممت هذه النماذج في الأصل للتعلم الخاضع للإشراف باستخدام علامات ImageNet، إلا أنها يمكن أن تستفيد أيضًا من تقنيات التعلم الذاتي مثل برامج الترميز الذاتية القناع (MAE). ومع ذلك، وجدنا أن الجمع البسيط بين هذين النهجين يؤدي إلى أداء دون المستوى المطلوب. في هذه الورقة، نقترح إطار ترميز ذاتي قناع قائمًا على التحويل بالكامل وطبقة جديدة لتطبيع الاستجابة العالمية (GRN) يمكن إضافتها إلى بنية ConvNeXt لتعزيز المنافسة بين ميزات القناة. يؤدي هذا التصميم المشترك لتقنيات التعلم الذاتي والتحسين المعماري إلى عائلة نماذج جديدة تسمى ConvNeXt V2، والتي تحسن بشكل كبير أداء شبكات الالتفاف الخالصة على معايير التعرف المختلفة، بما في ذلك تصنيف ImageNet، والكشف عن COCO، وقسم ADE20K. كما نقدم نماذج ConvNeXt V2 مُدربة مسبقًا بأحجام مختلفة، بدءًا من نموذج Atto الفعال بحجم 3.7 مليون معلمة بنسبة دقة 76.7٪ على ImageNet، إلى نموذج Huge بحجم 650 مليون معلمة يحقق دقة 88.9٪ من الطراز الأول باستخدام بيانات التدريب العامة فقط.*

<img src="https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/convnextv2_architecture.png"
alt="drawing" width="600"/>

<small>هندسة ConvNeXt V2. مأخوذة من <a href="https://arxiv.org/abs/2301.00808">الورقة الأصلية</a>.</small>

ساهم بهذا النموذج [adirik](https://huggingface.co/adirik). يمكن العثور على الكود الأصلي [هنا](https://github.com/facebookresearch/ConvNeXt-V2).

## الموارد

قائمة بموارد Hugging Face الرسمية وموارد المجتمع (مشار إليها بـ 🌎) لمساعدتك في البدء باستخدام ConvNeXt V2.

<PipelineTag pipeline="image-classification"/>

- [`ConvNextV2ForImageClassification`] مدعوم بواسطة [نص برمجي مثالي](https://github.com/huggingface/transformers/tree/main/examples/pytorch/image-classification) و [دفتر الملاحظات](https://colab.research.google.com/github/huggingface/notebooks/blob/main/examples/image_classification.ipynb).

إذا كنت مهتمًا بتقديم مورد لإدراجه هنا، فالرجاء فتح طلب سحب وسنراجعه! يجب أن يُظهر المورد في الحالة المثالية شيئًا جديدًا بدلاً من تكرار مورد موجود.

## ConvNextV2Config

[[autodoc]] ConvNextV2Config

## ConvNextV2Model

[[autodoc]] ConvNextV2Model

- forward

## ConvNextV2ForImageClassification

[[autodoc]] ConvNextV2ForImageClassification

- forward

## TFConvNextV2Model

[[autodoc]] TFConvNextV2Model

- call

## TFConvNextV2ForImageClassification

[[autodoc]] TFConvNextV2ForImageClassification

- call