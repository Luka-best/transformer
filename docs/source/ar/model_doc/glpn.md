# GLPN

<Tip>

هذا نموذج تم تقديمه مؤخرًا، لذلك لم يتم اختبار واجهة برمجة التطبيقات الخاصة به بشكل مكثف. قد تكون هناك بعض الأخطاء أو التغييرات الطفيفة التي قد تسبب كسره في المستقبل. إذا لاحظت شيئًا غريبًا، يرجى إرسال تقرير عن المشكلة على <[Github Issue](https://github.com/huggingface/transformers/issues/new?assignees=&labels=&template=bug-report.md&title)>

</Tip>

## نظرة عامة

تم اقتراح نموذج GLPN في <["Global-Local Path Networks for Monocular Depth Estimation with Vertical CutDepth"](https://arxiv.org/abs/2201.07436)> بواسطة دويون كيم، وونغهيون جا، وبيونغوان آن، ودونجيو جو، وسيوهان تشون، وجونمو كيم.

يُدمج GLPN محول SegFormer الهرمي مع فك تشفير خفيف الوزن لتقدير العمق أحادي العين. ويظهر فك التشفير المقترح أداءً أفضل من فك التشفير المقترح سابقًا، مع تعقيد حسابي أقل بكثير.

الملخص من الورقة هو ما يلي:

*تقدير العمق من صورة واحدة هي مهمة مهمة يمكن تطبيقها على مختلف المجالات في رؤية الكمبيوتر، وقد نمت بسرعة مع تطور الشبكات العصبية التلافيفية. في هذه الورقة، نقترح بنية واستراتيجية تدريب جديدتين لتقدير العمق أحادي العين لتحسين دقة التنبؤ للشبكة بشكل أكبر. نستخدم برنامج ترميز محول هرمي لالتقاط ونقل السياق العالمي، ونصمم فك تشفير خفيف الوزن ولكنه قوي لتوليد خريطة عمق مقدرة مع مراعاة الاتصال المحلي. من خلال بناء مسارات متصلة بين ميزات متعددة النطاق وتدفق فك التشفير العالمي مع وحدة دمج الميزات الانتقائية المقترحة، يمكن للشبكة دمج كلا التمثيلين واستعادة التفاصيل الدقيقة. بالإضافة إلى ذلك، يظهر فك التشفير المقترح أداءً أفضل من فك التشفير المقترح سابقًا، مع تعقيد حسابي أقل بكثير. علاوة على ذلك، نحسن طريقة التعزيز المحددة للعمق من خلال الاستفادة من ملاحظة مهمة في تقدير العمق لتعزيز النموذج. تتفوق شبكتنا على أداء الطراز المماثل على مجموعة بيانات العمق الصعبة NYU Depth V2. وقد أجريت تجارب مكثفة للتحقق من صحة النهج المقترح وإظهار فعاليته. وأخيرًا، يظهر نموذجنا قدرة تعميم وقوة تحمل أفضل من النماذج المقارنة الأخرى.*

<img src="https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/glpn_architecture.jpg"
alt="drawing" width="600"/>

<small> ملخص النهج. مأخوذ من <[الأوراق الأصلية](https://arxiv.org/abs/2201.07436)> </small>

تمت المساهمة بهذا النموذج بواسطة [nielsr](https://huggingface.co/nielsr). يمكن العثور على الكود الأصلي [هنا](https://github.com/vinvino02/GLPDepth).

## الموارد

فيما يلي قائمة بموارد Hugging Face الرسمية وموارد المجتمع (المشار إليها بـ 🌎) لمساعدتك في البدء باستخدام GLPN.

- يمكن العثور على دفاتر الملاحظات التوضيحية لـ [`GLPNForDepthEstimation`] [هنا](https://github.com/NielsRogge/Transformers-Tutorials/tree/master/GLPN).
- [دليل مهام تقدير العمق أحادي العين](../tasks/monocular_depth_estimation)

## GLPNConfig

[[autodoc]] GLPNConfig

## GLPNFeatureExtractor

[[autodoc]] GLPNFeatureExtractor

- __call__

## GLPNImageProcessor

[[autodoc]] GLPNImageProcessor

- preprocess

## GLPNModel

[[autodoc]] GLPNModel

- forward

## GLPNForDepthEstimation

[[autodoc]] GLPNForDepthEstimation

- forward