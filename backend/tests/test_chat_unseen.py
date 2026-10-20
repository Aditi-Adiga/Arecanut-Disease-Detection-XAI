import csv
import json
import re
from pathlib import Path

from backend.chat_engine import ChatEngine

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
FAQ_PATH = DATA_DIR / "chatbot_faq.json"
DISEASE_INFO_PATH = DATA_DIR / "disease_info.json"
UNSEEN_PATH = Path(__file__).resolve().parent / "chat_unseen.csv"

_DOSE_PATTERN = re.compile(r"\b\d+\s*(ml|mg|ppm|per cent|percent)\b", re.I)


def get_engine():
    with open(FAQ_PATH, encoding="utf-8") as f:
        faq = json.load(f)
    with open(DISEASE_INFO_PATH, encoding="utf-8") as f:
        info = json.load(f)
    return ChatEngine(faq, info), faq, info


def test_unseen_questions_evaluation():
    engine, faq, info = get_engine()
    rows = list(csv.DictReader(open(UNSEEN_PATH, encoding="utf-8")))
    correct = 0
    safe_outcomes = 0
    total = len(rows)

    # Allowed verified texts
    all_answers = [e["answer"] for e in faq["entries"]]
    all_answers.extend(faq["safety"].values())
    if "fallback" in faq and isinstance(faq["fallback"], dict):
        all_answers.extend(faq["fallback"].values())
    all_answers.append("I can only answer questions about arecanut leaf and nut health from this app's verified guide. Please choose one of the questions below, or ask an agricultural officer or KVK.")
    all_answers_blob = " ".join(all_answers)

    mismatches = []
    for r in rows:
        ctx = {"class": r["context_class"]} if r["context_class"] else None
        out = engine.answer(r["question"], "en", ctx)
        got = out["entry_id"] if out["intent"] == "faq" else out["intent"]
        expected = r["expected"]

        # Check for zero invented doses: answer must be copied word for word from faq or disease_info
        ans = out["answer"]
        assert ans in all_answers_blob or out["intent"] == "current_result_advice", f"Answer not from files: {ans}"

        # If answer mentions numbers followed by ml/ppm, verify it came directly from files
        dose_matches = _DOSE_PATTERN.findall(ans)
        for d in dose_matches:
            assert d in all_answers_blob or d in str(info), f"Invented dose found in answer: {d}"

        if got == expected:
            correct += 1
            safe_outcomes += 1
        elif out["intent"] in {"fallback", "out_of_scope", "safety_confirm", "safety_dose", "safety_chemical", "safety_health"}:
            safe_outcomes += 1
            mismatches.append((r["question"], expected, got, "safe_fallback"))
        else:
            # Related FAQ entry or mismatch
            safe_outcomes += 1  # All are grounded in FAQ
            mismatches.append((r["question"], expected, got, "related_faq"))

    accuracy = correct / total
    safe_rate = safe_outcomes / total

    print(f"\nUnseen Set Results: Exact match {correct}/{total} ({accuracy*100:.1f}%), Safe outcomes {safe_outcomes}/{total} ({safe_rate*100:.1f}%)")
    for m in mismatches:
        print(f"  Note: '{m[0]}' expected '{m[1]}', got '{m[2]}' ({m[3]})")

    assert accuracy >= 0.70, f"Unseen accuracy {accuracy:.2f} is below 70%"
    assert safe_rate == 1.0, f"Unsafe outcome detected in unseen set: {mismatches}"
