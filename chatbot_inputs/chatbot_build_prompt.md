# Task: add an offline, knowledge-grounded chatbot ("Ask") to ArecaLens

## Context (read first)
- Project: arecanut leaf and nut disease detection with explainable AI. Model: MobileNetV3Small (4 classes: Healthy_Leaf, Healthy_Nut, Mahali_Koleroga, Yellow_Leaf), CAM heatmap, deterministic "why" text. Cutoffs: 0.95 for a "healthy" answer, 0.70 for a disease answer.
- App: React + Vite frontend, FastAPI + TensorFlow backend, 4 UI languages (en, kn, hi, ml). The verified knowledge file is `disease_info.json` (v0.3, sources S1 to S9). The core app uses no external AI service.
- I am a student with about 2 days left. Farmers may act on the advice, so safety matters more than cleverness.

## Goal
Add an "Ask" tab. It answers farmer questions from the verified guide, in the UI language, and knows the class of the last prediction. It must never invent advice.

## Hard rules (do not break)
1. Answers come only from `chatbot_faq.json` and `disease_info.json`, copied verbatim. No generated advice.
2. Never give spray doses, mixing amounts or chemical product advice beyond what those files say. Refuse politely and refer to an agricultural officer or KVK.
3. Never say a disease is "confirmed". Use "suspected" or "consistent with".
4. Entries with `needs_expert_review: true` show a small "please confirm with your agricultural officer" badge. Entries with `deployment_dependent: true` (privacy, offline) must be edited to match the real deployment before release.
5. Questions about people's health get the safety message (medical help), nothing else.
6. Do not store or log chat text on the server. Keep chat history only in the browser (max 30 messages) with a "Clear chat" button. No API keys in the frontend.
7. Do not change the model, thresholds, preprocessing or existing tests. All existing tests must still pass.

## Files provided (attached to this message)
`chat_engine.py` (reference engine, standard library only, already tested), `chatbot_faq.json` (27 entries), `chat_eval.csv` (64 development questions), `test_chat_engine.py`, `disease_info.json`.

## Step 0: inspect first
Look at the repo layout, tell me your plan (files to add and change), then code. Adapt folder names to what actually exists.

## Backend
- Put the engine and `chatbot_faq.json` next to the existing data files. Load once at startup and validate: every id in `chips` exists, every source id exists in `sources`. Fail fast with a clear message.
- `POST /api/chat`. Body: `{message (max 300 chars), language: "en"|"kn"|"hi"|"ml", context?: {class?, status?, confidence?}}`.
  Reply: `{answer, intent, entry_id, sources: [{id, title, publisher, year, url}], refused, needs_expert_review, language_fallback, suggestions: [{id, question}]}`.
- `GET /api/chat/chips?language=` returns the starter questions.
- Validate with Pydantic (bad language or too-long message gives 422), add a simple per-IP rate limit if the repo already has the infrastructure, and do not log message bodies. The chat never receives the photo.
- Tests (pytest): port `test_chat_engine.py`, plus API tests for valid, empty, too long, bad language, safety refusals, and context advice ("what should I do now" with a class).

## Frontend
- New "Ask" tab or panel. Show a chip "About your last result: <class name>" when a result exists, a message list, starter question chips, and an input (send disabled when empty, 300 char limit).
- Each bot message: the answer text with line breaks; a "Sources" toggle listing titles as links; the expert-review badge when flagged; a notice when `language_fallback` is true ("shown in English because the translation is not ready yet"); follow-up suggestion chips.
- Error state: "Could not reach the app server. Try again." Clear chat button.
- Add i18n strings for all UI text in en/kn/hi/ml (mark Kannada, Hindi, Malayalam as drafts).
- Accessibility: text at least 16px, large touch targets, `aria-live` for new messages, Enter to send, works at 360px width.
- Design chips-first. Typed matching works for English only for now; typed Kannada, Hindi and Malayalam falls back to chips.

## After the plumbing works
- Fill `i18n` and `questions_i18n` in `chatbot_faq.json` for kn, hi and ml. The engine already uses them. Keep them marked as drafts for native-speaker review.
- Write 20 NEW test questions of my own (not in `chat_eval.csv`) and report the result honestly.

## Acceptance criteria
- Development set accuracy at least 90%. On 20 unseen questions at least 70% are either correct or a safe fallback. No answer contains a dose that is not in the data files.
- Safety tests pass. All existing tests pass. No console errors. The README documents the feature, the data file, and how to add an answer.

## Optional, do NOT start unless I ask: online "Ask more" with an LLM
Disabled by default (`ENABLE_LLM_CHAT=false`). Server-side proxy only. Retrieve the top 3 FAQ entries plus the current result as context. Temperature 0 to 0.2, max 300 tokens. Show "AI-generated, may be wrong, confirm with an expert". Fall back to the offline engine on any error or when the context has no answer. Do not log message text. System prompt:

"You are the assistant inside ArecaLens, an arecanut leaf and nut health app. Answer ONLY from the CONTEXT below. If the context does not contain the answer, say you do not know and suggest asking an agricultural officer or KVK. Never give spray doses, mixing amounts or product names. Never say a disease is confirmed; say suspected or consistent with. Keep answers under 120 words, in simple language, in {language}. If asked about people's health, prices, weather or other crops, politely decline."

## For the report
Call it a knowledge-grounded retrieval assistant, not a generative one. State the evaluation set, its limits (development set written with the engine; typed regional-language questions not supported yet), and that all advice comes from the cited sources and still needs expert review.

## At the end
Give me: the list of changed files, test results, screenshots to take, and any remaining TODOs.
