# BLIP-2

## نظرة عامة

اقترح نموذج BLIP-2 في [BLIP-2: Bootstrapping Language-Image Pre-training with Frozen Image Encoders and Large Language Models](https://arxiv.org/abs/2301.12597) by
Junnan Li, Dongxu Li, Silvio Savarese, Steven Hoi. يستفيد BLIP-2 من encoders الصور المسبقة التدريب والنماذج اللغوية الكبيرة (LLMs) عن طريق تدريب محول خفيف الوزن مكون من 12 طبقة
مشفِّر بينهما، مما يحقق أداءً متميزًا في مختلف مهام الرؤية واللغة. والأهم من ذلك أن BLIP-2 يحسن [Flamingo](https://arxiv.org/abs/2204.14198)، وهو نموذج مكون من 80 مليار معلمة، بنسبة 8.7%
على VQAv2 بدون تدريب باستخدام 54 ضعف عدد المعلمات القابلة للتدريب.

المستخلص من الورقة هو ما يلي:

* أصبحت تكلفة التدريب على الرؤية واللغة باهظة بشكل متزايد بسبب التدريب من البداية إلى النهاية لنماذج واسعة النطاق. تقترح هذه الورقة BLIP-2، وهي استراتيجية تدريب مسبق عامة وفعالة تقوم بتهيئة التدريب المسبق للرؤية واللغة من encoders الصور المسبقة التدريب الجاهزة والنماذج اللغوية الكبيرة المجمدة. يتجاوز BLIP-2 الفجوة بين الوسائط باستخدام محول استعلام خفيف الوزن، يتم تدريبه المسبق على مرحلتين. المرحلة الأولى تقوم بتهيئة تعلم تمثيل الرؤية واللغة من مشفر صورة مجمد. المرحلة الثانية تقوم بتهيئة التعلم التوليدي للرؤية إلى اللغة من نموذج لغة مجمد. يحقق BLIP-2 أداءً متميزًا في مختلف مهام الرؤية واللغة، على الرغم من وجود عدد أقل بكثير من المعلمات القابلة للتدريب مقارنة بالطرق الحالية. على سبيل المثال، يتفوق نموذجنا على Flamingo80B بنسبة 8.7% في VQAv2 بدون تدريب باستخدام 54 ضعف عدد المعلمات القابلة للتدريب. كما نوضح قدرات النموذج الناشئة على التوليد من الصورة إلى النص بدون تدريب والتي يمكنها اتباع تعليمات اللغة الطبيعية. *

<img src="https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/transformers/model_doc/blip2_architecture.jpg"
alt="drawing" width="600"/>

<small> هندسة BLIP-2. مأخوذة من <a href="https://arxiv.org/abs/2301.12597">الورقة الأصلية.</a> </small>

تمت المساهمة بهذا النموذج من قبل [nielsr](https://huggingface.co/nielsr).
يمكن العثور على الكود الأصلي [هنا](https://github.com/salesforce/LAVIS/tree/5ee63d688ba4cebff63acee04adaef2dee9af207).

## نصائح الاستخدام

- يمكن استخدام BLIP-2 للتوليد النصي الشرطي بناءً على صورة وطلب نص اختياري. في وقت الاستدلال، يوصى باستخدام طريقة [`generate`] .
- يمكن للمرء استخدام [`Blip2Processor`] لتحضير الصور للنموذج، وفك رموز معرّفات الرموز المتوقعة مرة أخرى إلى نص.

## الموارد

قائمة بموارد Hugging Face الرسمية وموارد المجتمع (مشار إليها بـ 🌎) لمساعدتك في البدء باستخدام BLIP-2.

- يمكن العثور على دفاتر الملاحظات التوضيحية لـ BLIP-2 لتعليق الصور، والإجابة على الأسئلة المرئية (VQA) والمحادثات الشبيهة بالدردشة [هنا](https://github.com/NielsRogge/Transformers-Tutorials/tree/master/BLIP-2).
إذا كنت مهتمًا بتقديم مورد لإدراجه هنا، فالرجاء فتح طلب سحب وسنراجعه! يجب أن يوضح المورد في الوضع المثالي شيئًا جديدًا بدلاً من تكرار مورد موجود.

## Blip2Config

[[autodoc]] Blip2Config

- from_vision_qformer_text_configs

## Blip2VisionConfig

[[autodoc]] Blip2VisionConfig

## Blip2QFormerConfig

[[autodoc]] Blip2QFormerConfig

## Blip2Processor

[[autodoc]] Blip2Processor

## Blip2VisionModel

[[autodoc]] Blip2VisionModel

- forward

## Blip2QFormerModel

[[autodoc]] Blip2QFormerModel

- forward

## Blip2Model

[[autodoc]] Blip2Model

- forward
- get_text_features
- get_image_features
- get_qformer_features

## Blip2ForConditionalGeneration

[[autodoc]] Blip2ForConditionalGeneration

- forward
- generate