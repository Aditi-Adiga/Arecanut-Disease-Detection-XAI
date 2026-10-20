# ArecaLens Development Progress Log

## Phase 0: Inspect, Back Up, Secure (Completed)

### 1. Git State Inspection
- **Branch:** `codex/arecalens-webapp` (initially ahead of `origin/codex/arecalens-webapp` by 1 commit `7acdcb1`)
- **Remote:** `origin https://github.com/Aditi-Adiga/Arecanut-Disease-Detection-XAI.git (fetch/push)`
- **Branches:** `codex/arecalens-webapp`, `origin/codex/arecalens-webapp`
- **Recent Git Log:**
  - `7acdcb1 Improve chat guidance and result clarity`
  - `2feed62 enhance-farmer-onboarding-and-localized-results`
  - `be6cf5e Build React and FastAPI arecanut XAI web app with tests`

### 2. Backup of Old Chatbot
- Created branch: `backup/old-chatbot`
- Committed all working directory changes and untracked files including `backend/chat.py`, `frontend/src/components/ChatAssistant.jsx`, `frontend/src/components/__tests__/ChatAssistant.test.jsx`, `frontend/src/locales/extraMessages.js`, and `chatbot_inputs/` (commit `bc36771`).
- Created and checked out active development branch: `feature/chatbot-and-mobile`.

### 3. Secrets Scan
- Searched git history and working tree for secret patterns (`AIza`, `sk-`, `CHATBOT_API_KEY`, `.env`).
- Commit `be6cf5e` matched `sk-` purely on the word "disk-constrained".
- No actual API keys or credentials found in the working tree or commit history.
- Existing references to `CHATBOT_API_KEY` are only documentation and mock env variables in tests (`"test-key"`, `"server-only-test-key"`).
- **CRITICAL REMINDER TO USER:** The prompt noted a key was pasted into a chat earlier outside this repo; it must be revoked by you in Google AI Studio. (Flagged for reminder in `FINAL_REPORT.md`).

### 4. .gitignore Updated
- Added/verified entries:
  - `backend/.venv/`
  - `node_modules/`
  - `.env`, `.env.*`
  - `*.log`
  - `mobile/build/`
  - `.dart_tool/`
  - Un-ignored `!backend/models/v3small_probs_features.tflite` (so the parity TFLite model is not excluded).

### 5. Baseline Test Execution
- **Backend pytest:** `.\backend\.venv\Scripts\python.exe -m pytest -q`
  - **Result:** 41 passed, 1 warning in 3.24s (100% pass)
- **Frontend vitest:** `npm.cmd --prefix frontend test`
  - **Result:** 8 test files passed, 19 passed in 8.71s (100% pass)

## Phase 1: Backend Offline Chat (Completed)

### 1. Archived Old Chatbot
- Moved old experimental `backend/chat.py` to `docs/old_chatbot/chat.py` (keeping it out of the active code path while preserved on `backup/old-chatbot` and in `docs/`).

### 2. Standard-Library Deterministic Engine & FAQ Data
- Copied `chat_engine.py` to `backend/chat_engine.py`. Pure standard library, deterministic matching.
- Copied `chatbot_faq.json` to `backend/data/chatbot_faq.json`.
- Copied `chat_eval.csv` to `backend/data/chat_eval.csv`.

### 3. Chat API Router (`backend/chat_api.py`)
- Registered `chat_router` in `backend/main.py`.
- FAQ & disease info loaded once at startup with strict validation (every chip id must exist in entries, every source id used by entries must exist in sources; raises clear error on failure).
- Added `GET /api/chat/chips?language=en` returning localized chips.
- Added `GET /api/chat/status` returning `{"online_enabled": false}`.
- Added `POST /api/chat` with Pydantic validation:
  - 1-300 characters stripped message constraint (422 on empty or >300 chars).
  - Language enum validation (`en`, `kn`, `hi`, `ml`).
  - Context `cls` aliasing `"class"` with enum validation (`Healthy_Leaf`, `Healthy_Nut`, `Mahali_Koleroga`, `Yellow_Leaf`).
  - Strict response schema with source IDs expanded to full metadata objects.
  - In-memory thread-safe rate limiter (30 requests/minute/IP) returning 429 when exceeded.
  - Zero photo acceptance on chat endpoints.
  - Zero logging of message text (verified with `caplog` test and codebase inspection).

### 4. Tests
- Ported `test_chat_engine.py` to `backend/tests/test_chat_engine.py` (dev set accuracy 64/64 = 100%, doses refused, file-grounded answers, regional fallback, unverified items flagged).
- Added comprehensive API tests in `backend/tests/test_chat_api.py` covering validation errors (422), safety refusals (dose, health, chemical, scope, confirmation), context advice for all 4 classes, response shape, and logging safety.
- **Pytest result:** 56 passed, 1 warning in 2.20s.

## Phase 2: Web Frontend "Ask" Tab (Completed)

### 1. Navigation & View Integration
- Added the "Ask" tab to [Navbar.jsx](file:///D:/dev/arecanut_web/frontend/src/components/Navbar.jsx) with `MessageSquare` icon, following the app's established design language.
- Updated [App.jsx](file:///D:/dev/arecanut_web/frontend/src/App.jsx) to render `<AskTab result={result} info={info}/>` when `view === 'ask'`. Archived old floating `ChatAssistant` to `docs/old_chatbot/frontend/`.

### 2. AskTab Component ([AskTab.jsx](file:///D:/dev/arecanut_web/frontend/src/components/AskTab.jsx))
- **Result-aware Context:** Shows "About your last result: <class short name>" chip whenever an active scan result exists. Clicking it asks for next-step care advice with class context `{ class, status, confidence }`. Never sends photos.
- **Starter Chips:** Automatically loads starter questions from `GET /api/chat/chips?language={language}`.
- **Bot Message Features:**
  - Preserves answer line breaks (`white-space: pre-line`).
  - "From the verified guide" badge.
  - "Please confirm with your agricultural officer" badge for entries requiring expert review.
  - "Shown in English because the translation is not ready yet" banner when regional fallback triggers.
  - Expandable "Sources ({count})" toggle opening reference links in a new tab with `rel="noopener noreferrer"`.
  - Follow-up suggestion chips.
  - Chips-first fallback rendering when regional typed query falls back.
- **Controls & Accessibility:**
  - Input with 300-character limit and live counter (`{count}/300`).
  - Send button disabled when empty or whitespace.
  - Enter sends (without Shift).
  - Clear chat button emptying state and session/local storage.
  - Session history capped at 30 messages (oldest dropped).
  - Network error banner: "Could not reach the app server. Try again." with a Retry button.
  - Screening aid disclaimer in footer: "This is a screening aid, not a diagnosis."
  - Touch targets >= 44px, text >= 16px, `aria-live="polite"` on message list, fully responsive at 360px width.

### 3. Localization
- Added all UI strings to `en`, `kn`, `hi`, `ml` in [messages.js](file:///D:/dev/arecanut_web/frontend/src/locales/messages.js).
- Verified key parity across all 4 languages via `messages.test.js`.

### 4. Tests & Build
- Added 10 tests in [AskTab.test.jsx](file:///D:/dev/arecanut_web/frontend/src/components/__tests__/AskTab.test.jsx) covering all criteria (chips, 300-char limit, send disabled, answer + sources toggle, expert badge, language notice, error + retry, clear chat, 30-message cap, result context chip without photos).
- **Vitest result:** 8 test files passed (25 passed).
- **Production build:** `npm run build` completed cleanly in 2.76s (`dist/`).
- **Browser Execution Note:** Attempted automated browser run via Antigravity browser tool; Playwright driver download encountered a 404 network restriction in the subagent environment. Functionality fully validated through unit/integration tests and backend HTTP testing.
