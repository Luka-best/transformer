#!/usr/bin/env bash
export PYTHONPATH="../":"${PYTHONPATH}"

python finetune.py \
    --learning_rate=3e-5 \
    --fp16 \
    --gpus $N_GPUS \
    --do_train \
    --val_check_interval 0.1 \
    --n_val 500 \
    --adam_eps 1e-06 \
    --num_train_epochs 6 --src_lang en_XX --tgt_lang ro_RO \
    --freeze_encoder --freeze_embeds --data_dir $ENRO_DIR \
    --max_source_length 296 --max_target_length 296 --val_max_target_length 296 --test_max_target_length 296 \
    --train_batch_size=$BS --eval_batch_size=$BS --gradient_accumulation_steps=$GAS \
    --model_name_or_path facebook/mbart-large-cc25 \
    --task translation \
    --warmup_steps 500 \
    $@
