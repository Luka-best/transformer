# Mamba

## نظرة عامة
اقترح نموذج مامبا في [مامبا: نمذجة تسلسل الوقت الخطي مع مساحات الحالة الانتقائية](https://arxiv.org/abs/2312.00752) بواسطة ألبرت جو وتري داو.

هذا النموذج هو بنية نموذجية جديدة تعتمد على نماذج مساحات الحالة. يمكنك قراءة المزيد حول الحدس وراء هذه [هنا](https://srush.github.io/annotated-s4/).

الملخص من الورقة هو ما يلي:

*تعتمد نماذج الأساس، التي تعمل الآن على تشغيل معظم التطبيقات المثيرة في التعلم العميق، بشكل شبه عالمي على بنية المحول ووحدته الأساسية لوحدة الاهتمام. وقد تم تطوير العديد من التصميمات المعمارية ذات الوقت دون التربيعي مثل الاهتمام الخطي، والنماذج المتكررة والمقيدة، ونماذج مساحات الحالة المنظمة، لمعالجة عدم كفاءة المحول الحسابي على التسلسلات الطويلة، ولكنها لم تؤد أداءً جيدًا مثل الاهتمام بالطرائق المهمة مثل اللغة. نحدد أن أحد أوجه القصور الرئيسية لهذه النماذج هو عدم قدرتها على إجراء الاستدلال القائم على المحتوى، ونقوم بعدة تحسينات. أولاً، يؤدي ببساطة السماح لمعلمات SSM بأن تكون دالات للإدخال إلى معالجة ضعفها مع الطرائق المنفصلة، مما يسمح للنموذج بانتقائية انتشار المعلومات أو نسيانها على طول بعد طول التسلسل اعتمادًا على الرمز الحالي. ثانيًا، على الرغم من أن هذا التغيير يمنع استخدام التحويلات الفعالة، إلا أننا نصمم خوارزمية متوازية واعية بالأجهزة في الوضع المتكرر. ندمج هذه SSM الانتقائية في بنية شبكة عصبية مبسطة من النهاية إلى النهاية بدون كتل اهتمام أو حتى كتل MLP (Mamba). يتمتع مامبا باستدلال سريع (5x من خلال وضع المحولات) وتدرج خطي في طول التسلسل، ويتحسن أداؤه على البيانات الحقيقية حتى تسلسلات المليون طولًا. باعتباره العمود الفقري للنموذج التسلسلي العام، يحقق مامبا أداءً متميزًا عبر طرائق متعددة مثل اللغة والصوت وعلم الجينوم. في نمذجة اللغة، يتفوق نموذجنا مامبا-3B على المحولات بنفس الحجم ويتطابق مع المحولات التي يبلغ حجمها ضعف حجمها، في كل من التدريب المسبق والتقييم اللاحق.*

نصائح:

- مامبا هو بنية نموذج مساحة حالة جديدة تنافس المحولات الكلاسيكية. وهو يعتمد على خط التقدم في نماذج مساحات الحالة المنظمة، مع تصميم وتنفيذ فعالين وواعيين بالأجهزة على غرار [FlashAttention](https://github.com/Dao-AILab/flash-attention).

- تُكدس مامبا طبقات "المزج"، والتي تعادل طبقات "الاهتمام". المنطق الأساسي لـ "مامبا" موجود في فئة "MambaMixer".

- هناك تنفيذان متعايشان: أحدهما مُحسّن ويستخدم نوى CUDA السريعة، في حين أن الآخر بسيط ولكنه يمكن تشغيله على أي جهاز!

- يستفيد التنفيذ الحالي من نوى CUDA الأصلية: ما يعادل الاهتمام الفوري لـ مامبا يستضيفه ["mamba-ssm"](https://github.com/state-spaces/mamba) و ["causal_conv1d"](https://github.com/Dao-AILab/causal-conv1d) المستودعات. تأكد من تثبيتها إذا كان جهازك يدعمها!

- المساهمات لجعل المسار البسيط أسرع موضع ترحيب 🤗

تمت المساهمة بهذا النموذج من قبل [ArthurZ](https://huggingface.co/ArthurZ).

يمكن العثور على الكود الأصلي [هنا](https://github.com/state-spaces/mamba).

# الاستخدام

### مثال بسيط على التوليد:

```python
from transformers import MambaConfig, MambaForCausalLM, AutoTokenizer
import torch

tokenizer = AutoTokenizer.from_pretrained("state-spaces/mamba-130m-hf")
model = MambaForCausalLM.from_pretrained("state-spaces/mamba-130m-hf")
input_ids = tokenizer("Hey how are you doing?", return_tensors="pt")["input_ids"]

out = model.generate(input_ids, max_new_tokens=10)
print(tokenizer.batch_decode(out))
```

### Peft fine-tuning

الإصدار البطيء غير مستقر للغاية للتدريب، ويحتاج الإصدار السريع إلى `float32`!

```python
from datasets import load_dataset
from trl import SFTTrainer
from peft import LoraConfig
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments
model_id = "state-spaces/mamba-130m-hf"
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(model_id)
dataset = load_dataset("Abirate/english_quotes", split="train")
training_args = TrainingArguments(
    output_dir="./results",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    logging_dir='./logs',
    logging_steps=10,
    learning_rate=2e-3
)
lora_config = LoraConfig(
    r=8,
    target_modules=["x_proj", "embeddings", "in_proj", "out_proj"],
    task_type="CAUSAL_LM",
    bias="none"
)
trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    args=training_args,
    peft_config=lora_config,
    train_dataset=dataset,
    dataset_text_field="quote",
)
trainer.train()
```

## MambaConfig

[[autodoc]] MambaConfig

## MambaModel

[[autodoc]] MambaModel

- forword

## MambaLMHeadModel

[[autodoc]] MambaForCausalLM

- forword