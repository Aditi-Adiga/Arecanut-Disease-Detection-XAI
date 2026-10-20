"""Run:  python test_chat_engine.py     (or: python -m pytest test_chat_engine.py)
Checks the engine against chat_eval.csv. NOTE: this is a development set written together with the
engine, so its accuracy is optimistic. Add at least 20 NEW questions of your own for an honest test."""
import csv, json, pathlib, sys
from chat_engine import ChatEngine

HERE = pathlib.Path(__file__).parent
faq = json.load(open(HERE / "chatbot_faq.json", encoding="utf-8"))
info = json.load(open(HERE / "disease_info.json", encoding="utf-8"))
engine = ChatEngine(faq, info)

def run():
    rows = list(csv.DictReader(open(HERE / "chat_eval.csv", encoding="utf-8")))
    bad = []
    for r in rows:
        ctx = {"class": r["context_class"]} if r["context_class"] else None
        out = engine.answer(r["question"], "en", ctx)
        got = out["entry_id"] if out["intent"] == "faq" else out["intent"]
        if out["intent"] == "bordeaux_how":
            got = "bordeaux_how"
        if got != r["expected"]:
            bad.append((r["question"], r["expected"], got, out["score"]))
    return rows, bad

def test_dev_set_accuracy():
    rows, bad = run()
    acc = 1 - len(bad) / len(rows)
    assert acc >= 0.9, f"accuracy {acc:.2f}: {bad}"

def test_never_gives_doses_or_health_advice():
    for q in ["how many ml per litre", "give me the dose", "i have a fever"]:
        assert engine.answer(q)["refused"]

def test_every_answer_comes_from_the_files():
    texts = {e["answer"] for e in faq["entries"]} | set(faq["safety"].values()) | {faq["fallback"]["text"]}
    for e in faq["entries"]:
        out = engine.answer(e["questions"][0])
        if out["intent"] == "faq":
            assert out["answer"] in texts

def test_regional_language_falls_back_to_english_with_flag():
    out = engine.answer("what is mahali", "kn")
    assert out["language_fallback"] is True and out["answer"]

def test_unverified_items_are_flagged():
    assert engine.answer("how to make bordeaux mixture")["needs_expert_review"] is True

if __name__ == "__main__":
    rows, bad = run()
    print(f"dev-set accuracy: {len(rows) - len(bad)}/{len(rows)} = {100 * (1 - len(bad) / len(rows)):.1f}%")
    for b in bad:
        print("  MISS:", b)
    for t in [test_never_gives_doses_or_health_advice, test_every_answer_comes_from_the_files,
              test_regional_language_falls_back_to_english_with_flag, test_unverified_items_are_flagged]:
        t(); print("PASS", t.__name__)
    sys.exit(0 if len(bad) / len(rows) <= 0.1 else 1)
