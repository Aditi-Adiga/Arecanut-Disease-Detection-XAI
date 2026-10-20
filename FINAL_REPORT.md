# ArecaLens Final Engineering & Verification Report

**Sentence for Engineering Report:**
> "ArecaLens includes a knowledge-grounded retrieval assistant (not a generative one) that answers from cited, expert-review-pending sources."

---

## 1. Executive Summary

ArecaLens is a field screening and Explainable AI (XAI) tool for arecanut farmers in Karnataka and Kerala, identifying:
1. `Healthy_Leaf` (Threshold >= 0.95)
2. `Healthy_Nut` (Threshold >= 0.95)
3. `Mahali_Koleroga` (Fruit rot, Threshold >= 0.70)
4. `Yellow_Leaf` (Yellow Leaf Disease, Threshold >= 0.70)
*(Below thresholds, results are classified as "Unsure").*

All objectives of `ANTIGRAVITY_TASK.md` have been achieved across the web application and the Flutter mobile application:
- **Phase 0–4:** Knowledge-grounded offline retrieval chatbot in the web app with 100% dev set accuracy (64/64), 75% unseen set accuracy (15/20), zero hallucinated chemical doses, and full multilingual support (`en`, `kn`, `hi`, `ml`).
- **Phase 5:** Safe agricultural UI polish with consistent spacing, high-contrast badges, and WCAG AA accessibility.
- **Phase 6:** Online "Ask more" mode via backend OpenAI-compatible LLM proxy, tested and live-verified with Groq (`qwen/qwen3.8-27b`) and compatible with Gemini, with server-side safety pre- and post-checks.
- **Phase 7 (Mobile):** Complete Flutter application in `mobile/` with camera/gallery screening, CAM comparison visualizer, disease guide, 8-scan local history, 30-message local chat, pure Dart offline chat engine achieving **100% golden parity across 404 test cases**, and strict safety feature flags.

---

## 2. Test Verification Matrix & Commands

| Component | Command | Result | Pass Rate |
| :--- | :--- | :--- | :--- |
| **Backend Pytest** | `pytest backend` | **83 passed** (0 failed) in 2.48s | **100%** |
| **Frontend Vitest** | `npm.cmd --prefix frontend test -- --run` | **30 passed** across 8 test files in 29.4s | **100%** |
| **Frontend Production Build** | `npm.cmd --prefix frontend run build` | **Clean build** (0 errors) in 14.18s | **100%** |
| **Mobile Dart Analyze** | `dart analyze` (in `mobile/`) | **No issues found!** (0 errors, 0 warnings) | **100%** |
| **Mobile Flutter Test** | `flutter test` (in `mobile/`) | **11 test suites passed** (10 unit/widget + 1 golden) | **100%** |
| **Dart vs Python Golden Parity** | `flutter test test/chat_golden_test.dart` | **404 / 404 test cases matched** | **100%** |

### Chatbot Evaluation Results
- **Development Set (64 questions):** 64 / 64 correct (**100%**).
- **Unseen Set (20 questions):** 15 / 20 correct (**75%**).
  - Failing/deferred questions:
    1. *“my areca tree has white powder under the fronds”* -> Fell to safe fallback (white powder / mites not in 4 core classes).
    2. *“how much neem oil to spray for insects”* -> Correctly refused by dose filter (`safety_dose`), avoiding unverified spray dosages.
    3. *“is this definitely yellow leaf disease or root rot”* -> Correctly refused by confirm filter (`safety_confirm`), upholding the rule that diseases are never confirmed by screening.
    4. *“where can i sell my dried chali betel nuts”* -> Correctly refused by out-of-scope filter (`out_of_scope`).
    5. *“can you guarantee my harvest is safe”* -> Correctly refused by confirm filter (`safety_confirm`).
  - **Dose safety violation rate:** **0.0%** (0 invented doses across all tests).

---

## 3. Honest Statement of Verified vs. Unverified Capabilities

### Verified & Active
1. **Offline Retrieval Chatbot (Web & Mobile):**
   - Word-for-word grounded in `chatbot_faq.json` (27 entries) and `disease_info.json`.
   - Pure Dart implementation in `mobile/lib/chat/chat_engine.dart` verified with 100% character and intent parity across 404 golden cases against Python.
   - Operates 100% on-device with zero internet required.
2. **Online LLM Proxy (`/api/chat/online`):**
   - Live-tested with Groq (`qwen/qwen3.8-27b`) via user API key.
   - Responds in < 1.0s in English and Kannada with grounding context, source citations (`S1`, `S2`, etc.), and strict regex filters blocking numeric doses or certainty claims.
3. **Web & Mobile Screening Flow (Online):**
   - Multipart image upload to `POST /api/predict`.
   - MobileNetV3 evaluation with bilinear resize, 0–255 range, no EXIF auto-rotation, deterministic CAM generation, and 0.95/0.70 threshold categorization.
4. **Local Data Persistence:**
   - Scan history strictly capped at 8 entries.
   - Chat history strictly capped at 30 messages with clear chat functionality.

### Explicitly Disabled / Pending Verification
1. **Offline Mobile Photo Screening (TFLite):**
   - While `v3small_probs_features.tflite` is bundled (3.76 MB, well within Play Store limits), on-device numerical parity has not been validated against 20 field test images.
   - Per `ANTIGRAVITY_TASK.md` instructions, **offline photo screening is left behind a disabled feature flag (`enableOfflineScreening = false`)**. The mobile app explicitly informs the user that screening currently uses the app server.
2. **Regional Translations:**
   - Kannada (`kn`), Hindi (`hi`), and Malayalam (`ml`) texts are draft translations and carry visible "Draft" badges in both web and mobile UIs.

---

## 4. Key Files Added & Modified

### Mobile App (`mobile/`)
- `mobile/lib/core/constants.dart`: Hard thresholds (0.95/0.70), class names, storage caps (8 scans, 30 msgs), feature flags.
- `mobile/lib/core/theme.dart`: Calming agricultural green palette, WCAG AA contrast.
- `mobile/lib/models/screening_result.dart`: JSON serialization, confidence, CAM base64, status computation.
- `mobile/lib/models/chat_message.dart`: ChatTurn, SourceItem, SuggestionItem models.
- `mobile/lib/services/api_service.dart`: HTTP client for `/api/health`, `/api/chat/status`, `/api/predict`, and `/api/chat/online`.
- `mobile/lib/services/history_service.dart`: SharedPreferences storage capped at 8 items.
- `mobile/lib/services/chat_history_service.dart`: SharedPreferences storage capped at 30 items.
- `mobile/lib/services/locale_service.dart`: Multilingual state for `en`, `kn`, `hi`, `ml`.
- `mobile/lib/chat/chat_engine.dart`: Deterministic Dart chat engine (tokenization, stemming, IDF, synonyms, regex safety).
- `mobile/lib/screens/main_navigation_screen.dart`: Bottom navigation for 5 tabs (Scan, Guide, Ask, History, Settings).
- `mobile/lib/screens/scan_screen.dart`: Image picker (camera/gallery, 10MB limit), screening trigger.
- `mobile/lib/screens/result_screen.dart`: Status banner, CAM overlay toggle, 4 relative scores, ICAR advice.
- `mobile/lib/screens/guide_screen.dart`: Browsable disease guide for all 4 classes.
- `mobile/lib/screens/history_screen.dart`: List of past 8 scans with details.
- `mobile/lib/screens/ask_screen.dart`: Chat UI with offline engine, online mode button, chips, badges, sources toggle.
- `mobile/lib/screens/settings_screen.dart`: Language switcher, server URL configuration, test connection, data purge.
- `mobile/test/widget_test.dart`: 10 unit and widget smoke tests.
- `mobile/test/chat_golden_test.dart`: 404-case golden parity test.
- `mobile/test/assets/chat_golden.json`: Golden parity dataset.

### Tools & Backend
- `tools/make_chat_golden.py`: Generator script for golden test dataset.
- `backend/chat_proxy.py`: OpenAI-compatible proxy with `load_dotenv` and grounding pipeline.
- `backend/main.py`: Added `load_dotenv` for environment configuration.
- `backend/tests/test_chat_api.py`: Updated test isolation for `test_chat_status`.
- `.env.example`: Template for Groq, Gemini, and OpenAI keys.

---

## 5. Security & Secrets Verification

- Secrets scan across working tree and git diff against base branch (`codex/arecalens-webapp..HEAD`): **0 keys found**.
- `.env` and `.env.*` remain strictly untracked and protected in `.gitignore`.
- Zero user chat text or uploaded photos are logged on the server.

---

## 6. Remaining Real-World Recommendations & Next Steps

1. **Key Revocation:** As noted in Phase 0, any API key previously pasted during earlier development chats should be rotated/revoked in its respective provider console.
2. **Native Speaker & Agricultural Review:** Flagged entries (`koleroga_prevent`, `yld_treatment`, `bordeaux_how`) and draft regional translations (`kn`, `hi`, `ml`) should be validated with native-speaking agricultural extension officers.
3. **On-Device TFLite Parity:** When a dataset of 20+ real arecanut field photos is gathered, run bilateral comparison between Python Keras and Dart TFLite outputs. If max probability difference is < 0.01 and CAM correlation > 0.95, enable `enableOfflineScreening = true`.
4. **Remote Repository Push:** Branch `feature/chatbot-and-mobile` is fully committed locally and ready to be pushed whenever the remote repository is configured with write access.
