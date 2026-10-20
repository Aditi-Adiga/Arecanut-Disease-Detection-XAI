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
    safety_texts = {v for v in faq["safety"].values() if isinstance(v, str)}
    texts = {e["answer"] for e in faq["entries"]} | safety_texts | {faq["fallback"]["text"]}
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


# ---------- Multilingual safety and fallback tests (bug fix) -----------------

_SAFETY_QUERIES = [
    ("how many ml per litre", "safety_dose"),
    ("which fungicide should i use", "safety_chemical"),
    ("i have a fever", "safety_health"),
    ("what is the price of areca today", "out_of_scope"),
    ("is it confirmed koleroga", "safety_confirm"),
]


def test_safety_messages_translated_for_kn():
    engine, faq, _ = get_engine()
    en_texts = {
        "safety_dose": faq["safety"]["dose"],
        "safety_chemical": faq["safety"]["chemical"],
        "safety_health": faq["safety"]["health"],
        "out_of_scope": faq["safety"]["out_of_scope"],
        "safety_confirm": faq["safety"]["confirm"],
    }
    for question, expected_intent in _SAFETY_QUERIES:
        out = engine.answer(question, "kn")
        assert out["intent"] == expected_intent, f"intent mismatch for '{question}'"
        assert out["refused"] is True
        # Answer must NOT be English
        assert out["answer"] != en_texts[expected_intent], (
            f"Safety reply for '{question}' was English despite language=kn"
        )
        # No fallback flag — we have a kn translation
        assert out["language_fallback"] is False, (
            f"language_fallback should be False for '{question}' in kn"
        )


def test_safety_messages_translated_for_hi():
    engine, faq, _ = get_engine()
    for question, expected_intent in _SAFETY_QUERIES:
        out = engine.answer(question, "hi")
        assert out["intent"] == expected_intent
        assert out["refused"] is True
        assert out["language_fallback"] is False


def test_safety_messages_translated_for_ml():
    engine, faq, _ = get_engine()
    for question, expected_intent in _SAFETY_QUERIES:
        out = engine.answer(question, "ml")
        assert out["intent"] == expected_intent
        assert out["refused"] is True
        assert out["language_fallback"] is False


def test_fallback_translated_for_regional_languages():
    """An out-of-vocabulary question must get the translated fallback, not English."""
    engine, faq, _ = get_engine()
    en_fallback = faq["fallback"]["text"]
    for lang in ("kn", "hi", "ml"):
        out = engine.answer("xyzzy frobnicator", lang)
        assert out["intent"] == "fallback"
        assert out["answer"] != en_fallback, (
            f"Fallback was English for language={lang}"
        )
        assert out["language_fallback"] is False


def test_safety_english_has_no_fallback_flag():
    """English safety/fallback replies must not set language_fallback."""
    engine, _, _ = get_engine()
    for question, _ in _SAFETY_QUERIES:
        out = engine.answer(question, "en")
        assert out["language_fallback"] is False
    out = engine.answer("xyzzy frobnicator", "en")
    assert out["language_fallback"] is False
