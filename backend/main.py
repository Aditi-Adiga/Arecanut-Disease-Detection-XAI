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

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from .inference import Predictor, load_disease_info
from .preprocessing import MAX_BYTES
from .chat_api import router as chat_router

logger = logging.getLogger(__name__)


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
app.include_router(chat_router)


@app.get("/api/health")
def health():
    ready = getattr(app.state, "predictor", None) is not None
    return {"status": "ready" if ready else "unavailable", "model_loaded": ready,
            "detail": getattr(app.state, "model_error", None), "model": "MobileNetV3Small"}


@app.get("/api/diseases")
def diseases(language: Literal["en", "kn", "hi", "ml"] = "en"):
    return load_disease_info(language)


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
