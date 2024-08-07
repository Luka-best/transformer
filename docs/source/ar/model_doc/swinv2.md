# Swin Transformer V2

## نظرة عامة

اقتُرح نموذج Swin Transformer V2 في ورقة بحثية بعنوان [Swin Transformer V2: Scaling Up Capacity and Resolution](https://arxiv.org/abs/2111.09883) بواسطة Ze Liu و Han Hu و Yutong Lin و Zhuliang Yao و Zhenda Xie و Yixuan Wei و Jia Ning و Yue Cao و Zheng Zhang و Li Dong و Furu Wei و Baining Guo.

وفيما يلي الملخص المستخرج من الورقة البحثية:

*أظهرت النماذج اللغوية واسعة النطاق تحسناً ملحوظاً في الأداء على المهام اللغوية دون أي مؤشرات على التشبع. كما أنها تُظهر قدرات مذهلة على التعلم القليل مثل قدرات البشر. تهدف هذه الورقة إلى استكشاف النماذج واسعة النطاق في رؤية الكمبيوتر. نتناول ثلاث قضايا رئيسية في تدريب وتطبيق النماذج البصرية واسعة النطاق، بما في ذلك عدم استقرار التدريب، والفجوات في الدقة بين التدريب الأولي والضبط الدقيق، والحاجة إلى البيانات المُوسمة. تم اقتراح ثلاث تقنيات رئيسية: 1) طريقة residual-post-norm مُجمعة مع انتباه كوسين لتحسين استقرار التدريب؛ 2) طريقة log-spaced continuous position bias لنقل النماذج المُدربة مسبقًا باستخدام صور منخفضة الدقة بشكل فعال إلى مهام التدفق السفلي مع إدخالات عالية الدقة؛ 3) طريقة pre-training ذاتية الإشراف، SimMIM، لتقليل الحاجة إلى الصور المُوسمة الكبيرة. من خلال هذه التقنيات، نجحت هذه الورقة في تدريب نموذج Swin Transformer V2 الذي يحتوي على 3 مليار معامل، وهو أكبر نموذج رؤية كثيف حتى الآن، وجعله قادرًا على التدريب باستخدام صور يصل حجمها إلى 1,536×1,536. حقق هذا النموذج سجلات أداء جديدة في 4 مهام رؤية تمثيلية، بما في ذلك تصنيف الصور ImageNet-V2، وكشف الأجسام COCO، والتجزئة الدلالية ADE20K، وتصنيف إجراءات الفيديو Kinetics-400.*

تمت المساهمة بهذا النموذج من قبل [nandwalritik](https://huggingface.co/nandwalritik). يمكن العثور على الكود الأصلي [هنا](https://github.com/microsoft/Swin-Transformer).

## الموارد

قائمة بموارد Hugging Face الرسمية وموارد المجتمع (مشار إليها بـ 🌎) لمساعدتك في البدء باستخدام Swin Transformer v2.

<PipelineTag pipeline="image-classification"/>

- [`Swinv2ForImageClassification`] مدعوم بواسطة [script](https://github.com/huggingface/transformers/tree/main/examples/pytorch/image-classification) و [notebook](https://colab.research.google.com/github/huggingface/notebooks/blob/main/examples/image_classification.ipynb).

- راجع أيضًا: [دليل مهام تصنيف الصور](../tasks/image_classification)

بالإضافة إلى ذلك:

- [`Swinv2ForMaskedImageModeling`] مدعوم بواسطة [script](https://github.com/huggingface/transformers/tree/main/examples/pytorch/image-pretraining).

إذا كنت مهتمًا بتقديم مورد لإدراجه هنا، فيرجى فتح طلب سحب Pull Request وسنقوم بمراجعته! يُفضل أن يُظهر المورد شيئًا جديدًا بدلاً من تكرار مورد موجود.

## Swinv2Config

[[autodoc]] Swinv2Config

## Swinv2Model

[[autodoc]] Swinv2Model

- forward

## Swinv2ForMaskedImageModeling

[[autodoc]] Swinv2ForMaskedImageModeling

- forward

## Swinv2ForImageClassification

[[autodoc]] transformers.Swinv2ForImageClassification

- forward