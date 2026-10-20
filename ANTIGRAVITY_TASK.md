<USER_REQUEST>
# ANTIGRAVITY TASK: finish the ArecaLens chatbot, add online mode, then build the Flutter app

Read this whole file before doing anything. Work through the phases in order. Commit after every phase. Keep a running log in `PROGRESS.md` (what was done, test output, open problems). At the end, write `FINAL_REPORT.md`.

---------------------------------------------------------------------------------------------------

## 0. Who I am and what I need

I am a final-year engineering student. ArecaLens is my project. I have about 2 days. The web app works. The chatbot does not work and nothing is finished for mobile. I need:

1. An offline, knowledge-grounded chatbot ("Ask") working in the web app. (MANDATORY)
2. An optional online "Ask more" mode using an LLM through a backend proxy. (SECOND PRIORITY)
3. A Flutter mobile app that works online and offline as far as honestly possible. (THIRD PRIORITY)
4. A cleaner, more attractive UI. (Only after 1 to 3 work. Small, safe CSS improvements only.)

If time runs short, finish in this order and stop cleanly. A finished phase 1 to 4 beats a half-finished everything.

## 1. The project (facts, do not change these)

- ArecaLens screens photos of arecanut leaves and nuts. It is a screening aid, not a diagnosis tool.
- Model: MobileNetV3Small, 4 classes in this exact order: `Healthy_Leaf`, `Healthy_Nut`, `Mahali_Koleroga`, `Yellow_Leaf`.
- Thresholds: 0.95 for a healthy result, 0.70 for a suspected disease result, below that "unsure". DO NOT CHANGE.
- Preprocessing: decode as RGB, resize to 224x224 with bilinear resize (TensorFlow `tf.image.resize`), raw float32 values 0 to 255 (the backbone contains normalisation), image is stretched, not cropped, no EXIF auto-rotation. DO NOT CHANGE.
- Explanation: deterministic CAM = ReLU(features @ effective_weights), max-normalised, bicubic resized, overlaid. It is not Grad-CAM.
- Scores are relative scores, not probabilities of a correct diagnosis.
- UI languages: en, kn, hi, ml. Kannada, Hindi and Malayalam text are drafts pending native-speaker and agricultural review.
- Frontend: React 19, Vite 6, JavaScript, Lucide icons, Vitest. Backend: Python 3.13, FastAPI, Uvicorn, TensorFlow 2.21, Keras, Pillow, pytest.
- Repo: https://github.com/Aditi-Adiga/Arecanut-Disease-Detection-XAI , branch `codex/arecalens-webapp`.
- Local folder on my laptop: `D:\dev\arecanut_web`. Project Python: `D:\dev\arecanut_web\backend\.venv\Scripts\python.exe`. Do not use `D:\dev\backend\.venv`.
- Existing endpoints: `GET /api/health`, `GET /api/ready`, `GET /api/diseases?language=`, `POST /api/predict?language=`, `/docs`. The backend also serves the built React app on port 8000.
- Repo files (from the README): `backend/models/mobilenetv3small.keras`, `backend/models/v3small_probs_features.tflite` (probabilities + features export, used for parity checks), `backend/data/cam_weights.json`, `backend/data/disease_info.json` (v0.3-draft), `Dockerfile`, `render.yaml`, `pytest.ini`, `start.cmd`, `start.ps1`, `DEMO_CHECKLIST.md`, `colab_reference_export.py`.
- Hosting is planned on a free Render service. Memory limits there are unverified. Do not select a paid plan.

## 2. Input files (I will place them in `chatbot_inputs/` in the workspace)

- `chat_engine.py`: reference offline engine, standard library only. Class `ChatEngine(faq, info=None, min_score=0.5)`, method `answer(message, language="en", context=None)`.
- `chatbot_faq.json`: version 0.1-draft, 27 entries, 7 chips, 5 safety messages, 9 sources (S1 to S9) keyed by id with title, publisher, year, url, used_for. Entry flags: `needs_expert_review` (koleroga_prevent, yld_treatment, bordeaux_how), `deployment_dependent` (privacy, offline). All `i18n` and `questions_i18n` for kn, hi, ml are empty.
- `disease_info.json`: v0.3-draft. Keys: classes, uncertain_result, bordeaux_mixture_recipe, sources, placeholders, explanation, i18n_status. It is also at `backend/data/disease_info.json` in the repo.
- `chat_eval.csv`: 64 development questions (columns: question, context_class, expected).
- `test_chat_engine.py`: tests against the dev set.
- `chatbot_build_prompt.md`: my earlier spec for the web chatbot. Treat this file as a requirement source. Where this file and that one disagree, this file wins.

Verified before you start: with all of the above together, the engine scores 64/64 on the dev set and the 4 other tests pass. On 20 quick unseen questions it had three real misses, listed in Phase 3.

## 3. Hard rules (never break these)

1. All chatbot answers in OFFLINE mode come only from `chatbot_faq.json` and `disease_info.json`, copied word for word. No generated advice offline.
2. Never give spray doses, mixing amounts, or chemical product advice beyond what those two files contain. Refuse politely and refer to an agricultural officer or Krishi Vigyan Kendra (KVK).
3. Never say a disease is "confirmed". Use "suspected" or "consistent with".
4. Entries with `needs_expert_review: true` show a small badge: "please confirm with your agricultural officer". Entries with `deployment_dependent: true` must match the real deployment (see Phase 3).
5. Questions about people's health get the safety message (medical help) and nothing else.
6. Never store or log chat text on the server. No `print`, logger call or access-log line may contain message text. Chat history lives only in the browser or app, maximum 30 messages, with a "Clear chat" button.
7. Never put API keys in frontend code, Flutter code, committed files, logs or screenshots. Keys live only in backend environment variables.
8. Do not change the model, thresholds, preprocessing, CAM logic or any existing test. All existing backend and frontend tests must still pass after every phase.
9. The unverified Bordeaux recipe (`bordeaux_mixture_recipe`) must never be displayed or spoken by the bot. The FAQ entry `bordeaux_how` already defers to the agricultural officer or KVK. Keep that behaviour.
10. Do not claim field accuracy, parity or verification that you have not actually measured. Report only what you ran.
11. Work on a new branch `feature/chatbot-and-mobile`. Never force-push. Never push to `main` or to `codex/arecalens-webapp` directly. Do not push at all unless the remote is writable; if it is not, tell me and leave everything committed locally.

## 4. Phase 0: inspect, back up, secure (do this first)

1. Run `git status`, `git remote -v`, `git branch -a`, `git log --oneline -10`. Report them in `PROGRESS.md`.
2. My VS Code folder holds an OLD chatbot that is not pushed and does not work properly: `backend/chat.py`, `frontend/src/components/ChatAssistant.jsx`, `frontend/src/locales/extraMessages.js`, and chat tests. Do NOT delete any of it. First create a backup branch `backup/old-chatbot` and commit everything as it stands, including uncommitted files.
3. Secrets scan: search the whole working tree and git history for API keys or tokens (`AIza`, `sk-`, `CHATBOT_API_KEY=`, `.env`). If anything is found, remove it from the working tree, add the file pattern to `.gitignore`, and tell me loudly in `PROGRESS.md`. A key was pasted into a chat earlier and must be revoked by me in Google AI Studio; remind me in `FINAL_REPORT.md`.
4. Make sure `.gitignore` contains `.env`, `.env.*`, `backend/.venv`, `node_modules`, `*.log`, and Flutter build folders (`mobile/build`, `.dart_tool`).
5. Create the branch `feature/chatbot-and-mobile` from the current working state, excluding the old chatbot files from the final design (see Phase 1 step 1).
6. Run the existing tests first and record the baseline: `.\backend\.venv\Scripts\python.exe -m pytest -q` and `npm.cmd --prefix frontend test`. Record counts. If the baseline fails, fix nothing unrelated; note it.

## 5. Phase 1: backend offline chat (MANDATORY)

1. The old `chat.py` is replaced. Keep the old file out of the active code path (move it to `docs/old_chatbot/` or remove it from the branch since the backup branch has it). The old matcher returned unrelated text and repeated answers; do not reuse its matching logic.
2. Copy `chat_engine.py` to `backend/chat_engine.py`. Keep it standard library only. You may make small safe fixes (see Phase 3) but keep the answer-order of safety checks intact.
3. Copy `chatbot_faq.json` to `backend/data/chatbot_faq.json`, next to `disease_info.json`.
4. Create `backend/chat_api.py` with a FastAPI `APIRouter` and register it in `backend/main.py`:
   - Load FAQ and `disease_info.json` once at startup. Validate: every id in `chips` exists in `entries`; every source id used by any entry exists in `sources`. On failure, raise a clear error at startup that names the bad id.
   - `GET /api/chat/chips?language=en` returns `{"chips": [{"id": "...", "question": "..."}]}`.
   - `GET /api/chat/status` returns `{"online_enabled": bool}` (false until Phase 6).
   - `POST /api/chat`:

     Request (Pydantic):
     ```json
     {"message": "string, 1 to 300 characters, stripped",
      "language": "en | kn | hi | ml",
      "context": {"class": "Healthy_Leaf | Healthy_Nut | Mahali_Koleroga | Yellow_Leaf (optional)",
                  "status": "optional string", "confidence": "optional float 0..1"}}
     ```
     IMPORTANT: `class` is a Python keyword. Define the field as `cls: Optional[ClassName] = Field(None, alias="class")` with `populate_by_name=True`, and pass `{"class": value}` to the engine.

     Response:
     ```json
     {"answer": "string", "intent": "string", "entry_id": "string or null",
      "sources": [{"id": "S1", "title": "...", "publisher": "...", "year": "...", "url": "..."}],
      "refused": false, "needs_expert_review": false, "language_fallback": false,
      "suggestions": [{"id": "...", "question": "..."}],
      "ai_generated": false, "answer_source": "guide"}
     ```
     The engine returns source ids only. Expand them to full objects from `faq["sources"]`.
   - Validation errors return 422 (bad language, empty message after stripping, more than 300 characters, unknown class).
   - Per-IP rate limit only if the repo already has rate-limit code. If not, add a small in-memory limiter (for example 30 requests per minute per IP) that returns 429 and logs no message text.
   - The chat endpoints must never receive or accept a photo.
5. Logging check: grep the backend for any logging of request bodies and confirm uvicorn's access log does not include bodies (it does not log POST bodies by default, but verify any custom middleware).
6. Tests (pytest) in the existing backend test folder:
   - Port `test_chat_engine.py` (dev set accuracy at least 90%, doses refused, every answer comes from the files, regional fallback flag, unverified items flagged).
   - API tests: valid question, empty message, 301-character message, bad language, unknown class, dose refusal, health refusal, price/out-of-scope refusal, "confirm for sure" refusal, "what should I do now" with each of the 4 classes returns `intent == "current_result_advice"`, response shape, sources expanded to objects, no body text in logs (use `caplog`).
7. Run all backend tests including the existing ones. Commit: `feat(chat): offline chat engine and API`.

## 6. Phase 2: web frontend "Ask" tab (MANDATORY)

Inspect `frontend/src/App.jsx`, the components folder and the locales files first. Match the existing style, structure and test setup.

1. Add an Ask tab or panel (follow how the app does navigation; the old design used a floating panel, a tab is preferred).
2. Contents:
   - A chip "About your last result: <class display name>" when a scan result exists. The class comes from the app's current result state; never send photos.
   - Message list (user and bot messages), starter question chips (from `GET /api/chat/chips`), an input with a 300-character limit and a live counter, a Send button disabled when empty.
   - Each bot message shows: the answer with line breaks preserved; a "Sources" toggle listing titles as links (open in new tab with `rel="noopener noreferrer"`); the expert-review badge when `needs_expert_review`; a notice when `language_fallback` is true ("Shown in English because the translation is not ready yet"); a label "From the verified guide"; follow-up suggestion chips; a small "this is a screening aid, not a diagnosis" line in the panel footer.
   - Error state: "Could not reach the app server. Try again." with a Retry button.
   - Clear chat button. History kept in React state plus `sessionStorage` or `localStorage` (maximum 30 messages). Drop the oldest beyond 30.
3. Add i18n strings for all new UI text in en, kn, hi, ml. Mark kn, hi, ml as drafts in the same way the project already marks them.
4. Accessibility: text at least 16px, touch targets at least 44px, `aria-live="polite"` on the message list, labels on the input and buttons, Enter sends, Shift+Enter is not needed, layout works at 360px width, visible focus outlines.
5. Chips-first design. Typed matching works for English only; if a user types in Kannada, Hindi or Malayalam and the engine falls back, show the fallback message together with the starter chips.
6. Tests (Vitest and Testing Library): renders chips, send disabled when empty, 300-char limit, shows answer and sources toggle, shows expert badge, shows language-fallback notice, shows error state on failed fetch, clear chat empties messages, caps at 30 messages, result chip appears only when a result exists. Mock `fetch`.
7. Run the frontend tests and the production build. Check the browser console for errors using a real browser run (use the Antigravity browser tool if available): open the app, run a scan with a sample image if one exists, open Ask, ask three questions, capture screenshots at 360px and desktop width. Commit: `feat(chat): Ask tab`.

## 7. Phase 3: content fixes (MANDATORY, in `chatbot_faq.json`)

Edit only wording and keywords. Do not invent agricultural facts; reuse text from `disease_info.json` or the README facts below.

1. Retrieval misses found on unseen questions:
   - "do you save my photo" returns `photo_tips`, it must return `privacy`. Add keywords and question variants for save, store, keep, delete, privacy, data, upload, photo saved.
   - "which language does the app support" falls to the fallback, it must return `languages`.
   - "my areca leaves are turning yellow what is wrong" falls just under the threshold (score 0.485 vs 0.5), it must return `what_is_yld`. Add paraphrase questions and keywords (leaves yellow, yellowing, turning yellow).
   - After any edit, rerun the dev set. It must stay at or above 90% (currently 64 of 64).
2. `deployment_dependent` entries must match the real deployment:
   - `offline`: The app runs on a laptop without internet after it is installed and while the local server is running. A phone using an online deployment needs internet for photo screening. (After Phase 7, update this entry to describe what the mobile app can do offline, using only what you have verified.)
   - `privacy`: Scan history is stored in the browser on the device (up to 8 resized scans). Raw uploads are not saved to the backend filesystem. The chat does not send your photo. Chat text is not stored on the server. Hosting operators control their own server logs.
3. Keep `needs_expert_review` badges on the three flagged entries.
4. Regional translations: fill `questions_i18n` and `i18n` for kn, hi, ml for the 7 chip entries first, then as many others as time allows. Mark each as draft. Use only content that already exists in `disease_info.json`'s regional guide text if present; otherwise write careful plain-language translations and flag them for native-speaker review in `FINAL_REPORT.md`. Do not translate doses (there are none to translate). `i18n_status` stays "draft".
5. Write 20 NEW test questions of your own, not in `chat_eval.csv`, covering: 8 in-scope questions phrased differently from the dev set, 4 safety questions (dose, chemical, health, confirm), 4 out-of-scope (price, weather, other crops, joke), 4 follow-ups with a class context. Save them as `backend/tests/chat_unseen.csv` with expected outcomes. Run them. Report honestly: accuracy, which failed, why. Acceptance: at least 70% correct or a safe fallback, and zero answers containing a dose that is not in the data files.
6. Commit: `content(chat): faq fixes, deployment entries, translations (draft)`.

## 8. Phase 4: README, docs, evaluation write-up

1. README: document the feature, the data file, the endpoints (request and response above), how to add an FAQ answer (id, topic, questions, keywords, answer, sources, classes, flags, i18n), how to run tests, the safety rules, and the limits (retrieval assistant, English typed matching only, draft regional text, expert review pending).
2. Call it a knowledge-grounded retrieval assistant, not a generative one. Say the dev set was written alongside the engine, so its accuracy is optimistic, and report the unseen-set result separately.
3. Update `DEMO_CHECKLIST.md` with the chatbot demo steps.
4. Make sure the `Dockerfile` copies `backend/chat_engine.py`, `backend/chat_api.py` and `backend/data/chatbot_faq.json` (check the existing COPY lines; do not rebuild the image unless Docker is available).
5. Commit: `docs: chatbot README and demo checklist`.

## 9. Phase 5: UI polish (small, safe)

Only after Phase 1 to 4 pass. CSS and layout only: consistent spacing, readable contrast (WCAG AA), larger touch targets, a calmer colour palette that fits farmers and green agriculture, clearer result cards, readable heatmap controls. No behaviour changes, no new dependencies, no layout shifts that break existing Vitest tests. Show before/after screenshots. Commit: `style: ui polish`.

## 10. Phase 6: optional online "Ask more" (SECOND PRIORITY)

Disabled by default: `ENABLE_LLM_CHAT=false`.

Backend (environment variables only, read at request time, never logged):
- `ENABLE_LLM_CHAT` (default false), `CHATBOT_API_KEY`, `CHATBOT_API_URL`, `CHATBOT_MODEL`.
- Provider: an OpenAI-compatible chat-completions endpoint. For Gemini use its OpenAI-compatible endpoint. Check the current Google documentation for the exact base URL and for a currently available model ID before hardcoding anything; do not guess a model name. The model ID must stay configurable.
- `GET /api/chat/status` returns `{"online_enabled": true}` only when the flag is true AND key, URL and model are all set. A true status does not prove the provider will accept the call; say that in the README.
- `POST /api/chat/online` takes the same request as `/api/chat`:
  1. Run the SAME safety filters first (health, dose, chemical, out-of-scope, confirm). If one fires, return the safety message from the offline engine and do not call the provider.
  2. Retrieve the top 3 FAQ entries (add a `top_k(message, k=3)` method to the engine that reuses its scoring) plus the current class advice from `disease_info.json` if a class is given.
  3. Send to the provider with temperature 0 to 0.2, max 300 tokens, the user message, up to 6 recent turns if the client supplies them (client sends turns; server does not store them), and the retrieved text as CONTEXT. Never send photos or scan history.
  4. System prompt, exactly:

     "You are the assistant inside ArecaLens, an arecanut leaf and nut health app. Answer ONLY from the CONTEXT below. If the context does not contain the answer, say you do not know and suggest asking an agricultural officer or KVK. Never give spray doses, mixing amounts or product names. Never say a disease is confirmed; say suspected or consistent with. Keep answers under 120 words, in simple language, in {language}. If asked about people's health, prices, weather or other crops, politely decline."
  5. Post-check the model reply: if it contains a number followed by ml, g, kg, litre, ppm, or `%` that does not appear in the retrieved context, or the words "confirmed", "definitely", "100%", discard it and return the offline answer.
  6. Response: same shape as `/api/chat` plus `"ai_generated": true`, `"answer_source": "ai"`. On ANY failure (not configured, timeout of 15 s, 401/403, 404 model, 429, 5xx, network), return HTTP 200 with the offline answer, `"ai_generated": false`, `"answer_source": "guide"`, and `"online_error": "not_configured | timeout | auth | model_not_found | rate_limited | provider_error | network"`.
  7. Never log message text, keys, provider response bodies or headers.
- Tests with a mocked provider: success, each failure code falls back, safety filter blocks the provider call (assert the mock was not called), post-check discards an invented dose, status false when any variable is missing, no key in any response.
- I have NOT confirmed a live provider response. If I give you a key in the environment, run one live test and report the real result; otherwise state clearly in the report that online mode is tested with mocks only.

Frontend:
- "Ask more (online)" button under a bot answer, visible only when `status.online_enabled` is true and `navigator.onLine` is true; greyed out with a short reason otherwise.
- Before the first online send, show a notice: what is sent (your question, the class of your last result, up to 3 guide entries) and what is not (photo, scan history). Remember the acknowledgement for the session.
- Every online answer carries the label "AI-generated, may be wrong. Confirm with your agricultural officer or KVK." Offline answers keep "From the verified guide".
- Loading indicator, 15 s timeout, and when `online_error` is present show "Online answer unavailable, showing the guide answer" with a wording variant for rate limit and not configured.
- Vitest tests for each of these states. Commit: `feat(chat): optional online mode`.

## 11. Phase 7: Flutter mobile app (THIRD PRIORITY)

Create the app in `mobile/` (Flutter stable, Dart null safety, Android first; iOS builds only if the toolchain is present). Use the web app's flows and wording as the reference. Keep dependencies few: `http` or `dio`, `provider` or `riverpod` (pick one), `image_picker`, `image`, `tflite_flutter`, `connectivity_plus`, `shared_preferences`, `url_launcher`, `flutter_localizations` plus `intl`. Check each package's current version and Android compatibility before adding it.

### 11.1 Screens and behaviour
- Welcome, language selection (en, kn, hi, ml with the draft marking), Screen (camera or gallery, validate JPEG/PNG/WebP, 10 MB, 24 MP), Result (suggested class, four relative scores, status healthy/suspected/unsure using 0.95 and 0.70, explanation text, heatmap with original/heatmap compare and opacity slider, save or share result), Guide (disease info), History (up to 8 results, local only), Ask (chat), Settings (language, server URL, clear data).
- Same wording rules: "suspected" never "confirmed", scores are relative, not probabilities, screening aid, expert confirmation.
- Responsive for small phones, font scaling respected, text at least 16 sp, 48 dp touch targets, semantic labels for screen readers.

### 11.2 Online mode
- Photo screening online: `POST {baseUrl}/api/predict?language=` multipart `file`, using the existing backend. Base URL configurable in Settings and in a build-time constant; HTTPS for production, `http://10.0.2.2:8000` for the Android emulator in debug only. Handle timeouts (60 s, because model cold start can be slow) and `/api/ready` before predict.
- Chat online: `POST /api/chat` (and `/api/chat/online` when `status.online_enabled`). No API key in the app, ever.
- Check CORS and cleartext rules: Android debug may need `usesCleartextTraffic` only for the debug manifest; release uses HTTPS only.

### 11.3 Offline mode (build in this order, stop at the first one that cannot be verified)
1. Offline guide and offline chat (MANDATORY inside this phase). Bundle `chatbot_faq.json` and `disease_info.json` as assets. Port `chat_engine.py` to Dart (`mobile/lib/chat/chat_engine.dart`) keeping the same tokenizer, stop words, synonym table, stemmer, regex safety checks, scoring formula and thresholds, and the same answer order. Do not "improve" it.
   - PARITY TEST (required): write a small Python script `tools/make_chat_golden.py` that runs the Python engine on every question in `chat_eval.csv` plus the unseen question file plus 20 extra safety and out-of-scope questions, in each of the four languages, and writes `mobile/test/assets/chat_golden.json` with intent, entry_id and the answer text. Write a Dart test that loads the same FAQ and runs the Dart engine on each question and asserts identical intent, entry_id and answer. All must match. Regex differences between Python `re` and Dart `RegExp` (word boundaries, Unicode `\w`, case-insensitivity, `\b` behaviour with non-Latin text) are the likely failure point; fix them until the golden test is fully green.
2. Offline photo screening with TFLite (only if verified).
   - The repo has `backend/models/v3small_probs_features.tflite`, which outputs probabilities and features. Use it with `cam_weights.json` to compute CAM on device: CAM = ReLU(features @ effective_weights for the predicted class), max-normalised, resized to the image size with bicubic interpolation, colourised and overlaid.
   - Preprocessing in Dart must reproduce the backend: decode RGB, resize to 224x224 with bilinear interpolation matching `tf.image.resize(..., method="bilinear")` (TF2 uses half-pixel centres and no antialiasing), raw float32 0 to 255, stretched, no EXIF rotation. The `image` package's resize can differ from TensorFlow's. Implement your own bilinear resize with half-pixel centres if needed.
   - PARITY TEST (required): take at least 20 images from the repo's test folders, or from `reference_bundle` if I provide it, run them through the Python backend and through the Dart/TFLite path (a device or emulator integration test, or `flutter test` with a desktop TFLite runtime if available). Compare class probabilities (max absolute difference should be below 0.01 and the predicted class must match on every image) and CAM (correlation above 0.95). Report the real numbers.
   - If parity fails and cannot be fixed within the time limit, DO NOT ship offline screening as working. Keep photo screening online-only in the app, state this limitation in the Settings screen and in `FINAL_REPORT.md`, and leave the TFLite code behind a feature flag set to off.
3. Connectivity behaviour: the app checks connectivity; screening uses the device model when verified and the user chose offline or has no connection, otherwise the server; chat uses the offline Dart engine always and offers "Ask more (online)" only when the backend status says online chat is enabled and the device is online.
4. Model size: check that the tflite asset fits Play Store limits and note the size.

### 11.4 Mobile tests and checks
- Dart unit tests: chat engine golden test, threshold/status logic (0.95/0.70/unsure), history cap at 8 and chat cap at 30, language fallback flags.
- Widget tests: Ask screen states (empty, answer with sources, badge, language notice, error, clear chat), Result screen unsure state wording, language switch.
- `flutter analyze` must be clean. `flutter test` must pass. Build a debug APK (`flutter build apk --debug`) and, if an emulator is available, run it and capture screenshots.
- Update the `offline` FAQ entry (web and mobile copies) to describe only what you verified.
- Commit: `feat(mobile): flutter app`.

## 12. Phase 8: final verification and report

1. Run everything again: backend `pytest`, frontend `vitest`, frontend build, `flutter analyze`, `flutter test`. Record counts.
2. Re-run the secrets scan. Confirm no key is in the tree or in the diff of this branch.
3. Write `FINAL_REPORT.md` with:
   - List of changed and added files.
   - Test results (counts and commands), dev set accuracy, unseen set accuracy with the failing questions.
   - Honest statement of what is verified and what is not (online mode live-tested or mock-only; offline TFLite parity numbers or "not verified, offline screening disabled"; regional text still draft).
   - Screenshots taken and where they are saved.
   - Remaining TODOs: revoke the old leaked key, native-speaker review of kn/hi/ml, agricultural-expert review of flagged entries, expert review of the disease guide, real-farm validation, push permission on the remote, Render memory check, Play Store signing and listing if wanted.
   - The sentence for my report: "ArecaLens includes a knowledge-grounded retrieval assistant (not a generative one) that answers from cited, expert-review-pending sources."
4. Push the branch if the remote is writable; otherwise say so.

## 13. Working rules for you (the agent)

- Plan first, then execute. Show the plan, files you will add or change, and any assumption. Ask me only if you are truly blocked (missing file, missing permission, a destructive action). For everything else choose the safer option and note it.
- Make small commits. Run tests after every phase and fix failures before moving on. Do not skip a failing test; do not edit existing tests to make them pass.
- Do not add dependencies without a reason noted in `PROGRESS.md`. No telemetry, analytics or third-party trackers.
- Do not touch model files, thresholds, CAM code or preprocessing.
- If a phase cannot be completed, write what blocked it, leave the code in a working state behind a flag, and continue with the next phase.
- Use plain, direct wording in all UI text and docs. Keep farmer-facing sentences short.

## 14. Acceptance checklist

- [ ] Old chatbot backed up on `backup/old-chatbot`; no key in tree or history of this branch.
- [ ] Dev set at least 90%; unseen set at least 70% correct or safe fallback; zero invented doses.
- [ ] All safety tests pass (dose, chemical, health, confirm, out-of-scope, Bordeaux recipe not shown).
- [ ] `/api/chat`, `/api/chat/chips`, `/api/chat/status` work; 422 on bad input; no message text in logs.
- [ ] Ask tab works at 360px and desktop; no console errors; accessibility items done.
- [ ] Existing backend and frontend tests still pass; new tests added.
- [ ] README, DEMO_CHECKLIST and FINAL_REPORT written; screenshots saved.
- [ ] Online mode behind a flag with mock tests and clean fallback; live-test status stated truthfully.
- [ ] Flutter app builds, `flutter analyze` clean, tests pass, Dart chat engine matches the Python golden file exactly.
- [ ] Offline photo screening either parity-verified with numbers or disabled and described honestly.
</USER_REQUEST>
<ADDITIONAL_METADATA>
The current local time is: 2026-10-20T16:22:49+05:30.

The user's current state is as follows:
Active Document: c:\Users\Aditya\Downloads\ANTIGRAVITY_TASK.md (LANGUAGE_MARKDOWN)
Cursor is on line: 32
Other open documents:
- c:\Users\Aditya\Downloads\ANTIGRAVITY_TASK.md (LANGUAGE_MARKDOWN)
</ADDITIONAL_METADATA>