"""
Generates the standalone Google Colab fine-tuning notebook:
notebooks/LUMYD_SLM_FineTuning_Colab.ipynb
"""

import json
import sys
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

repo_root = Path(__file__).resolve().parents[2]
notebook_path = repo_root / "notebooks" / "LUMYD_SLM_FineTuning_Colab.ipynb"

def create_cell(cell_type, source):
    if isinstance(source, list):
        src_lines = [s + "\n" if not s.endswith("\n") else s for s in source]
    else:
        src_lines = [line + "\n" for line in source.split("\n")]
        # Remove trailing newline from last line to match standard ipynb
        if src_lines:
            src_lines[-1] = src_lines[-1].rstrip("\n")

    cell = {
        "cell_type": cell_type,
        "metadata": {},
        "source": src_lines
    }
    if cell_type == "code":
        cell["execution_count"] = None
        cell["outputs"] = []
    return cell

def build_notebook():
    cells = []

    # Cell 1: Markdown Header
    cells.append(create_cell("markdown", """# 🚀 LUMYD Local SLM Fine-Tuning: Qwen2.5-Coder-1.5B with Unsloth (QLoRA)

Welcome to the **LUMYD** Teacher-Student Distillation training notebook!
In this notebook, you will fine-tune an ultra-fast, offline Small Language Model (**Qwen2.5-Coder-1.5B-Instruct**) on your verified multi-domain dataset (`lumyd_chatml_train.jsonl`).

### 📌 What this notebook accomplishes:
1. **Installs Unsloth** (2x faster fine-tuning, 70% less VRAM consumption).
2. **Loads Qwen2.5-Coder-1.5B-Instruct** in 4-bit precision (runs on free Colab T4 GPU).
3. **Applies LoRA adapters** targeting all attention & MLP projection layers.
4. **Loads and formats your multi-domain dataset** (English, Singlish, Sinhala queries + Pandas code + dialect explanations).
5. **Trains the model** using Hugging Face `SFTTrainer` in ~10-15 minutes.
6. **Tests inference** on holdout Singlish, Sinhala, and English prompts.
7. **Exports directly to GGUF (`lumyd-coder-slm-q4_k_m.gguf`)** for direct local deployment in LUMYD!

---
⚡ **Hardware Check:** In Google Colab top menu, navigate to **Runtime > Change runtime type** and select **T4 GPU** (Free)."""))

    # Cell 2: Setup Dependencies
    cells.append(create_cell("code", """# Check GPU availability
!nvidia-smi

# Install Unsloth & modern training dependencies
!pip install --no-deps "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
!pip install --no-deps "xformers<0.0.29" "trl<0.9.0" peft accelerate bitsandbytes datasets triton"""))

    # Cell 3: Load Base Model & Tokenizer
    cells.append(create_cell("code", """from unsloth import FastLanguageModel
import torch

max_seq_length = 2048
dtype = None # Auto detect: Float16 for T4 GPU, Bfloat16 for Ampere+
load_in_4bit = True

# Qwen2.5-Coder-1.5B-Instruct provides optimal reasoning, speed and 1.1GB GGUF size
model_name = "Qwen/Qwen2.5-Coder-1.5B-Instruct"

print(f"Loading {model_name} in 4-bit quantization...")
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = model_name,
    max_seq_length = max_seq_length,
    dtype = dtype,
    load_in_4bit = load_in_4bit,
)
print("✅ Base model loaded successfully!")"""))

    # Cell 4: Configure LoRA Adapters
    cells.append(create_cell("code", """# Apply parameter-efficient LoRA adapters
model = FastLanguageModel.get_peft_model(
    model,
    r = 16, # LoRA rank: 16 provides rich expressive capacity for code syntax
    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                      "gate_proj", "up_proj", "down_proj"],
    lora_alpha = 16,
    lora_dropout = 0, # Optimized 0 for Unsloth
    bias = "none",
    use_gradient_checkpointing = "unsloth", # 30% longer context with zero VRAM overhead
    random_state = 3407,
    use_rslora = False,
    loftq_config = None,
)

print("✅ LoRA adapters successfully attached!")
model.print_trainable_parameters()"""))

    # Cell 5: Upload or Load Dataset
    cells.append(create_cell("code", """import os
import json
from google.colab import files
from datasets import Dataset

# Expected dataset filename from LUMYD package
dataset_file = "lumyd_chatml_train.jsonl"

if not os.path.exists(dataset_file):
    print("📁 Please upload 'lumyd_chatml_train.jsonl' from your local LUMYD/notebooks/colab_training_package/ directory:")
    uploaded = files.upload()
    for fn in uploaded.keys():
        if fn.endswith(".jsonl"):
            dataset_file = fn
            break

print(f"Loading dataset from: {dataset_file}")

raw_data = []
with open(dataset_file, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            raw_data.append(json.loads(line))

print(f"✅ Loaded {len(raw_data)} verified multi-domain training samples!")
hf_dataset = Dataset.from_list(raw_data)"""))

    # Cell 6: Format Dataset with ChatML Template
    cells.append(create_cell("code", """from unsloth.chat_templates import get_chat_template

# Configure Qwen 2.5 ChatML template
tokenizer = get_chat_template(
    tokenizer,
    chat_template = "qwen-2.5",
    mapping = {"role" : "role", "content" : "content", "user" : "user", "assistant" : "assistant", "system" : "system"}
)

def formatting_prompts_func(examples):
    convos = examples["messages"]
    texts = [tokenizer.apply_chat_template(convo, tokenize=False, add_generation_prompt=False) for convo in convos]
    return { "text" : texts }

dataset = hf_dataset.map(formatting_prompts_func, batched=True)
print("Sample formatted training prompt:")
print("-" * 60)
print(dataset[0]["text"][:600] + "...")
print("-" * 60)"""))

    # Cell 7: Train with SFTTrainer
    cells.append(create_cell("code", """from trl import SFTTrainer
from transformers import TrainingArguments
from unsloth import is_bfloat16_supported

trainer = SFTTrainer(
    model = model,
    tokenizer = tokenizer,
    train_dataset = dataset,
    dataset_text_field = "text",
    max_seq_length = max_seq_length,
    dataset_num_proc = 2,
    packing = False,
    args = TrainingArguments(
        per_device_train_batch_size = 2,
        gradient_accumulation_steps = 4, # Effective batch size = 8
        warmup_steps = 5,
        max_steps = 60, # 60 steps (~3-4 epochs on 310 samples), takes ~10-12 mins on T4
        learning_rate = 2e-4,
        fp16 = not is_bfloat16_supported(),
        bf16 = is_bfloat16_supported(),
        logging_steps = 10,
        optim = "adamw_8bit",
        weight_decay = 0.01,
        lr_scheduler_type = "linear",
        seed = 3407,
        output_dir = "outputs",
        report_to = "none",
    ),
)

print("🚀 Starting Fine-Tuning on T4 GPU...")
trainer_stats = trainer.train()
print("🎉 Fine-Tuning Complete!")
print(f"Total Train Runtime: {trainer_stats.metrics.get('train_runtime', 0):.2f} seconds")"""))

    # Cell 8: Holdout Inference Validation across Dialects
    cells.append(create_cell("code", """# Enable fast inference mode
FastLanguageModel.for_inference(model)

test_cases = [
    {
        "dialect": "Singlish (Retail)",
        "schema": "['Product_Category', 'Sales_Amount', 'Profit', 'Region']",
        "query": "machan wadiyenma profit labuna product category eka mokakda balala denna"
    },
    {
        "dialect": "English (HR)",
        "schema": "['Employee_ID', 'Full_Name', 'Department', 'Base_Salary', 'Bonus']",
        "query": "What is the average bonus in the Engineering department?"
    },
    {
        "dialect": "Sinhala (Finance)",
        "schema": "['Expense_ID', 'Transaction_Date', 'Category', 'Vendor', 'Amount', 'Approval_Status']",
        "query": "තවමත් අනුමත නොවූ වියදම් වල එකතුව කීයද?"
    },
    {
        "dialect": "Singlish (Inventory)",
        "schema": "['SKU_Code', 'Item_Description', 'Stock_Quantity', 'Unit_Cost']",
        "query": "mcn total inventory value eka calculate karala denna"
    }
]

system_prompt = (
    "You are a helpful business intelligence code generator and data analyst. "
    "Given the dataframe schema and the user question, write Python code operating on `df` "
    "to compute the exact answer in variable `result`, and explain the findings in a friendly, "
    "human-readable manner in the user's dialect."
)

print("🔎 RUNNING VALIDATION INFERENCE ACROSS MULTIPLE DIALECTS:\n")

for case in test_cases:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Dataframe Schema (Columns): {case['schema']}\\nUser Question: {case['query']}"}
    ]
    inputs = tokenizer.apply_chat_template(
        messages,
        tokenize = True,
        add_generation_prompt = True,
        return_tensors = "pt"
    ).to("cuda")

    outputs = model.generate(input_ids = inputs, max_new_tokens = 256, use_cache = True, temperature = 0.2)
    response = tokenizer.batch_decode(outputs)
    
    # Strip template tags
    assistant_reply = response[0].split("<|im_start|>assistant\\n")[-1].replace("<|im_end|>", "")
    
    print("=" * 65)
    print(f"🌐 Dialect: {case['dialect']}")
    print(f"❓ Query: {case['query']}")
    print("🤖 Model Response:")
    print(assistant_reply.strip())
    print("=" * 65 + "\\n")"""))

    # Cell 9: Export to GGUF
    cells.append(create_cell("code", """# Export to GGUF format for llama.cpp / Ollama / local LUMYD inference
output_gguf_name = "lumyd-coder-slm"
quant_method = "q4_k_m" # High quality 4-bit medium quantization (~1.1 GB)

print(f"📦 Exporting model to GGUF ({quant_method})... This converts weights to GGUF format...")
model.save_pretrained_gguf(
    output_gguf_name,
    tokenizer,
    quantization_method = quant_method
)

print(f"✅ Successfully exported to {output_gguf_name}-{quant_method}.gguf!")
!ls -lh *gguf*"""))

    # Cell 10: Download to Computer
    cells.append(create_cell("code", """from google.colab import files
import glob

gguf_files = glob.glob(f"*{quant_method}*.gguf")
if gguf_files:
    target_file = gguf_files[0]
    print(f"📥 Initiating browser download for {target_file} (~1.1 GB)...")
    files.download(target_file)
    print("\\n✅ ACTION FOR USER:")
    print("Once downloaded, copy this .gguf file into your LUMYD project directory at:")
    print("👉 LUMYD/backend/models/lumyd-coder-slm-q4_k_m.gguf")
else:
    print("⚠️ GGUF file not found in current directory. Check folder contents with !ls")"""))

    notebook_content = {
        "cells": cells,
        "metadata": {
            "accelerator": "GPU",
            "colab": {
                "gpuType": "T4",
                "provenance": []
            },
            "language_info": {
                "name": "python"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 0
    }

    with open(notebook_path, "w", encoding="utf-8") as f:
        json.dump(notebook_content, f, indent=2, ensure_ascii=False)

    print(f"✅ Generated notebook at {notebook_path} with {len(cells)} cells.")

if __name__ == "__main__":
    build_notebook()
