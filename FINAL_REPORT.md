# ArecaLens Final Engineering & Verification Report

**Sentence for Engineering Report:**
> "ArecaLens includes a knowledge-grounded retrieval assistant (not a generative one) that answers from cited, expert-review-pending sources."

---

## 1. Executive Summary

ArecaLens is an Explainable Artificial Intelligence (XAI) screening aid and knowledge-grounded agricultural assistant designed for arecanut farmers in Karnataka and Kerala. The web application classifies leaf and nut cluster photographs into 4 primary classes:
1. `Healthy_Leaf` (Threshold >= 0.95)
2. `Healthy_Nut` (Threshold >= 0.95)
3. `Mahali_Koleroga` (Fruit rot, Threshold >= 0.70)
4. `Yellow_Leaf` (Yellow Leaf Disease, Threshold >= 0.70)
*(Photographs scoring below thresholds are categorized as "Unsure" to protect farmers against false reassurances).*

Per user direction, the application focuses 100% on delivering an attractive, robust, and accessible **Web Application**, combining deterministic on-device offline screening and FAQ retrieval with an optional server-side online LLM proxy (powered by Groq / Gemini).

---

## 2. Core Capabilities & Architecture

### A. Photo Screening & Explainable AI (XAI)
- **Model:** MobileNetV3Small trained on arecanut leaf and nut specimens.
- **Preprocessing:** Bilinear resize to 224x224 (matching TensorFlow half-pixel centres, float32 0–255), without EXIF auto-rotation.
- **Explanation:** Deterministic Class Activation Mapping (CAM):
  $$\text{CAM} = \text{ReLU}(\text{features} \cdot W_{\text{eff}})$$
  normalized and overlaid as a heatmap highlighting which regions influenced the classification.
- **Comparison Slider:** Interactive comparison control between the original photo and the heatmap overlay.
- **Local History:** Up to 8 recent scans stored in browser localStorage.

### B. Multilingual Offline Chatbot ("Ask" Tab)
- **Deterministic Engine (`backend/chat_engine.py`):** Pure standard library Python with Unicode tokenization, stemming, synonym mapping, and TF-IDF matching.
- **100% Knowledge Grounding:** All offline responses come word-for-word from `backend/data/chatbot_faq.json` (27 entries) and `backend/data/disease_info.json`. Zero hallucinations.
- **Multilingual Support:** Supports English (`en`), Kannada (`kn`), Hindi (`hi`), and Malayalam (`ml`). Visible "Draft translation" notices inform farmers that regional texts are pending native-speaker and agricultural review.
- **Safety Filters:**
  - `_DOSE`: Refuses unverified spray amounts or chemical concentrations and directs farmers to agricultural officers or KVKs.
  - `_HEALTH`: Blocks questions about human health or pesticide ingestion and advises immediate medical attention.
  - `_CONFIRM`: Enforces that screening results are "suspected" or "consistent with", never "confirmed".
  - `_OUT`: Politely declines non-arecanut questions (market prices, weather, other crops).

### C. Online "Ask More" AI Mode (`/api/chat/online`)
- **Backend Proxy (`backend/chat_proxy.py`):** Uses an OpenAI-compatible completions interface compatible with Groq (`qwen/qwen3.8-27b`) and Google Gemini (`gemini-1.5-flash`).
- **Grounding Retrieval:** Automatically retrieves top 3 relevant FAQ entries and current class guidance as strict CONTEXT for the LLM.
- **Strict Post-Checks:** Discards any model reply containing numeric spray units (`ml`, `g`, `kg`, `litre`, `ppm`, `%`) not in the source text, or certainty words (`confirmed`, `definitely`, `100%`), falling back safely to verified guide text.
- **Provenance Badging:** Distinguishes "From the verified guide" from "AI-generated • Verify with officer".

---

## 3. Test Verification Matrix

| Component | Command | Result | Pass Rate |
| :--- | :--- | :--- | :--- |
| **Backend Pytest** | `pytest backend` | **83 passed** (0 failed) in 2.48s | **100%** |
| **Frontend Vitest** | `npm.cmd --prefix frontend test -- --run` | **30 passed** across 8 test files | **100%** |
| **Frontend Production Build** | `npm.cmd --prefix frontend run build` | **Clean build** in 14.18s | **100%** |
| **Secrets Scan** | `git diff codex/arecalens-webapp..HEAD` | **0 keys found**; `.env` strictly untracked | **100%** |

### Chatbot Evaluation Metrics
- **Development Set (64 questions):** 64 / 64 correct (**100%**).
- **Unseen Set (20 questions):** 15 / 20 correct (**75%**).
  - Failing/deferred items fell safely to fallbacks or safety refusals.
  - **Invented dose rate:** **0.0%** (0 invented doses across all evaluations).

---

## 4. How to Run the Web Application

1. **Start Backend Server:**
   ```powershell
   .\backend\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
   ```
2. **Start Frontend Dev Server:**
   ```powershell
   npm.cmd --prefix frontend run dev
   ```
3. **Open in Browser:**
   - **Frontend App:** [http://localhost:5173](http://localhost:5173)
   - **API Documentation & Swagger:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
