## Llama3

```py
import transformers
import torch

model_id = "meta-llama/Meta-Llama-3-8B"

pipeline = transformers.pipeline("text-generation", model=model_id, model_kwargs={"torch_dtype": torch.bfloat16}, device_map="auto")
pipeline("Hey how are you doing today?")
```

## نظرة عامة
اقترح فريق الذكاء الاصطناعي في Meta نموذج Llama3 في منشور المدونة [تقديم Meta Llama 3: أكثر أنظمة اللغة المفتوحة قدرة حتى الآن](https://ai.meta.com/blog/meta-llama-3/).

وفيما يلي الملخص المنشور في المدونة:

*اليوم، يسرنا أن نعلن عن أول نموذجين من الجيل التالي من Llama، Meta Llama 3، والمتاحين للاستخدام العام. يتضمن هذا الإصدار نموذجين للغة مسبقة التدريب ومضبوطة التعليمات مع 8B و70B من المعلمات التي يمكن أن تدعم مجموعة واسعة من حالات الاستخدام. وتبين الجيل التالي من Llama أداءً رائدًا في المجال على مجموعة واسعة من المعايير الصناعية ويقدم قدرات جديدة، بما في ذلك تحسين الاستدلال. نعتقد أن هذه النماذج هي الأفضل في فئتها من المصادر المفتوحة، ببساطة. ودعمًا لنهجنا المفتوح الذي نتبعه منذ فترة طويلة، فإننا نضع Llama 3 في أيدي المجتمع. ونريد أن نطلق شرارة الموجة التالية من الابتكار في الذكاء الاصطناعي عبر المكدس - بدءًا من التطبيقات وحتى أدوات المطورين وحتى عمليات التقييم وحتى تحسينات الاستدلال والمزيد. ولا يمكننا الانتظار لنرى ما ستبنيه ونتطلع إلى تلقي ملاحظاتك.*

يمكنك الاطلاع على جميع نقاط تفتيش نموذج Llama3 [هنا](https://huggingface.co/models?search=llama3).

يمكن العثور على الكود الأصلي للمؤلفين [هنا](https://github.com/meta-llama/llama3).

## نصائح الاستخدام

<Tip warning={true}>

تم تدريب نماذج `Llama3` باستخدام `bfloat16`، ولكن الاستدلال الأصلي يستخدم `float16`. تستخدم نقاط التفتيش التي تم تحميلها على Hub `torch_dtype = 'float16'`، والتي سيتم استخدامها بواسطة واجهة برمجة التطبيقات `AutoModel` لتحويل نقاط التفتيش من `torch.float32` إلى `torch.float16`.

إن `dtype` للأوزان عبر الإنترنت غير ذي صلة إلى حد كبير ما لم تكن تستخدم `torch_dtype="auto"` عند تهيئة نموذج باستخدام `model = AutoModelForCausalLM.from_pretrained("path", torch_dtype = "auto")`. والسبب هو أن النموذج سيتم تنزيله أولاً (باستخدام `dtype` لنقاط التفتيش عبر الإنترنت)، ثم سيتم تحويله إلى `dtype` الافتراضي لـ `torch` (يصبح `torch.float32`)، وأخيرًا، إذا كان هناك `torch_dtype` مقدم في التكوين، فسيتم استخدامه.

لا يوصى بالتدريب على النموذج في `float16` ومن المعروف أنه ينتج `nan`؛ لذلك، يجب تدريب النموذج في `bfloat16`.

</Tip>

نصائح:

- يمكن الحصول على الأوزان الخاصة بنماذج Llama3 عن طريق ملء [هذا النموذج](https://ai.meta.com/resources/models-and-libraries/llama-downloads/).
- الهندسة المعمارية هي نفسها تمامًا مثل Llama2.
- محدد الرموز هو نموذج BPE يعتمد على [tiktoken](https://github.com/openai/tiktoken) (مقابل المستند إلى تنفيذ sentencepiece لـ Llama2). والفرق الرئيسي هو أنه يتجاهل قواعد الدمج BPE عندما يكون رمز الإدخال جزءًا من المفردات. وهذا يعني أنه إذا لم يكن هناك دمج لإنتاج "hugging"، بدلاً من وجود أصغر وحدات، مثل `["hug" و"ging"] تشكل رمزين، إذا كانت "hugging" جزءًا من المفردات، فسيتم إرجاعها تلقائيًا كرموز.
- يستخدم النموذج الأصلي `pad_id = -1` مما يعني أنه لا يوجد رمز خاص للتعبئة. لا يمكننا أن نتبع نفس المنطق، فتأكد من إضافة رمز خاص بالتعبئة باستخدام `tokenizer.add_special_tokens({"pad_token":"<pad>"})` وقم بتغيير حجم تضمين الرمز وفقًا لذلك. يجب عليك أيضًا تعيين `model.config.pad_token_id`. يتم تهيئة طبقة `embed_tokens` للنموذج باستخدام `self.embed_tokens = nn.Embedding(config.vocab_size، config.hidden_size، self.config.padding_idx)`، والتي تتأكد من أن ترميز رمز التعبئة سينتج أصفارًا، لذا يوصى بتمريره عند التهيئة.
- يمكن تحويل نقطة التفتيش الأصلية باستخدام [سكريبت التحويل](https://github.com/huggingface/transformers/blob/main/src/transformers/models/llama/convert_llama_weights_to_hf.py). يمكن استدعاء السكريبت باستخدام الأمر التالي (كمثال):

```bash
python src/transformers/models/llama/convert_llama_weights_to_hf.py \
    --input_dir /path/to/downloaded/llama/weights --model_size 7B --output_dir /output/path --llama_version 3
```

- بعد التحويل، يمكن تحميل النموذج ومحول الرموز باستخدام ما يلي:

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("/output/path")
model = AutoModelForCausalLM.from_pretrained("/output/path")
```

ملاحظة: يتطلب تنفيذ السكريبت مساحة كافية من ذاكرة الوصول العشوائي (RAM) لتنفيذ النموذج بالكامل في دقة float16 (حتى إذا كانت أكبر الإصدارات تأتي في عدة نقاط تفتيش، يحتوي كل منها على جزء من كل وزن للنموذج، لذلك نحتاج إلى تحميلها جميعًا في ذاكرة الوصول العشوائي). بالنسبة للنموذج 75B، هناك حاجة إلى 145 جيجابايت من ذاكرة الوصول العشوائي.

- عند استخدام Flash Attention 2 عبر `attn_implementation="flash_attention_2"`، لا تمرر `torch_dtype` إلى طريقة `from_pretrained` واستخدم التدريب على الأرقام العشرية العائمة المختلطة التلقائية. عند استخدام "مدرب"، يكون الأمر ببساطة بتحديد إما `fp16` أو `bf16` إلى `True`. وإلا، فتأكد من استخدام `torch.autocast`. هذا مطلوب لأن Flash Attention يدعم فقط أنواع البيانات `fp16` و`bf16`.

## الاستخدام السريع

```py3
import transformers
import torch

model_id = "meta-llama/Meta-Llama-3-8B"

pipeline = transformers.pipeline("text-generation", model=model_id, model_kwargs={"torch_dtype": torch.bfloat16}, device_map="auto")
pipeline("Hey how are you doing today?")
```

## الموارد

تتوفر الكثير من الموارد الرائعة بالفعل على صفحة وثائق [~llama2]، وندعو المساهمين إلى إضافة موارد جديدة مخصصة لـ Llama3 هنا! 🤗