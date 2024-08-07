# محول الرؤية التحويلي التلافيفي (CvT)

## نظرة عامة

اقترح نموذج CvT في [CvT: تقديم التحويلات إلى محولات الرؤية](https://arxiv.org/abs/2103.15808) بواسطة Haiping Wu و Bin Xiao و Noel Codella و Mengchen Liu و Xiyang Dai و Lu Yuan و Lei Zhang. محول الرؤية التلافيفي (CvT) يحسن من [محول الرؤية (ViT)](vit) في الأداء والكفاءة من خلال تقديم التحويلات إلى ViT لإنتاج الأفضل من كلا التصميمين.

الملخص من الورقة هو ما يلي:

*نقدم في هذه الورقة بنية جديدة، تسمى محول الرؤية التلافيفي (CvT)، والتي تحسن محول الرؤية (ViT) في الأداء والكفاءة من خلال تقديم التحويلات إلى ViT لإنتاج الأفضل من كلا التصميمين. يتم تحقيق ذلك من خلال تعديلين رئيسيين: تسلسل هرمي لمحولات تحتوي على تضمين رمزي تحويلي جديد، وكتلة محول تحويلي تستخدم إسقاطًا تحويليًا. وتضيف هذه التغييرات خصائص مرغوبة من شبكات التلافيف العصبية (CNNs) إلى بنية ViT (مثل التحول، والتدرج، وثبات التشوه) مع الحفاظ على مزايا المحولات (مثل الاهتمام الديناميكي، والسياق العالمي، والتعميم الأفضل). نحن نتحقق من صحة CvT من خلال إجراء تجارب واسعة النطاق، مما يظهر أن هذا النهج يحقق أداءً متميزًا على محولات الرؤية الأخرى وشبكات ResNet على ImageNet-1k، مع عدد أقل من المعلمات وعمليات الفاصلة العائمة. بالإضافة إلى ذلك، يتم الحفاظ على مكاسب الأداء عند التدريب المسبق على مجموعات بيانات أكبر (مثل ImageNet-22k) والضبط الدقيق لمهام التدفق السفلي. عند التدريب المسبق على ImageNet-22k، يحصل نموذجنا CvT-W24 على دقة 87.7٪ للتصنيفات الأعلى-1 على مجموعة بيانات ImageNet-1k للتحقق من الصحة. وأخيرًا، تُظهر نتائجنا أنه يمكن الاستغناء بأمان عن الترميز الموضعي، وهو مكون أساسي في محولات الرؤية الحالية، في نموذجنا، مما يبسط التصميم لمهام الرؤية ذات الدقة الأعلى.*

تمت المساهمة بهذا النموذج بواسطة [anugunj](https://huggingface.co/anugunj). يمكن العثور على الكود الأصلي [هنا](https://github.com/microsoft/CvT).

## نصائح الاستخدام

- تعد نماذج CvT محولات رؤية عادية، ولكنها مدربة باستخدام التحويلات. إنها تتفوق على [النموذج الأصلي (ViT)](vit) عند ضبطها الدقيق على ImageNet-1K و CIFAR-100.
- يمكنك الاطلاع على دفاتر الملاحظات التجريبية المتعلقة بالاستدلال وكذلك الضبط الدقيق على البيانات المخصصة [هنا](https://github.com/NielsRogge/Transformers-Tutorials/tree/master/VisionTransformer) (يمكنك ببساطة استبدال [`ViTFeatureExtractor`] بـ [`AutoImageProcessor`] و [`ViTForImageClassification`] بـ [`CvtForImageClassification`]).
- نقاط التفتيش المتاحة إما (1) مدربة مسبقًا على [ImageNet-22k](http://www.image-net.org/) (مجموعة من 14 مليون صورة و22 ألف فئة) فقط، أو (2) أيضًا ضبطها بدقة على ImageNet-22k أو (3) أيضًا ضبطها بدقة على [ImageNet-1k](http://www.image-net.org/challenges/LSVRC/2012/) (يشار إليها أيضًا باسم ILSVRC 2012، وهي مجموعة من 1.3 مليون صورة و1000 فئة).

## الموارد

قائمة بموارد Hugging Face الرسمية والمجتمعية (مشار إليها بـ 🌎) لمساعدتك في البدء باستخدام CvT.

<PipelineTag pipeline="image-classification"/>

- [`CvtForImageClassification`] مدعوم بواسطة [نص البرنامج النصي التوضيحي](https://github.com/huggingface/transformers/tree/main/examples/pytorch/image-classification) و [دفتر الملاحظات](https://colab.research.google.com/github/huggingface/notebooks/blob/main/examples/image_classification.ipynb).
- راجع أيضًا: [دليل مهام تصنيف الصور](../tasks/image_classification)

إذا كنت مهتمًا بتقديم مورد لإدراجه هنا، فالرجاء فتح طلب سحب وسنراجعه! يجب أن يوضح المورد المثالي شيئًا جديدًا بدلاً من تكرار مورد موجود.

## CvtConfig

[[autodoc]] CvtConfig

<frameworkcontent>
<pt>

## CvtModel

[[autodoc]] CvtModel

- forward

## CvtForImageClassification

[[autodoc]] CvtForImageClassification

- forward

</pt>
<tf>

## TFCvtModel

[[autodoc]] TFCvtModel

- call

## TFCvtForImageClassification

[[autodoc]] TFCvtForImageClassification

- call

</tf>

</frameworkcontent>