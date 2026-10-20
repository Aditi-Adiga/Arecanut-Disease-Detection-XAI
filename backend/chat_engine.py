"""Offline, deterministic chat engine for ArecaLens.

No external AI service. Every answer is copied word for word from chatbot_faq.json or from the
verified disease_info.json, so the bot cannot invent advice. Pure Python (standard library only).

Usage:
    engine = ChatEngine(json.load(open("chatbot_faq.json", encoding="utf-8")),
                        info=json.load(open("disease_info.json", encoding="utf-8")))
    reply = engine.answer("how do I prevent mahali", language="en",
                          context={"class": "Mahali_Koleroga", "status": "suspected"})
"""
import math
import re
import unicodedata
from collections import Counter

_TOKEN = re.compile(r"\w+", re.UNICODE)
_STOP = set("a an the is are was were be been am do does did to of in on at for from with by and or if it its this that "
            "these those i me my we our you your can could should would will shall may might please tell about any "
            "there here have has had get got so very much".split())
_SYN = {
    "mahali": "koleroga", "kole": "koleroga", "kolleroga": "koleroga", "mahaali": "koleroga",
    "fell": "fall", "dropp": "fall", "drop": "fall", "shedd": "fall", "shed": "fall",
    "rott": "rot", "rotten": "rot", "rot": "rot", "decay": "rot",
    "cure": "treatment", "treat": "treatment", "remedy": "treatment", "medicine": "treatment",
    "solution": "treatment", "fix": "treatment",
    "protect": "prevention", "prevent": "prevention", "avoid": "prevention", "stop": "prevention",
    "pictur": "photo", "picture": "photo", "image": "photo", "pic": "photo", "camera": "photo",
    "color": "colour", "colour": "colour",
    "reliable": "accuracy", "accurate": "accuracy", "trust": "accuracy", "mistake": "wrong",
    "uncertain": "unsure", "diseas": "disease", "symptom": "sign", "leav": "leaf", "leaves": "leaf",
    "officer": "expert", "kvk": "expert", "scientist": "expert", "doctor": "expert",
    "internet": "offline", "network": "offline", "signal": "offline", "connection": "offline",
    "pest": "pests", "insect": "pests", "hopper": "pests",
}
_TOPIC = {"koleroga", "yellow", "spot", "bordeaux", "bud", "foot", "nut", "leaf", "crown", "spindle", "trunk"}

_DOSE = re.compile(r"\b(dose|dosage|how (many|much)\b.*\b(ml|gram|grams|g|kg|litre|liter)|per (litre|liter|acre|hectare|palm)|"
                   r"\d+\s*(ml|mg|g|kg|ppm)\b|ppm|mixing ratio|concentration)\b", re.I)
_CHEM = re.compile(r"\b(antibiotic|tetracycline|dimethoate|insecticide|pesticide|fungicide|mancozeb|metalaxyl|"
                   r"copper oxychloride|weedicide|herbicide|which (chemical|spray|product|brand))\b", re.I)
_HEALTH = re.compile(r"\b(fever|cough|headache|pregnan\w*|snake|poison\w*|swallow\w*|hospital|tablet|vomit\w*|"
                     r"my (child|son|daughter|baby|wife|husband)|i feel (sick|unwell|dizzy))\b", re.I)
_OUT = re.compile(r"\b(price|rate today|market|weather|forecast|will it rain|rain tomorrow|subsidy|loan|insurance|coconut|paddy|rice|banana|"
                  r"pepper|cocoa|rubber|tomato|cow|goat)\b", re.I)
_CONFIRM = re.compile(r"\b(confirm\w*|diagnos\w*|100 ?%|for sure|certain)\b", re.I)
_ADVICE = re.compile(
    r"\b(what (should|do|can|shall) i do|what now|next step|what to do|advice|how (do|can|to) (i )?(treat|fix|save))\b|"
    r"(ಈಗ ನಾನು ಏನು ಮಾಡಬೇಕು|ಮುಂದಿನ ಕ್ರಮ|ಮುಂದೆ ಏನು ಮಾಡಬೇಕು|ಸಲಹೆ)|"
    r"(अब मुझे क्या करना चाहिए|अगला कदम|क्या करूँ|सलाह)|"
    r"(ഇനി ഞാൻ എന്താണ് ചെയ്യേണ്ടത്|അടുത്ത നടപടി|എന്ത് ചെയ്യണം|ഉപദേശം)",
    re.I | re.UNICODE,
)


def _stem(t):
    for suf in ("ing", "ed", "es", "s"):
        if len(t) > len(suf) + 3 and t.endswith(suf):
            return t[: -len(suf)]
    return t


def tokens(text):
    text = unicodedata.normalize("NFKC", text).lower()
    out = []
    for t in _TOKEN.findall(text):
        if t in _STOP:
            continue
        t = _stem(t)
        out.append(_SYN.get(t, t))
    return out


class ChatEngine:
    def __init__(self, faq, info=None, min_score=0.5):
        self.faq, self.info, self.min_score = faq, info, min_score
        self.entries = {e["id"]: e for e in faq["entries"]}
        self.kw, self.qt = {}, {}
        for e in faq["entries"]:
            kw = set()
            for k in e["keywords"]:
                kw.update(tokens(k))
            qt = set()
            for q in e["questions"] + sum(e.get("questions_i18n", {}).values(), []):
                qt.update(tokens(q))
            self.kw[e["id"]], self.qt[e["id"]] = kw, qt
        df = Counter()
        for eid in self.entries:
            df.update(self.kw[eid] | self.qt[eid])
        n = len(self.entries)
        self.idf = {t: math.log((n + 1) / (c + 0.5)) + 0.1 for t, c in df.items()}

    # ---- helpers -------------------------------------------------------------------------
    def _chips(self, lang, ids=None):
        out = []
        for eid in (ids or self.faq["chips"]):
            e = self.entries[eid]
            qs = e.get("questions_i18n", {}).get(lang) or e["questions"]
            out.append({"id": eid, "question": qs[0]})
        return out

    def _reply(self, answer, intent, entry=None, sources=(), score=0.0, refused=False, lang="en",
                suggestions=None, i18n_map=None):
        """Build a reply dict.  *i18n_map* is an optional {lang: text} dict used
        to translate safety/fallback strings that are not stored in an entry."""
        fallback_lang = False
        if lang != "en":
            if entry is not None:
                # FAQ entry: use its i18n block
                translated = (entry.get("i18n") or {}).get(lang)
                if translated:
                    answer = translated
                else:
                    fallback_lang = True
            elif i18n_map is not None:
                # Safety / fallback: use the caller-supplied map
                translated = i18n_map.get(lang)
                if translated:
                    answer = translated
                else:
                    fallback_lang = True
            else:
                fallback_lang = True
        return {"answer": answer, "intent": intent, "entry_id": entry["id"] if entry else None,
                "sources": list(sources), "score": round(score, 3), "refused": refused,
                "needs_expert_review": bool(entry and entry.get("needs_expert_review")),
                "language_fallback": fallback_lang, "suggestions": suggestions or self._chips(lang)}

    def _current_result_advice(self, ctx, lang):
        info, cls = self.info, ctx.get("class")
        if not info or cls not in info["classes"]:
            return None
        ci = info["classes"][cls]
        parts, src = [ci["summary"]["text"]], set(ci["summary"].get("sources", []))
        todo = ci.get("what_to_do", [])
        if todo:
            parts.append("What to do:\n" + "\n".join("- " + x["text"] for x in todo))
            for x in todo:
                src.update(x.get("sources", []))
        if ci.get("limits"):
            parts.append(ci["limits"]["text"])
        return self._reply("\n\n".join(parts), "current_result_advice", sources=sorted(src), lang=lang)

    def answer_by_id(self, entry_id, language="en", context=None):
        """Direct entry lookup: used when user clicks a known chip.
        
        Returns the entry in the requested language (or English fallback with
        language_fallback=True if translation is missing).
        """
        if entry_id not in self.entries:
            return self.answer("", language=language, context=context)
        e = self.entries[entry_id]
        same = [x for x, ee in self.entries.items() if ee["topic"] == e["topic"] and x != e["id"]][:3]
        return self._reply(
            e["answer"],
            "faq",
            entry=e,
            sources=e["sources"],
            score=1.0,
            lang=language,
            suggestions=self._chips(language, same) if same else None,
        )

    def top_k(self, message, k=3, context=None):
        """Retrieve top k FAQ entries matching message, reusing engine scoring.
        
        Returns a list of up to k FAQ entry dicts.
        """
        msg = (message or "").strip()
        ctx = context or {}
        qtok = tokens(msg)
        known = [t for t in set(qtok) if t in self.idf]
        if not known:
            return [self.entries[cid] for cid in self.faq.get("chips", [])[:k] if cid in self.entries]

        total = sum(self.idf[t] for t in known)
        scored = []
        for eid, e in self.entries.items():
            if e.get("require") and not all(t in set(qtok) for t in tokens(" ".join(e["require"]))):
                continue
            matched = [t for t in known if t in self.kw[eid] or t in self.qt[eid]]
            if not matched:
                continue
            w = sum(self.idf[t] * (1.0 if t in self.kw[eid] else 0.6) for t in matched)
            score = (w / total) * min(1.0, 0.5 + 0.25 * len(matched))
            if ctx.get("class") in e.get("classes", []):
                score *= 1.15
            scored.append((score, e))

        scored.sort(key=lambda x: x[0], reverse=True)
        top = [e for _, e in scored[:k]]
        if len(top) < k:
            for cid in self.faq.get("chips", []):
                if len(top) >= k:
                    break
                ce = self.entries.get(cid)
                if ce and ce not in top:
                    top.append(ce)
        return top[:k]

    # ---- main entry ----------------------------------------------------------------------
    def answer(self, message, language="en", context=None):
        msg = (message or "").strip()
        ctx = context or {}
        fb = self.faq["fallback"]
        s = self.faq["safety"]
        if not msg:
            return self._reply(fb["text"], "fallback", lang=language,
                               i18n_map=fb.get("i18n"))
        low = msg.lower()
        if _HEALTH.search(low):
            return self._reply(s["health"], "safety_health", refused=True, lang=language,
                               i18n_map=s.get("health_i18n"))
        if re.search(r"bordeaux|bordo", low) and (_DOSE.search(low) or re.search(r"copper|sulphate|lime|make|prepar", low)):
            return self._reply(self.entries["bordeaux_how"]["answer"], "bordeaux_how",
                               entry=self.entries["bordeaux_how"], sources=self.entries["bordeaux_how"]["sources"], lang=language)
        if _DOSE.search(low):
            return self._reply(s["dose"], "safety_dose", refused=True, lang=language,
                               i18n_map=s.get("dose_i18n"))
        if _CHEM.search(low):
            return self._reply(s["chemical"], "safety_chemical", refused=True, lang=language,
                               i18n_map=s.get("chemical_i18n"))
        if _OUT.search(low):
            return self._reply(s["out_of_scope"], "out_of_scope", refused=True, lang=language,
                               i18n_map=s.get("out_of_scope_i18n"))
        qtok = tokens(msg)
        if _CONFIRM.search(low):
            return self._reply(s["confirm"], "safety_confirm", refused=True, lang=language,
                               i18n_map=s.get("confirm_i18n"))
        if ctx.get("class") and _ADVICE.search(low) and not (set(qtok) & _TOPIC):
            r = self._current_result_advice(ctx, language)
            if r:
                return r
        known = [t for t in set(qtok) if t in self.idf]
        if not known:
            return self._reply(fb["text"], "fallback", lang=language,
                               i18n_map=fb.get("i18n"))
        total = sum(self.idf[t] for t in known)
        best, second = (None, 0.0), 0.0
        for eid, e in self.entries.items():
            if e.get("require") and not all(t in set(qtok) for t in tokens(" ".join(e["require"]))):
                continue
            matched = [t for t in known if t in self.kw[eid] or t in self.qt[eid]]
            if not matched:
                continue
            w = sum(self.idf[t] * (1.0 if t in self.kw[eid] else 0.6) for t in matched)
            score = (w / total) * min(1.0, 0.5 + 0.25 * len(matched))
            if ctx.get("class") in e.get("classes", []):
                score *= 1.15
            if best[0] is None or score > best[1]:
                second = best[1]
                best = (eid, score)
            elif score > second:
                second = score
        if best[0] is None or best[1] < self.min_score:
            return self._reply(fb["text"], "fallback", score=best[1], lang=language,
                               i18n_map=fb.get("i18n"))
        e = self.entries[best[0]]
        same = [x for x, ee in self.entries.items() if ee["topic"] == e["topic"] and x != e["id"]][:3]
        return self._reply(e["answer"], "faq", entry=e, sources=e["sources"], score=best[1], lang=language,
                           suggestions=self._chips(language, same) if same else None)
