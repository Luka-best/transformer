# LLaVa

## نظرة عامة
LLaVa هو دردوبوت مفتوح المصدر تم تدريبه عن طريق الضبط الدقيق لـ LlamA/Vicuna على بيانات التعليمات متعددة الوسائط المولدة بواسطة GPT. إنه نموذج لغوي تنازلي، يعتمد على بنية المحول. وبعبارة أخرى، فهو إصدار متعدد الوسائط من نماذج اللغة الضخمة التي تم ضبطها الدقيق للدردشة/التعليمات.

تم اقتراح نموذج LLaVa في الورقة البحثية "Visual Instruction Tuning" وتم تحسينه في الورقة البحثية "Improved Baselines with Visual Instruction Tuning" بواسطة Haotian Liu وChunyuan Li وYuheng Li وYong Jae Lee.

ملخص الورقة البحثية هو كما يلي:

*أظهرت النماذج متعددة الوسائط الكبيرة مؤخرًا تقدمًا مشجعًا مع الضبط الدقيق للتعليمات المرئية. وفي هذه الملاحظة، نُظهر أن موصل الطراز الكامل عبر الوسائط في LLaVA قوي ومُتَوَفِّر للبيانات بشكل مدهش. ومن خلال إجراء تعديلات بسيطة على LLaVA، أي استخدام CLIP-ViT-L-336px مع إسقاط MLP وإضافة بيانات VQA الموجهة نحو المهام الأكاديمية مع مطالبات تنسيق الاستجابة البسيطة، نقوم بإنشاء خطوط أساس أقوى تتفوق على الحالة الراهنة عبر 11 معيارًا. وتستخدم نقطة التفتيش النهائية الخاصة بنا التي تبلغ 13 بليون مجرد 1.2 مليون بيانات متاحة للجمهور، وتنهي التدريب الكامل في ~1 يوم على عقدة A100 واحدة. ونأمل أن يجعل ذلك أبحاث النماذج اللغوية الضخمة متعددة الوسائط في متناول الجميع. وسيكون الكود والنموذج متاحين للجمهور*

<img src="https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/transformers/model_doc/llava_architecture.jpg"
alt="drawing" width="600"/>

<small>بنية LLaVa. مأخوذة من <a href="https://arxiv.org/abs/2304.08485">الورقة البحثية الأصلية.</a></small>

تمت المساهمة بهذا النموذج من قبل [ArthurZ](https://huggingface.co/ArthurZ) و[ybelkada](https://huggingface.co/ybelkada).
يمكن العثور على الكود الأصلي [هنا](https://github.com/haotian-liu/LLaVA/tree/main/llava).

## نصائح الاستخدام

- ننصح المستخدمين باستخدام `padding_side="left"` عند حساب التوليد الدفعي حيث يؤدي إلى نتائج أكثر دقة. كل ما عليك التأكد من هو استدعاء `processor.tokenizer.padding_side = "left"` قبل التوليد.

- لاحظ أن النموذج لم يتم تدريبه بشكل صريح لمعالجة صور متعددة في نفس المطالبة، على الرغم من أن هذا ممكن من الناحية الفنية، فقد تواجه نتائج غير دقيقة.

- للحصول على نتائج أفضل، نوصي المستخدمين بتزويد النموذج بتنسيق المطالبة الصحيح:

```bash
"USER: <image>\n<prompt> ASSISTANT:"
```

بالنسبة للمحادثات متعددة الأدوار:

```bash
"USER: <image>\n<prompt1> ASSISTANT: <answer1></s>USER: <prompt2> ASSISTANT: <answer2></s>USER: <prompt3> ASSISTANT:"
```

### استخدام Flash Attention 2

Flash Attention 2 هو إصدار أسرع وأكثر تحسينًا من التحسين السابق، يرجى الرجوع إلى قسم Flash Attention 2 في وثائق الأداء [هنا](https://huggingface.co/docs/transformers/perf_infer_gpu_one).

## الموارد

قائمة بموارد Hugging Face الرسمية وموارد المجتمع (مشار إليها بـ 🌎) لمساعدتك في البدء مع BEiT.

<PipelineTag pipeline="image-to-text"/>

- عرض توضيحي لـ [Google Colab](https://colab.research.google.com/drive/1qsl6cd2c8gGtEW1xV5io7S8NHh-Cp1TV?usp=sharing) حول كيفية تشغيل Llava على مثيل Google colab من المستوى المجاني باستخدام الاستدلال بـ 4 بت.

- دفتر ملاحظات [مشابه](https://github.com/NielsRogge/Transformers-Tutorials/blob/master/LLaVa/Inference_with_LLaVa_for_multimodal_generation.ipynb) يوضح الاستدلال الدفعي. 🌎

## LlavaConfig

[[autodoc]] LlavaConfig

## LlavaProcessor

[[autodoc]] LlavaProcessor

## LlavaForConditionalGeneration

[[autodoc]] LlavaForConditionalGeneration

- forward