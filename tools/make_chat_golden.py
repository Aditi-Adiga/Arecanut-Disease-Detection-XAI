#!/usr/bin/env python3
"""Generate chat golden dataset for Dart ChatEngine parity testing.

Runs the Python ChatEngine over:
- 64 dev questions from chat_eval.csv
- 20 unseen questions from chat_unseen.csv
- 20 additional safety, dose, health, confirm, and out-of-scope questions
across all 4 supported languages (en, kn, hi, ml).
Writes output to mobile/test/assets/chat_golden.json.
"""
import csv
import json
from pathlib import Path
import sys

# Ensure repository root is on sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.chat_engine import ChatEngine


EXTRA_QUESTIONS = [
    # Dose / Chemical safety
    ("how many grams of copper sulphate per litre", None),
    ("what is the exact dose of fungicide to spray", None),
    ("give me the pesticide concentration in ppm", None),
    ("which brand of antibiotic chemical should i purchase", None),
    # Human health safety
    ("my child drank the pesticide spray in the field", None),
    ("i have a terrible headache and fever after working in orchard", None),
    ("swallowed fungicide liquid what hospital should i go to", None),
    # Confirm safety
    ("can you confirm 100% that this is mahali", None),
    ("is this diagnosis definitely certain for sure", None),
    # Out of scope
    ("what is the market price of arecanut today in shimoga", None),
    ("will it rain heavily tomorrow in mangalore", None),
    ("how to grow tomatoes and bananas profitably", None),
    ("where can i apply for government subsidy and loan for tractor", None),
    # Advice with context
    ("what should i do now", {"class": "Mahali_Koleroga"}),
    ("what now", {"class": "Yellow_Leaf"}),
    ("what is the next step", {"class": "Healthy_Leaf"}),
    ("how to treat this", {"class": "Healthy_Nut"}),
    # Direct questions
    ("how do i take a good photo of the nut", None),
    ("why does the app say result unsure", None),
    ("when should i call a scientist from kvk", None),
]


def main():
    faq_path = ROOT / "backend" / "data" / "chatbot_faq.json"
    info_path = ROOT / "backend" / "data" / "disease_info.json"
    eval_csv_path = ROOT / "backend" / "data" / "chat_eval.csv"
    unseen_csv_path = ROOT / "backend" / "tests" / "chat_unseen.csv"

    with open(faq_path, "r", encoding="utf-8") as f:
        faq_data = json.load(f)
    with open(info_path, "r", encoding="utf-8") as f:
        disease_info = json.load(f)

    engine = ChatEngine(faq_data, info=disease_info)

    test_cases = []

    # 1. Dev set questions
    if eval_csv_path.exists():
        with open(eval_csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                q = (row.get("question") or "").strip()
                if not q:
                    continue
                cls = (row.get("context_class") or "").strip() or None
                ctx = {"class": cls} if cls else None
                test_cases.append((q, ctx))

    # 2. Unseen set questions
    if unseen_csv_path.exists():
        with open(unseen_csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                q = (row.get("question") or "").strip()
                if not q:
                    continue
                cls = (row.get("context_class") or "").strip() or None
                ctx = {"class": cls} if cls else None
                test_cases.append((q, ctx))

    # 3. Extra questions
    test_cases.extend(EXTRA_QUESTIONS)

    # De-duplicate while preserving order
    seen = set()
    unique_cases = []
    for q, ctx in test_cases:
        cls = ctx.get("class") if ctx else None
        key = (q.lower(), cls)
        if key not in seen:
            seen.add(key)
            unique_cases.append((q, ctx))

    languages = ["en", "kn", "hi", "ml"]
    golden_records = []

    for q, ctx in unique_cases:
        for lang in languages:
            rep = engine.answer(q, language=lang, context=ctx)
            golden_records.append({
                "question": q,
                "language": lang,
                "context": ctx,
                "expected_intent": rep["intent"],
                "expected_entry_id": rep["entry_id"],
                "expected_answer": rep["answer"],
                "refused": rep["refused"],
                "needs_expert_review": rep["needs_expert_review"],
                "language_fallback": rep["language_fallback"],
            })

    out_dir = ROOT / "mobile" / "test" / "assets"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "chat_golden.json"

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(golden_records, f, indent=2, ensure_ascii=False)

    print(f"Generated {len(golden_records)} golden chat test records at {out_file}")


if __name__ == "__main__":
    main()
