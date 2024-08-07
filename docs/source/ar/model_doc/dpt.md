# DPT

## نظرة عامة
يقترح نموذج DPT في [محولات الرؤية للتنبؤ الكثيف](https://arxiv.org/abs/2103.13413) بواسطة René Ranftl، وAlexey Bochkovskiy، وVladlen Koltun.
DPT هو نموذج يعتمد على [محول الرؤية (ViT)](vit) كعمود فقري لمهام التنبؤ الكثيف مثل التجزئة الدلالية وتقدير العمق.

المستخلص من الورقة هو ما يلي:

*نقدم محولات الرؤية الكثيفة، وهي بنية تستخدم محولات الرؤية بدلاً من الشبكات الاقترانية كعمود فقري لمهام التنبؤ الكثيف. نقوم بتجميع الرموز من مراحل مختلفة من محول الرؤية إلى تمثيلات شبيهة بالصور بدقات مختلفة ونجمعها تدريجياً في تنبؤات بدقة كاملة باستخدام فك تشفير الاقتران. تقوم البنية الأساسية للمحول بمعالجة التمثيلات بدقة ثابتة وعالية نسبياً ولها مجال استقبال عالمي في كل مرحلة. تسمح هذه الخصائص لمحول الرؤية الكثيف بتوفير تنبؤات أكثر دقة وتماسكاً عالمياً عند مقارنتها بالشبكات الاقترانية بالكامل. تُظهر تجاربنا أن هذا التصميم يحقق تحسينات كبيرة في مهام التنبؤ الكثيف، خاصة عند توفر كمية كبيرة من بيانات التدريب. بالنسبة لتقدير العمق الأحادي، نلاحظ تحسناً يصل إلى 28% في الأداء النسبي عند مقارنته بشبكة اقترانية كاملة متقدمة. عند تطبيقها على التجزئة الدلالية، تحدد محولات الرؤية الكثيفة حالة جديدة في الفن على ADE20K بنسبة 49.02% mIoU. كما نوضح أن البنية يمكن ضبطها بشكل دقيق على مجموعات بيانات أصغر مثل NYUv2 وKITTI وPascal Context حيث تحدد أيضًا الحالة الجديدة للفن.*

<img src="https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/dpt_architecture.jpg"
alt="drawing" width="600"/>

<small>هندسة DPT. مأخوذة من <a href="https://arxiv.org/abs/2103.13413" target="_blank">الورقة الأصلية</a>.</small>

تمت المساهمة بهذا النموذج بواسطة [nielsr](https://huggingface.co/nielsr). يمكن العثور على الكود الأصلي [هنا](https://github.com/isl-org/DPT).

## نصائح الاستخدام
يتوافق DPT مع فئة [`AutoBackbone`]. يسمح ذلك باستخدام إطار عمل DPT مع العمود الفقري لرؤية الكمبيوتر المختلفة المتاحة في المكتبة، مثل [`VitDetBackbone`] أو [`Dinov2Backbone`]. يمكن إنشاؤه على النحو التالي:

```python
from transformers import Dinov2Config, DPTConfig, DPTForDepthEstimation

# initialize with a Transformer-based backbone such as DINOv2
# in that case, we also specify `reshape_hidden_states=False` to get feature maps of shape (batch_size, num_channels, height, width)
backbone_config = Dinov2Config.from_pretrained("facebook/dinov2-base", out_features=["stage1", "stage2", "stage3", "stage4"], reshape_hidden_states=False)

config = DPTConfig(backbone_config=backbone_config)
model = DPTForDepthEstimation(config=config)
```

## الموارد
فيما يلي قائمة بموارد Hugging Face الرسمية وموارد المجتمع (المشار إليها بـ 🌎) لمساعدتك في البدء باستخدام DPT.

- يمكن العثور على دفاتر الملاحظات التوضيحية لـ [`DPTForDepthEstimation`] [هنا](https://github.com/NielsRogge/Transformers-Tutorials/tree/master/DPT).
- [دليل مهام التجزئة الدلالية](../tasks/semantic_segmentation)
- [دليل مهام تقدير العمق الأحادي](../tasks/monocular_depth_estimation)

إذا كنت مهتمًا بتقديم مورد لإدراجه هنا، فيرجى فتح طلب سحب وسنراجعه! يجب أن يوضح المورد في الوضع المثالي شيئًا جديدًا بدلاً من تكرار مورد موجود.

## DPTConfig

[[autodoc]] DPTConfig

## DPTFeatureExtractor

[[autodoc]] DPTFeatureExtractor

- __call__
- post_process_semantic_segmentation

## DPTImageProcessor

[[autodoc]] DPTImageProcessor

- preprocess
- post_process_semantic_segmentation

## DPTModel

[[autodoc]] DPTModel

- forward

## DPTForDepthEstimation

[[autodoc]] DPTForDepthEstimation

- forward

## DPTForSemanticSegmentation

[[autodoc]] DPTForSemanticSegmentation

- forward