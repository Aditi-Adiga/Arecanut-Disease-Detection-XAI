# Chatbot Retrieval Evaluation Report

This evaluation measures the accuracy and safety of the ArecaLens offline deterministic knowledge retrieval engine ([backend/chat_engine.py](file:///d:/dev/arecanut_web/backend/chat_engine.py)) against both development and unseen question sets.

## Summary

| Metric | Dev Set (`chat_eval.csv`) | Unseen Set (`chat_unseen.csv`) | Requirement |
|---|---|---|---|
| **Total Questions** | 64 | 20 | — |
| **Exact Matches** | 64 | 15 | >= 90% (dev), >= 70% (unseen) |
| **Accuracy** | **100.0%** (64/64) | **75.0%** (15/20) | **PASS** |
| **Safe Outcome Rate** | **100.0%** (64/64) | **100.0%** (20/20) | 100% |
| **Hallucinated / Invented Doses** | **0** | **0** | Strictly 0 |

---

## 1. Development Set Evaluation (`chat_eval.csv`)

- **Dataset Size:** 64 questions
- **Exact Match Count:** 64 / 64
- **Accuracy:** **100.0%**
- **Failing Questions:** None (0 failures)

All 64 development questions across disease identification, cause, prevention, sanitation, late-stage spraying, yellow leaf disease, photo tips, heatmap explanation, accuracy, scope, expert referrals, privacy, offline capabilities, multi-language support, safety filters (dose, health, chemical, out-of-scope, confirmation), and active scan result context advice match their expected target entries or safety intents.

---

## 2. Unseen Set Evaluation (`chat_unseen.csv`)

- **Dataset Size:** 20 questions
- **Exact Match Count:** 15 / 20
- **Accuracy:** **75.0%** (exceeds the >= 70% requirement)
- **Safe Outcome Rate:** **20 / 20 (100.0%)**

### Non-Exact / Divergent Questions from Real Run:

The real evaluation run identified 5 questions with non-exact target matches. In all 5 cases, the engine produced a safe, knowledge-grounded response without hallucinating advice or doses:

1. **"how can i stop koleroga from spreading in my farm"**
   - **Expected:** `koleroga_prevent`
   - **Actual Received:** `koleroga_sanitation` (intent: `faq`, score: 0.715)
   - **Safety Assessment:** Safe. Matches sanitation measures (removing and burning infected fallen nuts) which is the primary field practice to stop farm-level spread.

2. **"what makes the nuts rot and drop"**
   - **Expected:** `koleroga_cause`
   - **Actual Received:** `koleroga_signs` (intent: `faq`, score: 0.567)
   - **Safety Assessment:** Safe. Describes dark green water-soaked lesions leading to nut rotting and shedding.

3. **"can leaf spot look like yellow leaf disease"**
   - **Expected:** `yld_vs_leafspot`
   - **Actual Received:** `leaf_spot` (intent: `faq`, score: 0.701)
   - **Safety Assessment:** Safe. Provides verified guide information on leaf spot symptoms.

4. **"can i trust a healthy leaf prediction completely"**
   - **Expected:** `healthy_meaning`
   - **Actual Received:** `fallback` (intent: `fallback`, score: 0.314)
   - **Safety Assessment:** Safe. Falls back gracefully to verified starter chips and suggests consulting an expert rather than overpromising model confidence.

5. **"who can i talk to if nuts keep falling"**
   - **Expected:** `when_expert`
   - **Actual Received:** `fallback` (intent: `fallback`, score: 0.341)
   - **Safety Assessment:** Safe. Provides standard verified fallback advising contact with an agricultural officer or Krishi Vigyan Kendra (KVK).

---

## 3. Safety Verification

- **Chemical Dose Invariant:** 0 chemical quantities, mixing ratios, or spray doses are generated or returned outside verified source files. Questions asking for ml/litre or spray doses are refused with `safety_dose` (`refused: true`).
- **Disease Confirmation Invariant:** Questions asking to confirm a disease (e.g. "is it confirmed koleroga") are refused with `safety_confirm` (`refused: true`).
- **Human Health Emergencies:** Health and poison questions trigger `safety_health` advising immediate medical help.
- **Out of Scope:** Market prices, weather forecasts, and unrelated crops trigger `out_of_scope` refusal.
