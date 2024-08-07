# LiLT

## نظرة عامة
تم اقتراح نموذج LiLT في [LiLT: A Simple yet Effective Language-Independent Layout Transformer for Structured Document Understanding](https://arxiv.org/abs/2202.13669) بواسطة Jiapeng Wang, Lianwen Jin, Kai Ding.

يتيح LiLT الجمع بين أي مشفر نصي مدرب مسبقًا من نوع RoBERTa مع محول تخطيط خفيف الوزن، لتمكين فهم المستندات المشابهة لـ [LayoutLM](layoutlm) للعديد من اللغات.

الملخص من الورقة هو كما يلي:

*حظي فهم المستندات المنظمة باهتمام كبير وأحرز تقدمًا ملحوظًا في الآونة الأخيرة، وذلك بفضل دوره الحاسم في معالجة المستندات الذكية. ومع ذلك، لا يمكن لمعظم النماذج ذات الصلة الموجودة التعامل إلا مع بيانات المستندات بلغة (لغات) محددة (عادة ما تكون اللغة الإنجليزية) المدرجة في مجموعة البيانات التدريبية، والتي تعد محدودة للغاية. ولمعالجة هذه المشكلة، نقترح محول تخطيط مستقل عن اللغة (LiLT) بسيط وفعال لفهم المستندات المنظمة. يمكن تدريب نموذج LiLT مسبقًا على مستندات منظمة بلغة واحدة، ثم ضبط دقته مباشرة على لغات أخرى باستخدام النماذج النصية أحادية اللغة/المتعددة اللغات المُدربة مسبقًا المقابلة. أظهرت النتائج التجريبية على ثماني لغات أن LiLT يمكن أن يحقق أداءً تنافسيًا أو حتى متفوقًا على معايير مختلفة شائعة الاستخدام، مما يمكّن الاستفادة من التدريب المسبق لهيكل تخطيط المستندات بشكل مستقل عن اللغة.*

<img src="https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/transformers/model_doc/lilt_architecture.jpg"
alt="drawing" width="600"/>

<small>هندسة LiLT. مأخوذة من <a href="https://arxiv.org/abs/2202.13669">الورقة الأصلية</a>.</small>

تمت المساهمة بهذا النموذج بواسطة [nielsr](https://huggingface.co/nielsr).
يمكن العثور على الكود الأصلي [هنا](https://github.com/jpwang/lilt).

## نصائح الاستخدام

- للجمع بين محول التخطيط المستقل عن اللغة ونقطة تفتيش جديدة من RoBERTa من [hub](https://huggingface.co/models?search=roberta)، راجع [هذا الدليل](https://github.com/jpWang/LiLT#or-generate-your-own-checkpoint-optional).
سينتج البرنامج النصي عن ملفي `config.json` و`pytorch_model.bin` المخزنين محليًا. بعد القيام بذلك، يمكنك القيام بما يلي (بافتراض أنك قمت بتسجيل الدخول باستخدام حساب HuggingFace الخاص بك):

```python
from transformers import LiltModel

model = LiltModel.from_pretrained("path_to_your_files")
model.push_to_hub("name_of_repo_on_the_hub")
```

- عند إعداد البيانات للنموذج، تأكد من استخدام مفردات الرموز التي تتوافق مع نقطة تفتيش RoBERTa التي قمت بدمجها مع محول التخطيط.
- نظرًا لأن [lilt-roberta-en-base](https://huggingface.co/SCUT-DLVCLab/lilt-roberta-en-base) يستخدم نفس المفردات مثل [LayoutLMv3](layoutlmv3)، فيمكن استخدام [`LayoutLMv3TokenizerFast`] لإعداد البيانات للنموذج.
وينطبق الشيء نفسه على [lilt-roberta-en-base](https://huggingface.co/SCUT-DLVCLab/lilt-infoxlm-base): يمكن استخدام [`LayoutXLMTokenizerFast`] لهذا النموذج.

## الموارد

قائمة بموارد Hugging Face الرسمية وموارد المجتمع (المشار إليها بـ 🌎) لمساعدتك في البدء باستخدام LiLT.

- يمكن العثور على دفاتر الملاحظات التوضيحية لـ LiLT [هنا](https://github.com/NielsRogge/Transformers-Tutorials/tree/master/LiLT).

**موارد التوثيق**

- [دليل مهمة تصنيف النصوص](../tasks/sequence_classification)
- [دليل مهمة تصنيف الرموز](../tasks/token_classification)
- [دليل مهمة الإجابة على الأسئلة](../tasks/question_answering)

إذا كنت مهتمًا بتقديم مورد لإدراجه هنا، فالرجاء فتح طلب سحب وسنراجعه! يجب أن يوضح المورد في الوضع المثالي شيئًا جديدًا بدلاً من تكرار مورد موجود.

## LiltConfig

[[autodoc]] LiltConfig

## LiltModel

[[autodoc]] LiltModel

- forward

## LiltForSequenceClassification

[[autodoc]] LiltForSequenceClassification

- forward

## LiltForTokenClassification

[[autodoc]] LiltForTokenClassification

- forward

## LiltForQuestionAnswering

[[autodoc]] LiltForQuestionAnswering

- forward