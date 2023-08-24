<!--Copyright 2023 The HuggingFace Team. All rights reserved.
Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with
the License. You may obtain a copy of the License at
http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
specific language governing permissions and limitations under the License.
⚠️ Note that this file is in Markdown but contain specific syntax for our doc-builder (similar to MDX) that may not be
rendered properly in your Markdown viewer.
-->

# 🤗 PEFT를 사용하여 어댑터 가져오기 [[load-adapters-with-peft]]

[[Colab에서 열기]]

[Parameter-Efficient Fine Tuning (PEFT)](https://huggingface.co/blog/peft) 방법은 사전 훈련된 모델 매개변수를 미세 조정하는 동안 모델 매개변수를 고정하고 그 위에 훈련 가능한 매우 적은 수의 매개변수(어댑터)를 추가합니다. 어댑터는 작업별 정보를 학습하도록 훈련됩니다. 이 접근 방식은 전체로 사전 훈련된 모델과 비교 가능한 결과를 생성하면서 메모리 효율적이며 더 낮은 컴퓨팅 리소스를 사용한다는 것이 입증되었습니다.

PEFT로 훈련된 어댑터는 전체 모델 크기보다 일반적으로 한 순서 작으므로 공유, 저장 및 가져오기 편리합니다.

<div class="flex flex-col justify-center">
  <img src="https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/peft/PEFT-hub-screenshot.png"/>
  <figcaption class="text-center">Hub에 저장된 OPTForCausalLM 모델의 어댑터 가중치는 전체 모델 가중치 크기인 ~700MB 대비 약 6MB입니다.</figcaption>
</div>

🤗 PEFT 라이브러리에 대해 자세히 알아보려면 [문서](https://huggingface.co/docs/peft/index)를 확인하세요.

## 설정 [[setup]]

🤗 PEFT를 설치하여 시작하세요:

```bash
pip install peft
```

새로운 기능을 시도할 때 라이브러리를 소스로부터 설치하는 데 관심이 있을 수 있습니다:

```bash
pip install git+https://github.com/huggingface/peft.git
```

## 지원되는 PEFT 모델 [[supported-peft-models]]

🤗 Transformers는 기본적으로 일부 PEFT 방법을 지원하며, 로컬로 저장된 어댑터 가중치를 가져오거나 Hub에서 쉽게 실행하거나 훈련할 수 있습니다. 다음 방법을 지원합니다:

- [Low Rank Adapters](https://huggingface.co/docs/peft/conceptual_guides/lora)
- [IA3](https://huggingface.co/docs/peft/conceptual_guides/ia3)
- [AdaLoRA](https://arxiv.org/abs/2303.10512)

🤗 PEFT와 관련된 다른 방법(예: 프롬프트 훈련 또는 프롬프트 튜닝) 또는 일반적인 🤗 PEFT 라이브러리에 대해 자세히 알아보려면 [문서](https://huggingface.co/docs/peft/index)를 참조하세요.


## PEFT 어댑터 가져오기 [[load-a-peft-adapter]]

🤗 Transformers에서 PEFT 어댑터 모델을 가져오고 사용하려면 Hub 저장소나 로컬 디렉터리에 `adapter_config.json` 파일과 어댑터 가중치가 포함되어 있는지 확인하십시오. 그런 다음 `AutoModelFor` 클래스를 사용하여 PEFT 어댑터 모델을 가져올 수 있습니다. 예를 들어 인과 관계 언어 모델용 PEFT 어댑터 모델을 가져오려면 다음 단계를 따르십시오:

1. PEFT 모델 ID를 지정하십시오.
2. [`AutoModelForCausalLM`] 클래스에 전달하십시오.

```py
from transformers import AutoModelForCausalLM, AutoTokenizer

peft_model_id = "ybelkada/opt-350m-lora"
model = AutoModelForCausalLM.from_pretrained(peft_model_id)
```

<Tip>

`AutoModelFor` 클래스나 기본 모델 클래스(예: `OPTForCausalLM` 또는 `LlamaForCausalLM`) 중 하나를 사용하여 PEFT 어댑터를 가져올 수 있습니다.

</Tip>

`load_adapter` 메소드를 호출하여 PEFT 어댑터를 가져올 수도 있습니다.

```py
from transformers import AutoModelForCausalLM, AutoTokenizer

model_id = "facebook/opt-350m"
peft_model_id = "ybelkada/opt-350m-lora"

model = AutoModelForCausalLM.from_pretrained(model_id)
model.load_adapter(peft_model_id)
```

## 8비트 또는 4비트로 가져오기 [[load-in-8bit-or-4bit]]

`bitsandbytes` 통합은 8비트와 4비트 정밀도 데이터 유형을 지원하므로 큰 모델을 가져올 때 유용하며, 메모리를 절약합니다. 모델을 하드웨어에 효과적으로 분배하려면 [`~PreTrainedModel.from_pretrained`]에 `load_in_8bit` 또는 `load_in_4bit` 매개변수를 추가하고 `device_map="auto"`를 설정하십시오:

```py
from transformers import AutoModelForCausalLM, AutoTokenizer

peft_model_id = "ybelkada/opt-350m-lora"
model = AutoModelForCausalLM.from_pretrained(peft_model_id, device_map="auto", load_in_8bit=True)
```

## 새 어댑터 추가 [[add-a-new-adapter]]

기존 어댑터가 있는 모델에 새 어댑터를 추가하려면 [`~peft.PeftModel.add_adapter`]를 사용할 수 있습니다. 새 어댑터가 현재 어댑터와 동일한 유형이면 추가할 수 있습니다. 예를 들어 모델에 연결된 기존 LoRA 어댑터가 있는 경우:

```py
from transformers import AutoModelForCausalLM, OPTForCausalLM, AutoTokenizer
from peft import PeftConfig

model_id = "facebook/opt-350m"
model = AutoModelForCausalLM.from_pretrained(model_id)

lora_config = LoraConfig(
    target_modules=["q_proj", "k_proj"],
    init_lora_weights=False
)

model.add_adapter(lora_config, adapter_name="adapter_1")
```

새 어댑터를 추가하려면:

```py
# attach new adapter with same config
model.add_adapter(lora_config, adapter_name="adapter_2")
```

이제 [`~peft.PeftModel.set_adapter`]를 사용하여 어댑터를 사용할 어댑터로 설정할 수 있습니다:

```py
# use adapter_1
model.set_adapter("adapter_1")
output = model.generate(**inputs)
print(tokenizer.decode(output_disabled[0], skip_special_tokens=True))

# use adapter_2
model.set_adapter("adapter_2")
output_enabled = model.generate(**inputs)
print(tokenizer.decode(output_enabled[0], skip_special_tokens=True))
```

## 어댑터 활성화 및 비활성화 [[enable-and-disable-adapters]]

모델에 어댑터를 추가한 후 어댑터 모듈을 활성화 또는 비활성화할 수 있습니다. 어댑터 모듈을 활성화하려면:

```py
from transformers import AutoModelForCausalLM, OPTForCausalLM, AutoTokenizer
from peft import PeftConfig

model_id = "facebook/opt-350m"
adapter_model_id = "ybelkada/opt-350m-lora"
tokenizer = AutoTokenizer.from_pretrained(model_id)
text = "Hello"
inputs = tokenizer(text, return_tensors="pt")

model = AutoModelForCausalLM.from_pretrained(model_id)
peft_config = PeftConfig.from_pretrained(adapter_model_id)

# to initiate with random weights
peft_config.init_lora_weights = False

model.add_adapter(peft_config)
model.enable_adapters()
output = model.generate(**inputs)
```

어댑터 모듈을 비활성화하려면:

```py
model.disable_adapters()
output = model.generate(**inputs)
```

## PEFT 어댑터 훈련 [[train-a-peft-adapter]]

PEFT 어댑터는 [`Trainer`] 클래스에서 지원되므로 특정 사용 사례에 대한 어댑터를 훈련할 수 있습니다. 몇 줄의 코드를 추가하기만 하면 됩니다. 예를 들어 LoRA 어댑터를 훈련하려면 다음과 같습니다:

<Tip>

[`Trainer`]를 사용하여 모델을 미세 조정하는 것이 익숙하지 않다면 [미세 조정된 모델을 미세 조정하기](training) 튜토리얼을 확인하세요.

</Tip>

1. 작업 유형 및 하이퍼파라미터를 지정하여 어댑터 구성을 정의합니다. 하이퍼파라미터에 대한 자세한 내용은 [`~peft.LoraConfig`]를 참조하세요.

```py
from peft import LoraConfig

peft_config = LoraConfig(
    lora_alpha=16,
    lora_dropout=0.1,
    r=64,
    bias="none",
    task_type="CAUSAL_LM",
)
```

2. 모델에 어댑터를 추가합니다.

```py
model.add_adapter(peft_config)
```

3. 이제 모델을 [`Trainer`]에 전달할 수 있습니다!

```py
trainer = Trainer(model=model, ...)
trainer.train()
```

훈련한 어댑터를 저장하고 다시 가져오려면:

```py
model.save_pretrained(save_dir)
model = AutoModelForCausalLM.from_pretrained(save_dir)
```

<!--
TODO: (@younesbelkada @stevhliu)
- PEFT 문서에 대한 링크
- Trainer
- 8비트 / 4비트 예제?
-->