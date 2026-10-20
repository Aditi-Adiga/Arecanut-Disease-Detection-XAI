import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

from .inference import Predictor, load_disease_info
from .preprocessing import MAX_BYTES
from .chat import chat_answer, online_chat_available

logger = logging.getLogger(__name__)


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=1000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    mode: Literal["offline", "online"] = "offline"
    language: Literal["en", "kn", "hi", "ml"] = "en"
    history: list[ChatTurn] = Field(default_factory=list, max_length=6)


@asynccontextmanager
async def lifespan(app):
    app.state.predictor = None
    app.state.model_error = None
    try:
        app.state.predictor = await run_in_threadpool(Predictor)
    except Exception as exc:
        app.state.model_error = "Model unavailable. Check the model assets and server console."
        logger.exception("Model startup failed: %s", exc)
    yield


app = FastAPI(title="Arecanut XAI API", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
                   allow_credentials=False, allow_methods=["GET", "POST"], allow_headers=["*"])


@app.get("/api/health")
def health():
    ready = getattr(app.state, "predictor", None) is not None
    return {"status": "ready" if ready else "unavailable", "model_loaded": ready,
            "detail": getattr(app.state, "model_error", None), "model": "MobileNetV3Small"}


@app.get("/api/diseases")
def diseases(language: Literal["en", "kn", "hi", "ml"] = "en"):
    return load_disease_info(language)


@app.get("/api/chat/status")
def chat_status():
    return {"online_available": online_chat_available()}


@app.post("/api/chat")
def chat(payload: ChatRequest):
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="Enter a question.")
    try:
        history = [turn.model_dump() for turn in payload.history]
        return {"answer": chat_answer(payload.message.strip(), payload.mode, payload.language, history)}
    except RuntimeError as exc:
        logger.warning("Chat request could not be completed: %s", exc)
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Chat request failed")
        raise HTTPException(status_code=502, detail="The chat service failed unexpectedly. Check the backend console for details.") from exc


@app.get("/api/ready")
def ready():
    if getattr(app.state, "predictor", None) is None:
        raise HTTPException(status_code=503, detail="Model is not ready.")
    return {"status": "ready"}


@app.post("/api/predict")
async def predict(file: UploadFile = File(...), language: Literal["en", "kn", "hi", "ml"] = "en"):
    try:
        content = await file.read(MAX_BYTES + 1)
    finally:
        await file.close()
    if not content:
        raise HTTPException(status_code=400, detail="Choose an image before analysing.")
    if len(content) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="The image must be 10 MB or smaller.")
    predictor = getattr(app.state, "predictor", None)
    if predictor is None:
        raise HTTPException(status_code=503, detail="The model is not ready. Check the server console.")
    try:
        return await run_in_threadpool(predictor.predict, content, language)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Prediction failed")
        raise HTTPException(status_code=500, detail="Analysis failed. Please try another image.") from exc


# A production React build is served by FastAPI: one server, including offline.
DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/")
    def index():
        return FileResponse(DIST / "index.html")
