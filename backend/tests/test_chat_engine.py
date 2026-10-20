import csv
import json
from pathlib import Path

from backend.chat_engine import ChatEngine

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
FAQ_PATH = DATA_DIR / "chatbot_faq.json"
DISEASE_INFO_PATH = DATA_DIR / "disease_info.json"
EVAL_PATH = DATA_DIR / "chat_eval.csv"


def get_engine():
    with open(FAQ_PATH, encoding="utf-8") as f:
        faq = json.load(f)
    with open(DISEASE_INFO_PATH, encoding="utf-8") as f:
        info = json.load(f)
    return ChatEngine(faq, info), faq, info


def test_dev_set_accuracy():
    engine, _, _ = get_engine()
    rows = list(csv.DictReader(open(EVAL_PATH, encoding="utf-8")))
    bad = []
    for r in rows:
        ctx = {"class": r["context_class"]} if r["context_class"] else None
        out = engine.answer(r["question"], "en", ctx)
        got = out["entry_id"] if out["intent"] == "faq" else out["intent"]
        if out["intent"] == "bordeaux_how":
            got = "bordeaux_how"
        if got != r["expected"]:
            bad.append((r["question"], r["expected"], got, out["score"]))
    acc = 1 - len(bad) / len(rows)
    assert acc >= 0.9, f"Accuracy {acc:.2f} < 0.90: {bad}"


def test_never_gives_doses_or_health_advice():
    engine, _, _ = get_engine()
    for q in ["how many ml per litre", "give me the dose", "i have a fever"]:
        assert engine.answer(q)["refused"] is True


def test_every_answer_comes_from_the_files():
    engine, faq, _ = get_engine()
    texts = {e["answer"] for e in faq["entries"]} | set(faq["safety"].values()) | {faq["fallback"]["text"]}
    for e in faq["entries"]:
        out = engine.answer(e["questions"][0])
        if out["intent"] == "faq":
            assert out["answer"] in texts


def test_regional_language_falls_back_to_english_with_flag():
    engine, _, _ = get_engine()
    out = engine.answer("what is bud rot", "kn")
    assert out["language_fallback"] is True
    assert out["answer"]


def test_regional_language_translated_chip_returns_regional_text():
    engine, _, _ = get_engine()
    out = engine.answer("what is mahali", "kn")
    assert out["language_fallback"] is False
    assert out["answer"]


def test_unverified_items_are_flagged():
    engine, _, _ = get_engine()
    assert engine.answer("how to make bordeaux mixture")["needs_expert_review"] is True


def test_specific_content_queries():
    engine, _, _ = get_engine()
    assert engine.answer("do you save my photo")["entry_id"] == "privacy"
    assert engine.answer("which language does the app support")["entry_id"] == "languages"
    assert engine.answer("my areca leaves are turning yellow what is wrong")["entry_id"] == "what_is_yld"

