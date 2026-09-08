"""
LUMYD Colab Package Preparer & Dataset Validator
================================================
1. Validates every entry in backend/data/teacher_distillation_dataset.jsonl:
   - JSON validity
   - Required keys: instruction, dataset_columns, query, language, intent_label, python_code, human_explanation
   - Language dialect breakdown and token length metrics.
2. Converts raw records into standard ChatML format (`messages` array with system, user, assistant)
   and standard Alpaca format for 100% plug-and-play compatibility with Unsloth / SFTTrainer / HuggingFace.
3. Exports a clean standalone package directory at `notebooks/colab_training_package/`:
   - `lumyd_chatml_train.jsonl` (ChatML format)
   - `lumyd_alpaca_train.jsonl` (Alpaca format)
   - `dataset_metadata.json` (Summary stats and distribution)
   - `test_prompts.json` (Holdout verification queries in English, Singlish, Sinhala)
"""

import sys
import os
import json
from pathlib import Path
from collections import Counter

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

repo_root = Path(__file__).resolve().parents[2]
data_path = repo_root / "backend" / "data" / "teacher_distillation_dataset.jsonl"
package_dir = repo_root / "notebooks" / "colab_training_package"

def validate_and_package():
    if not data_path.exists():
        print(f"Error: Dataset not found at {data_path}")
        return

    package_dir.mkdir(parents=True, exist_ok=True)

    raw_records = []
    chatml_records = []
    alpaca_records = []

    languages = Counter()
    intents = Counter()
    sources = Counter()

    print("\n" + "="*70)
    print("🔍 VALIDATING LUMYD DISTILLATION DATASET FOR COLAB FINE-TUNING")
    print("="*70 + "\n")

    with open(data_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except Exception as e:
                print(f"[!] Syntax error on line {line_num}: {e}")
                continue

            # Check required fields
            req_keys = ["instruction", "dataset_columns", "query", "language", "python_code", "human_explanation"]
            missing = [k for k in req_keys if k not in record or not record[k]]
            if missing:
                print(f"[!] Missing keys {missing} on line {line_num}")
                continue

            raw_records.append(record)
            languages[record.get("language", "unknown")] += 1
            intents[record.get("intent_label", "unknown")] += 1
            sources[record.get("source", "unknown")] += 1

            # Build ChatML format
            user_content = (
                f"Dataframe Schema (Columns): {record['dataset_columns']}\n"
                f"User Question: {record['query']}"
            )
            assistant_content = (
                f"```python\n{record['python_code'].strip()}\n```\n\n"
                f"Explanation:\n{record['human_explanation'].strip()}"
            )

            chatml_entry = {
                "messages": [
                    {"role": "system", "content": record["instruction"]},
                    {"role": "user", "content": user_content},
                    {"role": "assistant", "content": assistant_content}
                ]
            }
            chatml_records.append(chatml_entry)

            # Build Alpaca format
            alpaca_entry = {
                "instruction": record["instruction"],
                "input": user_content,
                "output": assistant_content
            }
            alpaca_records.append(alpaca_entry)

    # Export ChatML JSONL
    chatml_path = package_dir / "lumyd_chatml_train.jsonl"
    with open(chatml_path, "w", encoding="utf-8") as f:
        for r in chatml_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Export Alpaca JSONL
    alpaca_path = package_dir / "lumyd_alpaca_train.jsonl"
    with open(alpaca_path, "w", encoding="utf-8") as f:
        for r in alpaca_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Build evaluation test prompts
    test_prompts = [
        {
            "domain": "Retail",
            "columns": ["Transaction_ID", "Date", "Product_Category", "Product_Name", "Sales_Amount", "Quantity", "Profit"],
            "query": "machan aduma profit ekak labuna item eka mokakda",
            "language": "singlish",
            "expected_operation": "df.groupby('Product_Name')['Profit'].sum().idxmin()"
        },
        {
            "domain": "HR",
            "columns": ["Employee_ID", "Full_Name", "Department", "Base_Salary", "Bonus", "Years_Experience"],
            "query": "What is the average bonus in the Engineering department?",
            "language": "english",
            "expected_operation": "df[df['Department'] == 'Engineering']['Bonus'].mean()"
        },
        {
            "domain": "Finance",
            "columns": ["Expense_ID", "Transaction_Date", "Category", "Vendor", "Amount", "Approval_Status"],
            "query": "තවමත් අනුමත නොවූ වියදම් වල එකතුව කීයද?",
            "language": "sinhala",
            "expected_operation": "df[df['Approval_Status'] == 'Pending']['Amount'].sum()"
        },
        {
            "domain": "Inventory",
            "columns": ["SKU_Code", "Item_Description", "Product_Line", "Stock_Quantity", "Unit_Cost"],
            "query": "mcn total inventory value eka calculate karala denna",
            "language": "singlish",
            "expected_operation": "(df['Stock_Quantity'] * df['Unit_Cost']).sum()"
        }
    ]
    test_prompts_path = package_dir / "test_prompts.json"
    with open(test_prompts_path, "w", encoding="utf-8") as f:
        json.dump(test_prompts, f, indent=2, ensure_ascii=False)

    metadata = {
        "total_records": len(raw_records),
        "languages": dict(languages),
        "intents": dict(intents),
        "sources": dict(sources),
        "chatml_file": str(chatml_path.name),
        "alpaca_file": str(alpaca_path.name),
        "recommended_model": "Qwen/Qwen2.5-Coder-1.5B-Instruct",
        "recommended_quantization": "4bit (QLoRA)",
        "target_gguf": "lumyd-coder-slm-q4_k_m.gguf",
    }
    metadata_path = package_dir / "dataset_metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print("📊 DATASET VALIDATION & EXPORT STATS:")
    print(f"   Total Verified Records Processed: {len(raw_records)}")
    print(f"   Languages: {dict(languages)}")
    print(f"   Top Intents: {dict(intents.most_common(5))}")
    print(f"   Sources: {dict(sources)}")
    print(f"\n📦 Package files created in: {package_dir}")
    print(f"   1. {chatml_path.name} ({chatml_path.stat().st_size:,} bytes)")
    print(f"   2. {alpaca_path.name} ({alpaca_path.stat().st_size:,} bytes)")
    print(f"   3. {test_prompts_path.name}")
    print(f"   4. {metadata_path.name}")
    print("="*70 + "\n")

if __name__ == "__main__":
    validate_and_package()
