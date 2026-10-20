"""Online 'Ask more' LLM proxy for ArecaLens.

Proxies user questions to an OpenAI-compatible LLM endpoint (such as Gemini's OpenAI-compatible endpoint)
grounded strictly in the retrieved FAQ and disease guide context.
Includes:
- Strict safety pre-checks (health, dose, chemical, confirm, out-of-scope).
- Deterministic context retrieval via ChatEngine.top_k and disease_info.
- Mandatory system prompt enforcing groundedness, safety, and conciseness.
- Post-checks blocking hallucinated spray amounts, doses, percentages, and certainty claims.
- Graceful fallback to offline guide answers on any provider or network failure.
- Zero logging of message text, API keys, or provider response bodies.
"""

import json
import logging
import os
import re
import socket
import urllib.error
import urllib.request
from typing import Any, Optional

from .chat_engine import (
    _CHEM,
    _CONFIRM,
    _DOSE,
    _HEALTH,
    _OUT,
    ChatEngine,
)

logger = logging.getLogger(__name__)

# Pattern to detect any number followed by dose/concentration units or percentage:
# e.g. 5ml, 10 g, 2.5 kg, 1 litre, 500 ppm, 1%, 100%
_NUMERIC_UNIT_PATTERN = re.compile(
    r"\b\d+(?:\.\d+)?\s*(?:(?:ml|mg|g|kg|litre|liter|litres|liters|ppm)\b|%)",
    re.IGNORECASE,
)

# Certainty terms forbidden in assistant responses:
_CERTAINTY_PATTERN = re.compile(
    r"(?:\b(?:confirmed|confirming|confirmation|definitely|definite)\b|100\s*%)",
    re.IGNORECASE,
)

_LANGUAGE_NAMES = {
    "en": "English",
    "kn": "Kannada",
    "hi": "Hindi",
    "ml": "Malayalam",
}


def is_online_enabled() -> bool:
    """Return True only if ENABLE_LLM_CHAT is enabled and all credentials/endpoints are set."""
    flag = os.environ.get("ENABLE_LLM_CHAT", "").strip().lower()
    if flag not in ("1", "true", "yes", "on"):
        return False
    key = os.environ.get("CHATBOT_API_KEY", "").strip()
    url = os.environ.get("CHATBOT_API_URL", "").strip()
    model = os.environ.get("CHATBOT_MODEL", "").strip()
    return bool(key and url and model)


def build_retrieved_context(
    chat_engine: ChatEngine,
    disease_info: dict,
    message: str,
    context: Optional[dict] = None,
    k: int = 3,
) -> tuple[str, list[dict], list[str], bool]:
    """Retrieve top k entries and current class guidance, formatting the CONTEXT block.
    
    Returns:
        (context_text, top_entries, source_ids, needs_expert_review)
    """
    ctx = context or {}
    top_entries = chat_engine.top_k(message, k=k, context=ctx)
    source_ids: set[str] = set()
    needs_expert_review = False
    context_blocks: list[str] = []

    for idx, entry in enumerate(top_entries, 1):
        q_label = (entry.get("questions") or [""])[0] or entry.get("id", "")
        context_blocks.append(f"Guide Entry {idx} ({q_label}):\n{entry.get('answer', '')}")
        for s in entry.get("sources", []):
            source_ids.add(s)
        if entry.get("needs_expert_review"):
            needs_expert_review = True

    cls_name = ctx.get("class")
    if cls_name and disease_info and "classes" in disease_info and cls_name in disease_info["classes"]:
        ci = disease_info["classes"][cls_name]
        summary_text = ci.get("summary", {}).get("text", "")
        for s in ci.get("summary", {}).get("sources", []):
            source_ids.add(s)
        what_to_do = ci.get("what_to_do", [])
        todo_lines = []
        for item in what_to_do:
            todo_lines.append(f"- {item.get('text', '')}")
            for s in item.get("sources", []):
                source_ids.add(s)
        advice_parts = [summary_text]
        if todo_lines:
            advice_parts.append("What to do:\n" + "\n".join(todo_lines))
        if ci.get("limits"):
            advice_parts.append(ci["limits"].get("text", ""))
        context_blocks.append(f"Current Result Context ({cls_name}):\n" + "\n\n".join(advice_parts))

    return "\n\n".join(context_blocks), top_entries, sorted(source_ids), needs_expert_review


def post_check_response(llm_reply: str, retrieved_context: str) -> tuple[bool, Optional[str]]:
    """Validate model reply against strict safety rules.
    
    Discards reply if:
    - Contains certainty words (confirmed, definitely, 100%)
    - Contains numeric measurements (ml, g, kg, litre, ppm, %) not in retrieved context
    
    Returns:
        (is_valid, cleaned_or_truncated_text)
    """
    if not llm_reply or not llm_reply.strip():
        return False, None

    text = llm_reply.strip()

    # 1. Certainty words check
    if _CERTAINTY_PATTERN.search(text):
        logger.warning("Online chat post-check rejected: certainty wording found in model response.")
        return False, None

    # 2. Number + unit or % check
    context_lower = retrieved_context.lower()
    for match in _NUMERIC_UNIT_PATTERN.finditer(text):
        unit_token = match.group(0).lower().strip()
        # Normalise multiple spaces between number and unit for matching
        normalized_token = re.sub(r"\s+", " ", unit_token)
        # Check if the number+unit appears anywhere in the retrieved guide context
        if normalized_token not in context_lower and unit_token not in context_lower:
            logger.warning(
                "Online chat post-check rejected: ungrounded dose/unit/percentage found in model response."
            )
            return False, None

    # 3. Extra check for hallucinated dose/spray instructions not in context
    if _DOSE.search(text) and not _DOSE.search(retrieved_context):
        logger.warning("Online chat post-check rejected: ungrounded dose advice pattern found.")
        return False, None

    # 4. Enforce 120-word limit
    words = text.split()
    if len(words) > 120:
        text = " ".join(words[:120]) + "…"

    return True, text


def call_openai_chat_completions(
    api_url: str,
    api_key: str,
    model: str,
    messages: list[dict],
    timeout: float = 15.0,
) -> tuple[Optional[str], Optional[str]]:
    """Invoke OpenAI-compatible chat completions endpoint with timeout.
    
    Returns:
        (response_content, error_type)
        where error_type is one of:
        "not_configured", "timeout", "auth", "model_not_found", "rate_limited", "provider_error", "network"
    """
    # Normalise endpoint URL
    url = api_url.strip()
    if not url.endswith("/chat/completions"):
        if url.endswith("/"):
            url += "chat/completions"
        else:
            url += "/chat/completions"

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.1,
        "max_tokens": 300,
    }
    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "ArecaLens/1.0",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.status
            raw_body = resp.read().decode("utf-8")
            parsed = json.loads(raw_body)
            choices = parsed.get("choices", [])
            if not choices:
                return None, "provider_error"
            content = choices[0].get("message", {}).get("content", "")
            return content, None

    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            logger.warning("Online chat provider auth failure (HTTP %d)", exc.code)
            return None, "auth"
        elif exc.code == 404:
            logger.warning("Online chat model/URL not found (HTTP 404)")
            return None, "model_not_found"
        elif exc.code == 429:
            logger.warning("Online chat provider rate limit exceeded (HTTP 429)")
            return None, "rate_limited"
        elif 500 <= exc.code <= 599:
            logger.warning("Online chat provider internal error (HTTP %d)", exc.code)
            return None, "provider_error"
        else:
            logger.warning("Online chat provider error (HTTP %d)", exc.code)
            return None, "provider_error"

    except (urllib.error.URLError, socket.timeout, TimeoutError) as exc:
        is_timeout = isinstance(exc, (socket.timeout, TimeoutError)) or (
            isinstance(exc, urllib.error.URLError) and isinstance(exc.reason, socket.timeout)
        )
        if is_timeout:
            logger.warning("Online chat request timed out after %.1fs", timeout)
            return None, "timeout"
        logger.warning("Online chat network connection failure")
        return None, "network"

    except Exception as exc:
        logger.warning("Online chat unexpected error during provider call")
        return None, "provider_error"


def answer_online(
    chat_engine: ChatEngine,
    disease_info: dict,
    faq_sources: dict,
    message: str,
    language: str = "en",
    context: Optional[dict] = None,
    history: Optional[list[dict]] = None,
) -> dict:
    """Execute grounded online answer flow with safety pre-checks, LLM proxy, and post-checks.
    
    Returns a dict adhering to the ChatResponse schema.
    Always falls back gracefully to the offline ChatEngine answer on any failure.
    """
    msg = (message or "").strip()
    low = msg.lower()
    ctx = context or {}

    # 1. Safety Pre-checks: Return offline response immediately; never call LLM provider
    if _HEALTH.search(low):
        return chat_engine.answer(msg, language=language, context=ctx)
    if re.search(r"bordeaux|bordo", low) and (_DOSE.search(low) or re.search(r"copper|sulphate|lime|make|prepar", low)):
        return chat_engine.answer(msg, language=language, context=ctx)
    if _DOSE.search(low):
        return chat_engine.answer(msg, language=language, context=ctx)
    if _CHEM.search(low):
        return chat_engine.answer(msg, language=language, context=ctx)
    if _OUT.search(low):
        return chat_engine.answer(msg, language=language, context=ctx)
    if _CONFIRM.search(low):
        return chat_engine.answer(msg, language=language, context=ctx)

    # 2. Check if online mode is configured
    if not is_online_enabled():
        offline_rep = chat_engine.answer(msg, language=language, context=ctx)
        offline_rep["ai_generated"] = False
        offline_rep["answer_source"] = "guide"
        offline_rep["online_error"] = "not_configured"
        return offline_rep

    # 3. Retrieve grounding context (top 3 FAQ entries + disease info class advice)
    context_str, top_entries, source_ids, needs_expert_review = build_retrieved_context(
        chat_engine, disease_info, msg, context=ctx, k=3
    )

    lang_name = _LANGUAGE_NAMES.get(language, "English")
    system_prompt = (
        "You are the assistant inside ArecaLens, an arecanut leaf and nut health app. "
        "Answer ONLY from the CONTEXT below. If the context does not contain the answer, "
        "say you do not know and suggest asking an agricultural officer or KVK. "
        "Never give spray doses, mixing amounts or product names. "
        "Never say a disease is confirmed; say suspected or consistent with. "
        f"Keep answers under 120 words, in simple language, in {lang_name}. "
        "If asked about people's health, prices, weather or other crops, politely decline.\n\n"
        f"CONTEXT:\n{context_str}"
    )

    # 4. Prepare message list (include up to 6 client turns if provided)
    llm_messages = [{"role": "system", "content": system_prompt}]
    if history and isinstance(history, list):
        for turn in history[-6:]:
            if isinstance(turn, dict) and turn.get("role") in ("user", "assistant") and turn.get("content"):
                llm_messages.append({"role": turn["role"], "content": str(turn["content"])[:300]})
    llm_messages.append({"role": "user", "content": msg})

    # 5. Call LLM provider
    api_url = os.environ.get("CHATBOT_API_URL", "").strip()
    api_key = os.environ.get("CHATBOT_API_KEY", "").strip()
    model = os.environ.get("CHATBOT_MODEL", "").strip()

    raw_reply, err = call_openai_chat_completions(
        api_url=api_url,
        api_key=api_key,
        model=model,
        messages=llm_messages,
        timeout=15.0,
    )

    if err or not raw_reply:
        offline_rep = chat_engine.answer(msg, language=language, context=ctx)
        offline_rep["ai_generated"] = False
        offline_rep["answer_source"] = "guide"
        offline_rep["online_error"] = err or "provider_error"
        return offline_rep

    # 6. Post-check model reply
    valid, cleaned_answer = post_check_response(raw_reply, context_str)
    if not valid or not cleaned_answer:
        logger.warning("Online reply failed safety post-check, falling back to offline answer")
        offline_rep = chat_engine.answer(msg, language=language, context=ctx)
        offline_rep["ai_generated"] = False
        offline_rep["answer_source"] = "guide"
        offline_rep["online_error"] = "provider_error"
        return offline_rep

    # 7. Format successful online response
    top_entry_id = top_entries[0]["id"] if top_entries else None
    suggestions = chat_engine._chips(language)
    if top_entries and top_entries[0].get("topic"):
        topic = top_entries[0]["topic"]
        same = [x for x, ee in chat_engine.entries.items() if ee["topic"] == topic and x != top_entry_id][:3]
        if same:
            suggestions = chat_engine._chips(language, same)

    return {
        "answer": cleaned_answer,
        "intent": "online_llm",
        "entry_id": top_entry_id,
        "sources": source_ids,
        "refused": False,
        "needs_expert_review": needs_expert_review,
        "language_fallback": False,
        "suggestions": suggestions,
        "ai_generated": True,
        "answer_source": "ai",
        "online_error": None,
    }
