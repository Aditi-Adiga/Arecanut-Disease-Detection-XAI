# ArecaLens Continuation Roadmap

This document outlines the scheduled work breakdown following the completion of Session 0+ (core offline chatbot verification, chip deduplication, line endings, and evaluation write-up).

## Remaining Sessions Order

### Session B: Online "Ask more" (Second Priority)
- Implement backend LLM proxy in `backend/chat_proxy.py` / `POST /api/chat/ask-more`.
- Configured via server-only env variables (`ENABLE_LLM_CHAT=1`, `CHATBOT_API_KEY`).
- Server-side safety post-checks: scan LLM response with `_DOSE` regex to block any hallucinated spray doses or mixing rates.
- Strict 15-second timeout and 120-word response constraint.
- Unit and integration tests (mocked responses only).
- Manual smoke test with real question using fresh provider key (key kept strictly out of git/frontend).
- Commit: `feat(chat): online ask-more proxy with safety post-checks`

### Session C: Flutter Mobile Shell
- Initialize Flutter application in `mobile/`.
- Core screens: Scan / Home screen, Results view with CAM overlay viewer, Guide screen, History screen (local SQLite/shared prefs), Settings / Language switcher (`en`, `kn`, `hi`, `ml`).
- Online screening client pointing to FastAPI `POST /api/predict`.
- Commit: `feat(mobile): flutter shell and online screening`

### Session D: Dart Chat Engine with Golden Parity
- Generate reference golden file with Python tool (`tools/make_chat_golden.py`).
- Implement pure Dart deterministic chat engine in `mobile/lib/chat/chat_engine.dart` with bundled `chatbot_faq.json` and `disease_info.json`.
- Golden parity unit test in Flutter verifying 100% agreement with Python chat engine outputs.
- Build mobile "Ask" tab UI.
- Commit: `feat(mobile): dart chat engine and ask screen`

### Session E: Mobile Offline Screening
- Evaluate `v3small_probs_features.tflite` model inference in Flutter.
- Verify numeric parity against Keras reference outputs.
- If parity passes, enable offline camera/gallery screening; if parity fails or cannot be verified, keep behind disabled feature flag and document.
- Commit: `feat(mobile): offline screening evaluation`

### Session F: UI Polish, Full Verification, and Final Report
- Final safe CSS adjustments for mobile and web.
- Full automated test suite run across backend, frontend, and mobile.
- Generate `FINAL_REPORT.md` including safety confirmations, model parity summary, test metrics, and user API key revocation reminder.
- Commit: `docs: final report and verification`
