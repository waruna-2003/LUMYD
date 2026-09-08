# LUMYD Local SLM Fine-Tuning Guide (Google Colab)

This directory contains the complete Google Colab training pipeline for fine-tuning **Qwen2.5-Coder-1.5B-Instruct** into a dedicated, offline business intelligence coding assistant (`lumyd-coder-slm-q4_k_m.gguf`).

---

## 📁 Package Contents

- **`LUMYD_SLM_FineTuning_Colab.ipynb`**: Ready-to-run Jupyter notebook configured with Unsloth, QLoRA, and automatic GGUF export.
- **`lumyd_chatml_train.jsonl`**: The verified multi-domain distillation dataset (310 samples across English, Singlish, and Sinhala, 100% verified in `CodeSandbox`).
- **`colab_training_package/`**:
  - `lumyd_chatml_train.jsonl`: Standard ChatML format.
  - `lumyd_alpaca_train.jsonl`: Alpaca instruction format.
  - `test_prompts.json`: Holdout validation prompts.
  - `dataset_metadata.json`: Dataset statistics and metrics.

---

## 🚀 Step-by-Step Instructions to Run in Google Colab

### Step 1: Open Google Colab
1. Go to [Google Colab](https://colab.research.google.com).
2. Click **File > Upload notebook** and select:
   `LUMYD/notebooks/LUMYD_SLM_FineTuning_Colab.ipynb`

### Step 2: Enable Free T4 GPU
1. In the top navigation menu, click **Runtime > Change runtime type**.
2. Under **Hardware accelerator**, select **T4 GPU**.
3. Click **Save**.

### Step 3: Upload the Dataset
- When prompted by Cell 5, upload `lumyd_chatml_train.jsonl` (found in `LUMYD/notebooks/`).
- Alternatively, click the **Folder icon (Files)** on the left sidebar in Colab and drag `lumyd_chatml_train.jsonl` into the files area.

### Step 4: Run All Cells
1. Click **Runtime > Run all** (or press `Ctrl+F9`).
2. The notebook will:
   - Install Unsloth and load Qwen2.5-Coder-1.5B in 4-bit.
   - Fine-tune with LoRA adapters for 60 steps (~10-12 minutes).
   - Test inference across English, Singlish, and Sinhala test cases.
   - Convert and export the model to `lumyd-coder-slm-q4_k_m.gguf` (~1.1 GB).
   - Trigger an automatic browser download of the `.gguf` file.

### Step 5: Bring Back the Trained GGUF Model
1. Once the browser download completes, move `lumyd-coder-slm-q4_k_m.gguf` to:
   ```
   LUMYD/backend/models/lumyd-coder-slm-q4_k_m.gguf
   ```
2. Inform the agent: *"I have downloaded the GGUF model and placed it in backend/models/"* to proceed to the local inference integration step!
