# محول المخطط الطيفي الصوتي Audio Spectrogram Transformer

## نظرة عامة

اقترح نموذج محول المخطط الطيفي الصوتي في [AST: Audio Spectrogram Transformer](https://arxiv.org/abs/2104.01778) من قبل يوان غونغ، ويو-آن تشونغ، وجيمس جلاس.

يطبق محول المخطط الطيفي الصوتي [محول الرؤية](vit) على الصوت، عن طريق تحويل الصوت إلى صورة (مخطط طيفي). ويحصل النموذج على نتائج متقدمة في تصنيف الصوت.

الملخص من الورقة هو كما يلي:

*في العقد الماضي، تم اعتماد الشبكات العصبية التلافيفية (CNNs) على نطاق واسع ككتلة بناء رئيسية لنماذج تصنيف الصوت من البداية إلى النهاية، والتي تهدف إلى تعلم خريطة مباشرة من المخططات الطيفية الصوتية إلى العلامات المقابلة. وللتقاط السياق العالمي طويل المدى بشكل أفضل، هناك اتجاه حديث يتمثل في إضافة آلية اهتمام ذاتي على رأس الشبكة العصبية التلافيفية، مما يشكل نموذج تهجين بين الشبكة العصبية التلافيفية والاهتمام. ومع ذلك، فمن غير الواضح ما إذا كان الاعتماد على الشبكة العصبية التلافيفية ضروريًا، وإذا كانت الشبكات العصبية التي تعتمد فقط على الاهتمام كافية للحصول على أداء جيد في تصنيف الصوت. في هذه الورقة، نجيب على هذا السؤال من خلال تقديم محول المخطط الطيفي الصوتي (AST)، وهو أول نموذج خالٍ من التلافيف وقائم على الاهتمام فقط لتصنيف الصوت. نقوم بتقييم AST على معايير تصنيف الصوت المختلفة، حيث يحقق نتائج جديدة متقدمة تبلغ 0.485 mAP على AudioSet، و95.6% دقة على ESC-50، و98.1% دقة على Speech Commands V2.*

<img src="https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/transformers/model_doc/audio_spectogram_transformer_architecture.png" alt="drawing" width="600"/>

<small> بنية محول المخطط الطيفي الصوتي. مأخوذة من <a href="https://arxiv.org/abs/2104.01778">الورقة الأصلية</a>.</small>

تمت المساهمة بهذا النموذج من قبل [nielsr](https://huggingface.co/nielsr).

يمكن العثور على الكود الأصلي [هنا](https://github.com/YuanGongND/ast).

## نصائح الاستخدام

- عند ضبط نموذج محول المخطط الطيفي الصوتي (AST) على مجموعة البيانات الخاصة بك، يوصى بالاهتمام بتطبيع الإدخال (للتأكد من أن الإدخال له متوسط 0 وانحراف معياري 0.5). ويتولى [`ASTFeatureExtractor`] العناية بهذا. لاحظ أنه يستخدم متوسط ​​ومجموعة AudioSet بشكل افتراضي. يمكنك التحقق من [`ast/src/get_norm_stats.py`](https://github.com/YuanGongND/ast/blob/master/src/get_norm_stats.py) لمعرفة كيفية حساب المؤلفين للإحصاءات لمجموعة بيانات أسفل البث.

- لاحظ أن AST يحتاج إلى معدل تعلم منخفض (يستخدم المؤلفون معدل تعلم أقل بعشر مرات مقارنة بنموذج الشبكة العصبية التلافيفية الذي اقترحوه في ورقة [PSLA](https://arxiv.org/abs/2102.01243)) ويصل إلى التقارب بسرعة، لذا يرجى البحث عن معدل تعلم مناسب ومخطط جدولة معدل التعلم لمهمتك.

### استخدام الانتباه المنتج المرجح بالبقعة (SDPA)

تتضمن PyTorch مشغل اهتمام منتج مرجح بالبقعة (SDPA) أصلي كجزء من `torch.nn.functional`. تشمل هذه الوظيفة عدة تطبيقات يمكن تطبيقها اعتمادًا على الإدخالات والأجهزة المستخدمة. راجع [الوثائق الرسمية](https://pytorch.org/docs/stable/generated/torch.nn.functional.scaled_dot_product_attention.html) أو صفحة [GPU Inference](https://huggingface.co/docs/transformers/main/en/perf_infer_gpu_one#pytorch-scaled-dot-product-attention) لمزيد من المعلومات.

يتم استخدام SDPA بشكل افتراضي لـ `torch>=2.1.1` عندما يكون التنفيذ متاحًا، ولكن يمكنك أيضًا تعيين `attn_implementation="sdpa"` في `from_pretrained()` لطلب استخدام SDPA بشكل صريح.

```
from transformers import ASTForAudioClassification
model = ASTForAudioClassification.from_pretrained("MIT/ast-finetuned-audioset-10-10-0.4593", attn_implementation="sdpa", torch_dtype=torch.float16)
...
```

للحصول على أفضل التحسينات، نوصي بتحميل النموذج بنصف الدقة (على سبيل المثال `torch.float16` أو `torch.bfloat16`).

في معيار محلي (A100-40GB، PyTorch 2.3.0، OS Ubuntu 22.04) مع `float32` ونموذج `MIT/ast-finetuned-audioset-10-10-0.4593`، رأينا التحسينات التالية أثناء الاستدلال.

| حجم الدفعة | متوسط ​​وقت الاستدلال (ميلي ثانية)، وضع التقييم | متوسط ​​وقت الاستدلال (ميلي ثانية)، نموذج SDPA | تسريع، SDPA / Eager (x) |
|--------------|-------------------------------------------|-------------------------------------------|------------------------------|
| 1 | 27 | 6 | 4.5 |
| 2 | 12 | 6 | 2 |
| 4 | 21 | 8 | 2.62 |
| 8 | 40 | 14 | 2.86 |

## الموارد

قائمة بموارد Hugging Face الرسمية وموارد المجتمع (المشار إليها بـ 🌎) لمساعدتك في البدء باستخدام محول المخطط الطيفي الصوتي.

<PipelineTag pipeline="audio-classification"/>

- يمكن العثور على دفتر ملاحظات يوضح الاستدلال باستخدام AST لتصنيف الصوت [هنا](https://github.com/NielsRogge/Transformers-Tutorials/tree/master/AST).
- يتم دعم [`ASTForAudioClassification`] بواسطة [نص برمجي توضيحي](https://github.com/huggingface/transformers/tree/main/examples/pytorch/audio-classification) و [دفتر ملاحظات](https://colab.research.google.com/github/huggingface/notebooks/blob/main/examples/audio_classification.ipynb).
- راجع أيضًا: [تصنيف الصوت](../tasks/audio_classification).

إذا كنت مهتمًا بتقديم مورد لإدراجه هنا، فالرجاء فتح طلب سحب وسنراجعه! يجب أن يوضح المورد بشكل مثالي شيئًا جديدًا بدلاً من تكرار مورد موجود.

## ASTConfig

[[autodoc]] ASTConfig

## ASTFeatureExtractor

[[autodoc]] ASTFeatureExtractor

- __call__

## ASTModel

[[autodoc]] ASTModel

- forward

## ASTForAudioClassification

[[autodoc]] ASTForAudioClassification

- forward