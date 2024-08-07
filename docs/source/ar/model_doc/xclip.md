# X-CLIP

## نظرة عامة
اقترح نموذج X-CLIP في [توسيع نماذج الصور المسبقة التدريب على اللغة للتعرف على الفيديو العام](https://arxiv.org/abs/2208.02816) بواسطة Bolin Ni، وHouwen Peng، وMinghao Chen، وSongyang Zhang، وGaofeng Meng، وJianlong Fu، وShiming Xiang، وHaibin Ling.

X-CLIP هو امتداد بسيط لـ [CLIP](clip) للفيديو. يتكون النموذج من مشفر نص، ومشفر رؤية عبر الإطارات، ومحول تكامل متعدد الإطارات، ومولد مطالبات محدد للفيديو.

المستخلص من الورقة هو ما يلي:

> *أظهر التدريب التمهيدي للغة التباينية نجاحًا كبيرًا في تعلم التمثيل المشترك للرؤية والنصوص من البيانات على نطاق الويب، مما يدل على قدرة تعميم "منعدم" ملحوظة لمختلف مهام الصور. ومع ذلك، لا يزال كيفية التوسع الفعال في مثل هذه الطرق الجديدة للتدريب التمهيدي للغة الصور في مجالات الفيديو مشكلة مفتوحة. في هذا العمل، نقدم نهجًا بسيطًا وفعالًا يقوم بتكييف نماذج الصور المسبقة التدريب على اللغة مع التعرف على الفيديو مباشرة، بدلاً من تدريب نموذج جديد من الصفر. على وجه التحديد، لالتقاط تبعيات الإطارات طويلة المدى على طول البعد الزمني، نقترح آلية اهتمام عبر الإطارات تتبادل المعلومات بشكل صريح عبر الإطارات. هذه الوحدة خفيفة الوزن ويمكن توصيلها بنماذج الصور المسبقة التدريب على اللغة بسلاسة. علاوة على ذلك، نقترح نظام مطالبات محدد للفيديو، والذي يستفيد من معلومات محتوى الفيديو لتوليد مطالبات نصية تمييزية. تُظهر التجارب المكثفة أن نهجنا فعال ويمكن تعميمه على سيناريوهات مختلفة للتعرف على الفيديو. على وجه الخصوص، في إعدادات الإشراف الكامل، يحقق نهجنا دقة أعلى بنسبة 87.1٪ في Kinectics-400، في حين يستخدم 12 مرة أقل من FLOPs مقارنة بـ Swin-L وViViT-H. في تجارب الصفر، يتفوق نهجنا على طرق SOTA الحالية بنسبة +7.6٪ و+14.9٪ من حيث دقة أعلى-1 وفقًا لبروتوكولين شائعين. في سيناريوهات القليل من البيانات، يتفوق نهجنا على أفضل الطرق السابقة بنسبة +32.1٪ و+23.1٪ عندما تكون البيانات المسماة محدودة للغاية.*

نصائح:

- استخدام X-CLIP هو نفسه [كليب](clip).

<img src="https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/transformers/model_doc/xclip_architecture.png" alt="drawing" width="600"/>

<small> تصميم X-CLIP. مأخوذة من <a href="https://arxiv.org/abs/2208.02816">الورقة الأصلية.</a> </small>

تمت المساهمة بهذا النموذج بواسطة [nielsr](https://huggingface.co/nielsr).
يمكن العثور على الكود الأصلي [هنا](https://github.com/microsoft/VideoX/tree/master/X-CLIP).

## الموارد

قائمة بموارد Hugging Face الرسمية وموارد المجتمع (مشار إليها بـ 🌎) لمساعدتك في البدء باستخدام X-CLIP.

- يمكن العثور على دفاتر الملاحظات التوضيحية لـ X-CLIP [هنا](https://github.com/NielsRogge/Transformers-Tutorials/tree/master/X-CLIP).

إذا كنت مهتمًا بتقديم مورد لإدراجه هنا، فيرجى فتح طلب سحب وسنراجعه! يجب أن يُظهر المورد بشكل مثالي شيئًا جديدًا بدلاً من تكرار مورد موجود.

## XCLIPProcessor

[[autodoc]] XCLIPProcessor

## XCLIPConfig

[[autodoc]] XCLIPConfig

- from_text_vision_configs

## XCLIPTextConfig

[[autodoc]] XCLIPTextConfig

## XCLIPVisionConfig

[[autodoc]] XCLIPVisionConfig

## XCLIPModel

[[autodoc]] XCLIPModel

- forward
- get_text_features
- get_video_features

## XCLIPTextModel

[[autodoc]] XCLIPTextModel

- forward

## XCLIPVisionModel

[[autodoc]] XCLIPVisionModel

- forward