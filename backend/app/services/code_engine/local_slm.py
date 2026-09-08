"""
LUMYD Local Small Language Model (SLM) Inference Engine
======================================================
Manages offline inference for fine-tuned GGUF models:
- Target Model: `lumyd-coder-slm-q4_k_m.gguf` (Qwen2.5-Coder-1.5B)
- Supported Runtimes:
  1. `llama_cpp` (direct in-process C++ inference with CPU/GPU offload)
  2. `Ollama` (REST API at localhost:11434 if Ollama is running)
- Fallback: Gracefully falls back to Gemini Teacher when the local model is not yet placed in `backend/models/`.
"""

import os
import re
import sys
import glob
import json
from pathlib import Path
from typing import Any, Dict, Optional
import pandas as pd

# Model Directory
MODELS_DIR = Path(__file__).resolve().parents[3] / "models"

class LocalSLMEngine:
    _instance = None
    _llm = None
    _model_path = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LocalSLMEngine, cls).__new__(cls)
            cls._instance._init_engine()
        return cls._instance

    def _init_engine(self):
        self.model_path = self._discover_model_path()
        self.runtime_available = False
        self._llm = None

        # Try discovering llama_cpp
        try:
            import llama_cpp
            self.runtime_available = True
            self.runtime_type = "llama_cpp"
        except ImportError:
            self.runtime_type = "none"

    def _discover_model_path(self) -> Optional[Path]:
        """Discovers any GGUF file inside backend/models/."""
        if not MODELS_DIR.exists():
            return None
        
        # Primary expected name
        primary = MODELS_DIR / "lumyd-coder-slm-q4_k_m.gguf"
        if primary.exists():
            return primary
        
        # Search any .gguf in directory
        gguf_candidates = list(MODELS_DIR.glob("*.gguf"))
        if gguf_candidates:
            return gguf_candidates[0]
        
        return None

    def get_status(self) -> Dict[str, Any]:
        """Returns the readiness state of the local SLM."""
        model_path = self._discover_model_path()
        model_exists = model_path is not None and model_path.exists()
        
        status = "awaiting_model"
        if model_exists:
            if self.runtime_available:
                status = "ready"
            else:
                status = "model_detected_needs_runtime"

        return {
            "model_exists": model_exists,
            "model_path": str(model_path) if model_path else None,
            "model_size_mb": round(model_path.stat().st_size / (1024 * 1024), 2) if model_exists else 0,
            "runtime_type": self.runtime_type,
            "status": status,
            "is_ready": status == "ready"
        }

    def _load_model_if_needed(self):
        """Loads GGUF model into memory if available."""
        if self._llm is not None:
            return self._llm

        model_path = self._discover_model_path()
        if not model_path or not self.runtime_available:
            return None

        try:
            from llama_cpp import Llama
            print(f"[+] Loading Local SLM from {model_path}...")
            self._llm = Llama(
                model_path=str(model_path),
                n_ctx=2048,
                n_threads=4,
                verbose=False
            )
            print("[+] Local SLM loaded successfully into memory!")
            return self._llm
        except Exception as e:
            print(f"[!] Failed to load Local SLM: {e}")
            return None

    def generate_solution(
        self,
        query: str,
        df: pd.DataFrame,
        detected_language: str = "singlish"
    ) -> Optional[Dict[str, Any]]:
        """
        Uses the local SLM to generate Python code and human explanation.
        Returns None if local SLM is not ready, allowing fallback to Gemini Teacher.
        """
        status = self.get_status()
        if not status["is_ready"]:
            return None

        llm = self._load_model_if_needed()
        if not llm:
            return None

        columns = [str(c) for c in df.columns]
        
        # Build Qwen2.5 ChatML prompt
        prompt = (
            f"<|im_start|>system\n"
            f"You are a helpful business intelligence code generator and data analyst. "
            f"Given the dataframe schema and the user question, write Python code operating on `df` "
            f"to compute the exact answer in variable `result`, and explain the findings in a friendly, "
            f"human-readable manner in the user's dialect.<|im_end|>\n"
            f"<|im_start|>user\n"
            f"Dataframe Schema (Columns): {columns}\n"
            f"User Question: {query}<|im_end|>\n"
            f"<|im_start|>assistant\n"
        )

        try:
            output = llm(
                prompt,
                max_tokens=300,
                temperature=0.2,
                stop=["<|im_end|>", "<|endoftext|>"]
            )
            raw_text = output["choices"][0]["text"].strip()
            
            # Extract python code
            code = ""
            code_match = re.search(r"```(?:python)?\s*([\s\S]*?)```", raw_text)
            if code_match:
                code = code_match.group(1).strip()
            else:
                # If model didn't wrap in markdown, check if output contains result =
                if "result =" in raw_text:
                    lines = [l for l in raw_text.split("\n") if not l.startswith("Explanation:")]
                    code = "\n".join(lines).strip()

            # Extract explanation
            explanation = ""
            if "Explanation:" in raw_text:
                explanation = raw_text.split("Explanation:")[-1].strip()
            else:
                explanation = raw_text

            if not code or "result" not in code:
                return None

            return {
                "python_code": code,
                "human_explanation": explanation,
                "language": detected_language,
                "intent_label": "local_slm_analysis",
                "source": "local_slm"
            }
        except Exception as e:
            print(f"[!] Local SLM inference error: {e}")
            return None

local_slm = LocalSLMEngine()
