# GIT

## نظرة عامة
اقترح نموذج GIT في [GIT: A Generative Image-to-text Transformer for Vision and Language](https://arxiv.org/abs/2205.14100) من قبل Jianfeng Wang, Zhengyuan Yang, Xiaowei Hu, Linjie Li, Kevin Lin, Zhe Gan, Zicheng Liu, Ce Liu, Lijuan Wang. GIT هو محول فك تشفير يعتمد فقط على مشفر الرؤية CLIP لتعريض النموذج لمدخلات الرؤية بالإضافة إلى النص. يحقق النموذج نتائج متقدمة على معايير تقييم إنشاء تعليقات الصور والإجابة على الأسئلة البصرية.

الملخص من الورقة هو ما يلي:

*في هذه الورقة، نقوم بتصميم وتدريب محول الصور النصية التوليدي، GIT، لتوحيد مهام الرؤية واللغة مثل إنشاء تعليقات الصور/الفيديو والإجابة على الأسئلة. في حين أن النماذج التوليدية توفر بنية شبكة متسقة بين المراحل التدريبية والضبط الدقيق، عادةً ما تحتوي الأعمال الموجودة على هياكل معقدة (مشفر/فك تشفير أحادي/متعدد الوسائط) وتعتمد على وحدات خارجية مثل أجهزة الكشف عن الأشياء/الموسومات والتعرف الضوئي على الحروف (OCR). في GIT، قمنا بتبسيط البنية إلى مشفر صورة واحد وفك تشفير نص واحد في إطار مهمة نمذجة لغة واحدة. كما نقوم بزيادة حجم بيانات التدريب المسبق وحجم النموذج لتعزيز أداء النموذج. بدون أجراس وصفارات، يحقق GIT الخاص بنا حالة جديدة من الفن في 12 معيارًا مرجعيًا صعبًا بهامش كبير. على سبيل المثال، يتفوق نموذجنا على أداء الإنسان لأول مرة في TextCaps (138.2 مقابل 125.5 في CIDEr). علاوة على ذلك، نقدم مخططًا جديدًا لتصنيف الصور والتعرف على نص المشهد القائمين على التوليد، وتحقيق أداء جيد في المعايير المرجعية القياسية.*

<img src="https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/transformers/model_doc/git_architecture.jpg"
alt="drawing" width="600"/>

<small>بنية GIT. مأخوذة من <a href="https://arxiv.org/abs/2205.14100" target="_blank">الورقة الأصلية</a>.</small>

تمت المساهمة بهذا النموذج من قبل [nielsr](https://huggingface.co/nielsr). يمكن العثور على الكود الأصلي [هنا](https://github.com/microsoft/GenerativeImage2Text).

## نصائح الاستخدام

- تم تنفيذ GIT بطريقة مشابهة جدًا لـ GPT-2، والفرق الوحيد هو أن النموذج مشروط أيضًا بـ `pixel_values`.

## الموارد

قائمة بموارد Hugging Face الرسمية وموارد المجتمع (المشار إليها بـ 🌎) لمساعدتك في البدء باستخدام GIT.

- يمكن العثور على دفاتر الملاحظات التوضيحية المتعلقة بالاستدلال + الضبط الدقيق لـ GIT على بيانات مخصصة [هنا](https://github.com/NielsRogge/Transformers-Tutorials/tree/master/GIT).
- راجع أيضًا: [دليل مهمة نمذجة اللغة السببية](../tasks/language_modeling)

إذا كنت مهتمًا بتقديم مورد لإدراجه هنا، فيرجى فتح طلب سحب وسنراجعه. يجب أن يوضح المورد المثالي شيئًا جديدًا بدلاً من تكرار مورد موجود.

## GitVisionConfig

[[autodoc]] GitVisionConfig

## GitVisionModel

[[autodoc]] GitVisionModel

- forward

## GitConfig

[[autodoc]] GitConfig

- all

## GitProcessor

[[autodoc]] GitProcessor

- __call__

## GitModel

[[autodoc]] GitModel

- forward

## GitForCausalLM

[[autodoc]] GitForCausalLM

- forward