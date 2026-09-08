# LUMYD Local SLM Models Directory

This directory stores offline local Small Language Model (SLM) GGUF weights.

### Target Model:
- **Filename:** `lumyd-coder-slm-q4_k_m.gguf`
- **Architecture:** Qwen 2.5 Coder 1.5B Instruct (Fine-tuned on LUMYD multi-domain distillation dataset)
- **Quantization:** 4-bit medium (`q4_k_m`)
- **Size:** ~1.1 GB
- **Inference Runtime:** `llama-cpp-python` / `ollama` / native local execution

### How to obtain the model:
1. Open [`notebooks/LUMYD_SLM_FineTuning_Colab.ipynb`](../notebooks/LUMYD_SLM_FineTuning_Colab.ipynb) in Google Colab.
2. Run on a free T4 GPU (~10-12 minutes).
3. The notebook will automatically download `lumyd-coder-slm-q4_k_m.gguf`.
4. Move the downloaded `.gguf` file into this folder (`backend/models/`).
