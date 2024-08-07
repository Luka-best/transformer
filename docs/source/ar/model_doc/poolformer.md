# PoolFormer

## نظرة عامة
تم اقتراح نموذج PoolFormer في [MetaFormer is Actually What You Need for Vision](https://arxiv.org/abs/2111.11418) بواسطة Sea AI Labs. بدلاً من تصميم أداة خلط رموز معقدة لتحقيق أداء SOTA، يهدف هذا العمل إلى إثبات كفاءة نماذج المحول التي تنبع إلى حد كبير من البنية العامة MetaFormer.

مقتبس من الورقة هو ما يلي:

> لقد أظهرت المحولات إمكانات كبيرة في مهام الرؤية الحاسوبية. هناك اعتقاد شائع بأن وحدة خلط الرموز القائمة على الاهتمام تساهم بشكل كبير في كفاءتها. ومع ذلك، أظهرت الأعمال الحديثة أنه يمكن استبدال الوحدة القائمة على الاهتمام في المحولات بواسطة MLPs المكانية وأن النماذج الناتجة لا تزال تؤدي أداءً جيدًا. بناءً على هذه الملاحظة، نفترض أن البنية العامة للمحولات، بدلاً من وحدة خلط الرموز المحددة، هي أكثر أهمية لأداء النموذج. للتحقق من ذلك، نقوم عن قصد باستبدال وحدة الاهتمام في المحولات بمشغل تجميع مكاني بسيط للغاية لإجراء مزج الرموز الأساسي فقط. ومما يثير الدهشة أننا نلاحظ أن النموذج المشتق، الذي يُطلق عليه اسم PoolFormer، يحقق أداءً تنافسيًا في مهام رؤية الكمبيوتر المتعددة. على سبيل المثال، على ImageNet-1K، يحقق PoolFormer دقة أعلى بنسبة 82.1٪، متجاوزًا خطوط الأساس المُحسنة جيدًا للرؤية المحولة/شبكة MLP-like baselines DeiT-B/ResMLP-B24 بنسبة 0.3٪/1.1٪ بدقة أقل من 35٪/52٪ من المعلمات و48٪/60٪ أقل من MACs. تؤكد فعالية PoolFormer افتراضنا وتحثنا على إطلاق مفهوم "MetaFormer"، وهو بنية عامة مستخلصة من المحولات دون تحديد خلاط الرموز. بناءً على التجارب المستفيضة، نجادل بأن MetaFormer هو اللاعب الرئيسي في تحقيق نتائج متفوقة لنماذج المحولات والشبكات المشابهة لـ MLP الحديثة في مهام الرؤية. يدعو هذا العمل إلى مزيد من الأبحاث المستقبلية المكرسة لتحسين MetaFormer بدلاً من التركيز على وحدات خلط الرموز. بالإضافة إلى ذلك، يمكن أن يكون PoolFormer المقترح بمثابة خط أساس لتصميم بنية MetaFormer المستقبلية.

يوضح الشكل أدناه بنية PoolFormer. مأخوذة من [الورقة الأصلية](https://arxiv.org/abs/2111.11418).

<img width="600" src="https://user-images.githubusercontent.com/15921929/142746124-1ab7635d-2536-4a0e-ad43-b4fe2c5a525d.png"/>

تمت المساهمة بهذا النموذج من قبل [heytanay](https://huggingface.co/heytanay). يمكن العثور على الكود الأصلي [هنا](https://github.com/sail-sg/poolformer).

## نصائح الاستخدام

- يحتوي PoolFormer على بنية هرمية، حيث توجد طبقة تجميع متوسطة بسيطة بدلاً من الاهتمام. يمكن العثور على جميع نقاط تفتيش النموذج على [hub](https://huggingface.co/models?other=poolformer).

- يمكن للمرء استخدام [`PoolFormerImageProcessor`] لتحضير الصور للنموذج.

- مثل معظم النماذج، يأتي PoolFormer بأحجام مختلفة، يمكن العثور على تفاصيلها في الجدول أدناه.

| **Model variant** | **Depths**    | **Hidden sizes**    | **Params (M)** | **ImageNet-1k Top 1** |
| :---------------: | ------------- | ------------------- | :------------: | :-------------------: |
| s12               | [2, 2, 6, 2]  | [64, 128, 320, 512] | 12             | 77.2                  |
| s24               | [4, 4, 12, 4] | [64, 128, 320, 512] | 21             | 80.3                  |
| s36               | [6, 6, 18, 6] | [64, 128, 320, 512] | 31             | 81.4                  |
| m36               | [6, 6, 18, 6] | [96, 192, 384, 768] | 56             | 82.1                  |
| m48               | [8, 8, 24, 8] | [96, 192, 384, 768] | 73             | 82.5                  |

## الموارد

قائمة بموارد Hugging Face الرسمية وموارد المجتمع (المشار إليها بـ 🌎) لمساعدتك في البدء باستخدام PoolFormer.

<PipelineTag pipeline="image-classification"/>

- [`PoolFormerForImageClassification`] مدعوم بواسطة [نص البرنامج النصي](https://github.com/huggingface/transformers/tree/main/examples/pytorch/image-classification) و [دفتر الملاحظات](https://colab.research.google.com/github/huggingface/notebooks/blob/main/examples/image_classification.ipynb) هذا.

- راجع أيضًا: [دليل مهام التصنيف الصوري](../tasks/image_classification)

إذا كنت مهتمًا بتقديم مورد لإدراجه هنا، فالرجاء فتح طلب سحب وسنراجعه! يجب أن يُظهر المورد المثالي شيئًا جديدًا بدلاً من تكرار مورد موجود.

## PoolFormerConfig

[[autodoc]] PoolFormerConfig

## PoolFormerFeatureExtractor

[[autodoc]] PoolFormerFeatureExtractor

- __call__

## PoolFormerImageProcessor

[[autodoc]] PoolFormerImageProcessor

- preprocess

## PoolFormerModel

[[autodoc]] PoolFormerModel

- forward

## PoolFormerForImageClassification

[[autodoc]] PoolFormerForImageClassification

- forward