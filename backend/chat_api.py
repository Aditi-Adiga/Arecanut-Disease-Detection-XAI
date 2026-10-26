import json
import logging
import threading
import time
from collections import defaultdict
from pathlib import Path
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator

from .chat_engine import ChatEngine

logger = logging.getLogger(__name__)

ClassName = Literal["Healthy_Leaf", "Healthy_Nut", "Mahali_Koleroga", "Yellow_Leaf"]
LanguageCode = Literal["en", "kn", "hi", "ml"]

# Valid FAQ entry IDs (loaded at startup; used to validate the entry_id direct-lookup field)
_VALID_ENTRY_IDS: set[str] = set()

DATA_DIR = Path(__file__).resolve().parent / "data"
FAQ_PATH = DATA_DIR / "chatbot_faq.json"
DISEASE_INFO_PATH = DATA_DIR / "disease_info.json"


def validate_faq_data(faq: dict) -> None:
    entries = {e["id"]: e for e in faq.get("entries", [])}
    for chip_id in faq.get("chips", []):
        if chip_id not in entries:
            raise ValueError(f"Invalid chip id in FAQ data: '{chip_id}' (not found in entries)")

    sources = faq.get("sources", {})
    for entry in faq.get("entries", []):
        entry_id = entry.get("id", "unknown")
        for source_id in entry.get("sources", []):
            if source_id not in sources:
                raise ValueError(
                    f"Invalid source id '{source_id}' used by entry '{entry_id}' (not found in sources)"
                )


def load_chat_data() -> tuple[dict, dict, ChatEngine]:
    if not FAQ_PATH.is_file():
        raise FileNotFoundError(f"Chatbot FAQ data file missing: {FAQ_PATH}")
    if not DISEASE_INFO_PATH.is_file():
        raise FileNotFoundError(f"Disease info file missing: {DISEASE_INFO_PATH}")

    with open(FAQ_PATH, encoding="utf-8") as f:
        faq = json.load(f)
    with open(DISEASE_INFO_PATH, encoding="utf-8") as f:
        disease_info = json.load(f)

    validate_faq_data(faq)
    engine = ChatEngine(faq, disease_info)
    return faq, disease_info, engine


faq_data, disease_info_data, chat_engine = load_chat_data()
_VALID_ENTRY_IDS.update(e["id"] for e in faq_data.get("entries", []))


class InMemoryRateLimiter:
    def __init__(self, max_requests: int = 30, window_seconds: float = 60.0):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: dict[str, list[float]] = defaultdict(list)
        self.lock = threading.Lock()

    def is_allowed(self, client_ip: str) -> bool:
        now = time.time()
        with self.lock:
            cutoff = now - self.window_seconds
            valid_times = [t for t in self.requests[client_ip] if t > cutoff]
            if len(valid_times) >= self.max_requests:
                self.requests[client_ip] = valid_times
                return False
            valid_times.append(now)
            self.requests[client_ip] = valid_times
            return True


rate_limiter = InMemoryRateLimiter(max_requests=30, window_seconds=60.0)


class ChatContext(BaseModel):
    cls: Optional[ClassName] = Field(None, alias="class")
    status: Optional[str] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)

    model_config = ConfigDict(populate_by_name=True)


class ChatRequest(BaseModel):
    message: str
    language: LanguageCode = "en"
    context: Optional[ChatContext] = None
    # Optional: when set, skip NLP inference and return the entry directly.
    # Sent by the frontend when the user clicks a chip whose entry_id is known.
    entry_id: Optional[str] = None

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        stripped = v.strip()
        if not (1 <= len(stripped) <= 300):
            raise ValueError("Message must be 1 to 300 characters after stripping.")
        return stripped

    @field_validator("entry_id")
    @classmethod
    def validate_entry_id(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        if v not in _VALID_ENTRY_IDS:
            raise ValueError(f"Unknown entry_id: '{v}'")
        return v


class SourceItem(BaseModel):
    id: str
    title: str
    publisher: str
    year: str
    url: str


class SuggestionItem(BaseModel):
    id: str
    question: str


class ChatResponse(BaseModel):
    answer: str
    intent: str
    entry_id: Optional[str] = None
    sources: list[SourceItem]
    refused: bool
    needs_expert_review: bool
    language_fallback: bool
    suggestions: list[SuggestionItem]
    ai_generated: bool = False
    answer_source: Literal["engine"] = "engine"


def format_chat_response(reply: dict) -> ChatResponse:
    expanded_sources: list[SourceItem] = []
    faq_sources = faq_data.get("sources", {})
    for sid in reply.get("sources", []):
        if sid in faq_sources:
            src = faq_sources[sid]
            expanded_sources.append(
                SourceItem(
                    id=sid,
                    title=src.get("title", ""),
                    publisher=src.get("publisher", ""),
                    year=str(src.get("year", "")),
                    url=src.get("url", ""),
                )
            )

    suggestions = [
        SuggestionItem(id=s["id"], question=s["question"])
        for s in reply.get("suggestions", [])
    ]

    return ChatResponse(
        answer=reply["answer"],
        intent=reply["intent"],
        entry_id=reply.get("entry_id"),
        sources=expanded_sources,
        refused=reply.get("refused", False),
        needs_expert_review=reply.get("needs_expert_review", False),
        language_fallback=reply.get("language_fallback", False),
        suggestions=suggestions,
        ai_generated=False,
        answer_source="engine",
    )


router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.get("/chips")
def get_chips(language: LanguageCode = "en", ids: Optional[str] = None):
    """Return starter chip labels in *language*.

    When *ids* is provided (comma-separated entry IDs) only those entries are
    returned, in the order given.  Unknown IDs are silently skipped.
    This is used by the frontend to refresh stale follow-up chip labels when the
    UI language changes.
    """
    if ids:
        id_list = [i.strip() for i in ids.split(",") if i.strip()]
        # Filter to known entries only
        id_list = [i for i in id_list if i in _VALID_ENTRY_IDS]
        chips = chat_engine._chips(language, id_list)
    else:
        chips = chat_engine._chips(language)
    return {"chips": chips}


@router.post("", response_model=ChatResponse)
def post_chat(payload: ChatRequest, request: Request):
    client_ip = request.client.host if request.client else "unknown"
    if not rate_limiter.is_allowed(client_ip):
        # Log rate-limit hit without logging any message text
        logger.warning("Chat rate limit exceeded for client %s", client_ip)
        raise HTTPException(status_code=429, detail="Too many chat requests. Please wait a moment.")

    engine_context = {}
    if payload.context:
        if payload.context.cls is not None:
            engine_context["class"] = payload.context.cls
        if payload.context.status is not None:
            engine_context["status"] = payload.context.status
        if payload.context.confidence is not None:
            engine_context["confidence"] = payload.context.confidence

    # Direct entry lookup: chip clicks send entry_id so we skip NLP scoring.
    if payload.entry_id:
        reply = chat_engine.answer_by_id(
            payload.entry_id,
            language=payload.language,
            context=engine_context,
        )
    else:
        reply = chat_engine.answer(payload.message, language=payload.language, context=engine_context)

    return format_chat_response(reply)
