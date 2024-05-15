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

# Carga los adaptadores con 🤗 PEFT

[[open-in-colab]]

[Parameter-Efficient Fine Tuning (PEFT)](https://huggingface.co/blog/peft) métodos congelan los parámetros del modelo preentrenado durante el punto fino y agregan un pequeño número de parámetros entrenables (los adaptadores) encima de eso.  Los parámetros (los adaptadores) están entrenados para aprender la información tarea específica.  Este enfoque a sido comprobado en ser muy eficiente en memoria con proceso inferior mientras produciendo resultados comparable a un modelo completamente afinado. 

 Adaptadores entrenados con PEFT también son usualmente un orden de magnitud más pequeños que los modelos enteros, haciéndolos más convenientes para compartir, archivar, y cargar. 

<div class="flex flex-col justify-center">
  <img src="https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/peft/PEFT-hub-screenshot.png"/>
  <figcaption class="text-center">Los pesos del adaptero para un modelo de OPTForCausalLM guardado en el Hub son solo ~6MB en comparaciôn al tamaño completo de los  pesos de modelo, cuales sean ~700MB.</figcaption>
</div>

Si estás interesado en aprender más sobre la librería de PEFT, mira la [documentación](https://huggingface.co/docs/peft/index).

## Configuración

Empezar por instalar 🤗 PEFT:

```bash
pip install peft
```

Si quieres tratar las nuevas características, instala la librería de la fuente:

```bash
pip install git+https://github.com/huggingface/peft.git
```

##  Los modelos de PEFT apoyados

Los 🤗 Transformers nativamente apoyan algunos métodos de PEFT, que significa puedes cargar los pesos del adaptador archivados localmente o archivados en el Hub y fácilmente ejecutar o entrenar los pesos con unas cuantas líneas de código.  Los siguientes métodos están apoyados:

- [Low Rank Adapters](https://huggingface.co/docs/peft/conceptual_guides/lora)
- [IA3](https://huggingface.co/docs/peft/conceptual_guides/ia3)
- [AdaLoRA](https://arxiv.org/abs/2303.10512)

Si quieres usar otros métodos de PEFT como el aprendizaje de los prompts o afinamientos de los prompts o de la librería de 🤗 PEFT en general, por favor refiere a la [documentación](https://huggingface.co/docs/peft/index).


## Cargar un adaptador de PEFT

Para cargar y usar un modelo adaptador de PEFT desde 🤗 Transformers, asegura que el Hub repositorio o el directorio local contiene un `adapter_config.json` archivo y pesas de adaptadores como presentado en el ejemplo de imagen de arriba. Después puedes cargar el modelo adaptador de PEFT usando la clase de `AutoModelFor`. Por ejemplo, para cargar el modelo adaptador de PEFT para el lenguaje casual en modelar:

1. específica el ID del modelo de PEFT
2. pásalo a la clase de [`AutoModelForCausalLM`]

```py
from transformers import AutoModelForCausalLM, AutoTokenizer

peft_model_id = "ybelkada/opt-350m-lora"
model = AutoModelForCausalLM.from_pretrained(peft_model_id)
```

<Tip>

Puedes cargar al PEFT adaptador con tampoco una clase de `AutoModelFor` o la clase del modelo base como `OPTForCausalLM` o `LlamaForCausalLM`.

</Tip>

Tambíen puedes cargar un adaptador de PEFT llamando el método de `load_adapter`:

```py
from transformers import AutoModelForCausalLM, AutoTokenizer

model_id = "facebook/opt-350m"
peft_model_id = "ybelkada/opt-350m-lora"

model = AutoModelForCausalLM.from_pretrained(model_id)
model.load_adapter(peft_model_id)
```

## Cargar en 8bit o 4bit

La integración de `bitsandbytes` apoya los tipos de datos precisos que son útiles para cargar modelos grandes porque
 guarda memoria (mira la [guia](https://huggingface.co/docs/transformers/quantization#bitsandbyes) de `bitsandbytes` para aprender mas). Agrega el parametro `load_in_8bit` o el parametro `load_in_4bit` al [`~PreTrainedModel.from_pretrained`] y coloca `device_map="auto"` para effectivamente distribuir el modelo en tu hardware:

```py
from transformers import AutoModelForCausalLM, AutoTokenizer

peft_model_id = "ybelkada/opt-350m-lora"
model = AutoModelForCausalLM.from_pretrained(peft_model_id, device_map="auto", load_in_8bit=True)
```

## Agrega un nuevo adaptador

Puedes usar [`~peft.PeftModel.add_adapter`] para agregar un nuevo adaptador a un modelo con un existente adaptador con tal que
 el nuevo sea el mismo tipo que el adaptador actual. Por ejemplo si tienes un existente LoRA adaptador connectado a un modelo:

```py
from transformers import AutoModelForCausalLM, OPTForCausalLM, AutoTokenizer
from peft import LoraConfig

model_id = "facebook/opt-350m"
model = AutoModelForCausalLM.from_pretrained(model_id),
lora_config = LoraConfig(
    target_modules=["q_proj", "k_proj"],
    init_lora_weights=False
)

model.add_adapter(lora_config, adapter_name="adapter_1")
```

Para agregar un nuevo adaptador:

```py
# attach new adapter with same config
model.add_adapter(lora_config, adapter_name="adapter_2")
```

Ahora puedes usar [`~peft.PeftModel.set_adapter`] para configurar cuál adaptador para usar:

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

## Para activar y desactivar los adaptadores

Cuando has agregado un adaptador a un modelo, puedes activar or desactivar el módulo de adaptador. Para activar el módulo de adaptador:

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

Para desactivar el modulo adaptero:

```py
model.disable_adapters()
output = model.generate(**inputs)
```

## Entrenar un adaptor de PEFT

Los adaptadores de PEFT están apoyados por la clase de [`Trainer`] para que puedas entrenar el adaptador para tu caso de uso específico. Sólo requiere agregar unas líneas más de código.  Por ejemplo, para entrenar un adaptador de LoRA:  

<Tip>

Si no estás familiarizado con el afinamiento de un modelo con la clase[`Trainer`], mira el tutorial [Fine-tune a pretrained model](training).

</Tip>

1. Define tu configuraciôn de adaptador con el tipo de tarea y hiperparámetros (ves [`~peft.LoraConfig`] para más detalles de lo que
 hacen los hiperparámetros).

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

2. Agrega el adaptador al modelo.

```py
model.add_adapter(peft_config)
```

3. ¡Ahora puedes pasar el modelo a [`Trainer`]!

```py
trainer = Trainer(model=model, ...)
trainer.train()
```

Para archivar tu adaptador entrenado y volver a cargarlo:

```py
model.save_pretrained(save_dir)
model = AutoModelForCausalLM.from_pretrained(save_dir)
```

## Agrega capas entrenables adicionales a un PEFT adaptador

Tambien puedes afinar adaptadores entrenables adicionales en encima de un modelo que tiene adaptadores connectados por pasar a `modules_to_save` en tu config de PEFT. Por ejemplo, si tu quieres también afinar el lm_head encima de un modelo con un adaptador de LoRA:

```py
from transformers import AutoModelForCausalLM, OPTForCausalLM, AutoTokenizer
from peft import LoraConfig

model_id = "facebook/opt-350m"
model = AutoModelForCausalLM.from_pretrained(model_id)

lora_config = LoraConfig(
    target_modules=["q_proj", "k_proj"],
    modules_to_save=["lm_head"],
)

model.add_adapter(lora_config)
```


<!--
TODO: (@younesbelkada @stevhliu)
-   Link to PEFT docs for further details
-   Trainer  
-   8-bit / 4-bit examples ?
-->
