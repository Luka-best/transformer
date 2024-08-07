# ConvNeXT

## نظرة عامة

اقترح نموذج ConvNeXT في [شبكة Convolutional لعقد العشرينيات](https://arxiv.org/abs/2201.03545) بواسطة زوانج ليو، هانزي ماو، تشاو-يوان وو، كريستوف فايشتنهوفر، تريفور داريل، ساينينغ شي.

ConvNeXT هي نموذج قائم على الشبكات العصبية التلافيفية الخالصة (ConvNet)، مستوحى من تصميم محولات الرؤية، والذي يدعي أنه يتفوق عليها.

الملخص من الورقة هو ما يلي:

*"بدأ "عقد العشرينيات الصاخب" للتعرف البصري مع تقديم محولات الرؤية (ViTs)، والتي تفوقت بسرعة على شبكات Convolutional كنموذج تصنيف الصور الأكثر تقدماً. من ناحية أخرى، يواجه ViT الأساسي صعوبات عند تطبيقه على مهام رؤية الكمبيوتر العامة مثل الكشف عن الأجسام والتجزئة الدلالية. إن المحولات الهرمية (مثل محولات Swin) هي التي أعادت تقديم العديد من الأولويات المسبقة لـ ConvNet، مما يجعل المحولات قابلة للتطبيق عمليًا كعمود فقري بصري عام وإظهار أداء رائع في مجموعة واسعة من مهام الرؤية. ومع ذلك، لا يزال يُنسب فعالية هذه الأساليب الهجينة إلى حد كبير إلى التفوق المتأصل لمحولات، بدلاً من التحيزات الاستقرائية المتأصلة للالتفافات. في هذا العمل، نعيد فحص مساحات التصميم واختبار حدود ما يمكن أن تحققه شبكة Convolutional نقية. نقوم تدريجياً "تحديث" ResNet القياسية نحو تصميم محول رؤية، واكتشاف العديد من المكونات الرئيسية التي تساهم في اختلاف الأداء على طول الطريق. نتيجة هذا الاستكشاف هي عائلة من نماذج ConvNet النقية تسمى ConvNeXt. تم بناء ConvNeXts بالكامل من وحدات ConvNet القياسية، وتتنافس ConvNeXts بشكل إيجابي مع المحولات من حيث الدقة وقابلية التطوير، وتحقيق 87.8٪ من دقة ImageNet الأعلى وتفوق محولات Swin على كوكو للكشف وADE20K للتجزئة، مع الحفاظ على بساطة وكفاءة شبكات ConvNets القياسية.*

<img src="https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/convnext_architecture.jpg" alt="drawing" width="600"/>

<small>هندسة ConvNeXT. مأخوذة من <a href="https://arxiv.org/abs/2201.03545">الورقة الأصلية</a>.</small>

تمت المساهمة في هذا النموذج بواسطة [nielsr](https://huggingface.co/nielsr). تمت المساهمة في إصدار TensorFlow من النموذج بواسطة [ariG23498](https://github.com/ariG23498) و [gante](https://github.com/gante) و [sayakpaul](https://github.com/sayakpaul) (مساهمة متساوية). يمكن العثور على الكود الأصلي [هنا](https://github.com/facebookresearch/ConvNeXt).

## الموارد

قائمة بموارد Hugging Face الرسمية وموارد المجتمع (المشار إليها بـ 🌎) لمساعدتك في البدء باستخدام ConvNeXT.

<PipelineTag pipeline="image-classification"/>

- [`ConvNextForImageClassification`] مدعوم بواسطة [نص برمجي توضيحي](https://github.com/huggingface/transformers/tree/main/examples/pytorch/image-classification) و [دفتر الملاحظات](https://colab.research.google.com/github/huggingface/notebooks/blob/main/examples/image_classification.ipynb).

- راجع أيضًا: [دليل مهام تصنيف الصور](../tasks/image_classification)

إذا كنت مهتمًا بتقديم مورد لإدراجه هنا، فيرجى فتح طلب سحب وسنراجعه! يجب أن يوضح المورد المثالي شيئًا جديدًا بدلاً من تكرار مورد موجود.

## ConvNextConfig

[[autodoc]] ConvNextConfig

## ConvNextFeatureExtractor

[[autodoc]] ConvNextFeatureExtractor

## ConvNextImageProcessor

[[autodoc]] ConvNextImageProcessor

- preprocess

<frameworkcontent>

<pt>

## ConvNextModel

[[autodoc]] ConvNextModel

- forward

## ConvNextForImageClassification

[[autodoc]] ConvNextForImageClassification

- forward

</pt>

<tf>

## TFConvNextModel

[[autodoc]] TFConvNextModel

- call

## TFConvNextForImageClassification

[[autodoc]] TFConvNextForImageClassification

- call

</tf>

</frameworkcontent>