"""Offline guide retrieval and optional OpenAI-compatible chat completion."""
import json
import os
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

import logging

from .inference import load_disease_info

logger = logging.getLogger(__name__)
MAX_MESSAGE_LENGTH = 1000
ONLINE_TIMEOUT_SECONDS = 20
ONLINE_MAX_TOKENS = 350

APP_HELP = {
    "en": "Choose Analyse to add a leaf or nut photo, then select Analyse plant health. The guide explains the four supported classes; Scan history keeps up to eight results in this browser.",
    "kn": "ಎಲೆಯ ಅಥವಾ ಅಡಿಕೆಯ ಚಿತ್ರವನ್ನು ಸೇರಿಸಲು ಪರಿಶೀಲನೆ ಆಯ್ಕೆಮಾಡಿ, ನಂತರ ಸಸ್ಯದ ಆರೋಗ್ಯ ಪರಿಶೀಲಿಸಿ ಒತ್ತಿ. ಮಾರ್ಗದರ್ಶಿ ನಾಲ್ಕು ಬೆಂಬಲಿತ ವರ್ಗಗಳನ್ನು ವಿವರಿಸುತ್ತದೆ; ಪರಿಶೀಲನೆ ಇತಿಹಾಸದಲ್ಲಿ ಈ ಬ್ರೌಸರ್‌ನ ಕೊನೆಯ ಎಂಟು ಫಲಿತಾಂಶಗಳು ಉಳಿಯುತ್ತವೆ.",
    "hi": "पत्ती या सुपारी की फोटो जोड़ने के लिए Analyse चुनें, फिर Analyse plant health दबाएँ। गाइड मॉडल की चार समर्थित श्रेणियाँ बताती है; Scan history इस ब्राउज़र में आठ तक परिणाम रखता है।",
    "ml": "ഇലയുടെയോ അടയ്ക്കയുടെയോ ചിത്രം ചേർക്കാൻ പരിശോധന തിരഞ്ഞെടുക്കുക, തുടർന്ന് ചെടിയുടെ ആരോഗ്യം പരിശോധിക്കുക അമർത്തുക. ഗൈഡ് പിന്തുണയ്ക്കുന്ന നാല് വിഭാഗങ്ങൾ വിശദീകരിക്കുന്നു; ഈ ബ്രൗസറിൽ എട്ട് ഫലങ്ങൾ വരെ പരിശോധനാ ചരിത്രത്തിൽ സൂക്ഷിക്കും.",
}

SCAN_HELP = {
    "en": "The scan compares a photo across four trained classes. Its score is a relative model score, not the chance that a diagnosis is correct. A CAM heatmap shows image regions that contributed to the model output; it does not confirm a diseased area or cause. A photo screening can be wrong, so ask an agricultural expert for confirmation.",
    "kn": "ಚಿತ್ರವನ್ನು ನಾಲ್ಕು ತರಬೇತಿ ಪಡೆದ ವರ್ಗಗಳೊಂದಿಗೆ ಹೋಲಿಸಲಾಗುತ್ತದೆ. ಅಂಕವು ಮಾದರಿಯ ತುಲನಾತ್ಮಕ ಅಂಕ ಮಾತ್ರ; ರೋಗನಿರ್ಣಯ ಸರಿಯಾಗಿರುವ ಸಾಧ್ಯತೆಯಲ್ಲ. CAM ಬಣ್ಣದ ನಕ್ಷೆ ಮಾದರಿಯ ಫಲಿತಾಂಶಕ್ಕೆ ಕೊಡುಗೆ ನೀಡಿದ ಭಾಗಗಳನ್ನು ತೋರಿಸುತ್ತದೆ; ಅದು ರೋಗವಿರುವ ಭಾಗ ಅಥವಾ ಕಾರಣವನ್ನು ದೃಢಪಡಿಸುವುದಿಲ್ಲ. ಕೃಷಿ ತಜ್ಞರಿಂದ ದೃಢೀಕರಣ ಪಡೆಯಿರಿ.",
    "hi": "स्कैन फोटो की तुलना मॉडल की चार प्रशिक्षित श्रेणियों से करता है। स्कोर मॉडल का तुलनात्मक स्कोर है, सही निदान की संभावना नहीं। CAM हीटमैप मॉडल के परिणाम में योगदान देने वाले हिस्से दिखाता है; यह रोगग्रस्त क्षेत्र या कारण की पुष्टि नहीं करता। कृषि विशेषज्ञ से पुष्टि लें।",
    "ml": "പരിശോധന ചിത്രം പരിശീലിപ്പിച്ച നാല് വിഭാഗങ്ങളുമായി താരതമ്യം ചെയ്യുന്നു. സ്കോർ മോഡലിന്റെ താരതമ്യ സ്കോർ മാത്രമാണ്; രോഗനിർണയം ശരിയാകാനുള്ള സാധ്യതയല്ല. CAM ഹീറ്റ്മാപ്പ് മോഡലിന്റെ ഫലത്തിന് സംഭാവന നൽകിയ ഭാഗങ്ങൾ കാണിക്കുന്നു; രോഗബാധിത ഭാഗമോ കാരണമോ സ്ഥിരീകരിക്കുന്നില്ല. കൃഷി വിദഗ്ധനോട് സ്ഥിരീകരിക്കുക.",
}

FALLBACK = {
    "en": "I couldn't find a reliable answer to that in the app's guide. Try asking about visible signs, care steps, scan scores, heatmaps, or how to use the app. For diagnosis or treatment, consult an agricultural officer or KVK.",
    "kn": "ಅಪ್ಲಿಕೇಶನ್ ಮಾರ್ಗದರ್ಶಿಯಲ್ಲಿ ಇದಕ್ಕೆ ವಿಶ್ವಾಸಾರ್ಹ ಉತ್ತರ ಸಿಗಲಿಲ್ಲ. ಕಾಣುವ ಲಕ್ಷಣಗಳು, ಆರೈಕೆ, ಸ್ಕೋರ್, ಬಣ್ಣದ ನಕ್ಷೆ ಅಥವಾ ಅಪ್ಲಿಕೇಶನ್ ಬಳಕೆಯ ಬಗ್ಗೆ ಕೇಳಿ. ರೋಗನಿರ್ಣಯ ಅಥವಾ ಚಿಕಿತ್ಸೆಗೆ ಕೃಷಿ ಅಧಿಕಾರಿ ಅಥವಾ KVK ಅವರನ್ನು ಸಂಪರ್ಕಿಸಿ.",
    "hi": "ऐप की गाइड में इसका भरोसेमंद उत्तर नहीं मिला। दिखने वाले लक्षण, देखभाल, स्कोर, हीटमैप या ऐप के उपयोग के बारे में पूछें। निदान या उपचार के लिए कृषि अधिकारी या KVK से संपर्क करें।",
    "ml": "ആപ്പിന്റെ ഗൈഡിൽ ഇതിന് വിശ്വസനീയമായ ഉത്തരം കണ്ടെത്താനായില്ല. കാണുന്ന ലക്ഷണങ്ങൾ, പരിചരണം, സ്കോർ, ഹീറ്റ്മാപ്പ്, അല്ലെങ്കിൽ ആപ്പ് ഉപയോഗം എന്നിവയെക്കുറിച്ച് ചോദിക്കുക. രോഗനിർണയത്തിനും ചികിത്സയ്ക്കും കൃഷി ഉദ്യോഗസ്ഥനെയോ KVK-യെയോ സമീപിക്കുക.",
}

SCAN_TERMS = {
    "kn": ("ಹೀಟ್‌ಮ್ಯಾಪ್", "ಸ್ಕೋರ್", "ಪರಿಶೀಲನೆ", "ಫಲಿತಾಂಶ"),
    "hi": ("हीटमैप", "स्कोर", "परिणाम", "जाँच", "स्कैन"),
    "ml": ("ഹീറ്റ്മാപ്പ്", "സ്കോർ", "ഫലം", "പരിശോധന"),
}

APP_TERMS = {
    "kn": ("ಬಳಸುವುದು", "ಇತಿಹಾಸ", "ಚಿತ್ರ"),
    "hi": ("उपयोग", "फोटो", "इतिहास"),
    "ml": ("ഉപയോഗം", "ചിത്രം", "ചരിത്രം"),
}

THANKS = {
    "en": "You're welcome. Ask another question whenever you're ready.",
    "kn": "ಸ್ವಾಗತ. ನಿಮಗೆ ಬೇಕಾದಾಗ ಮತ್ತೊಂದು ಪ್ರಶ್ನೆ ಕೇಳಿ.",
    "hi": "आपका स्वागत है। चाहें तो अगला प्रश्न पूछें।",
    "ml": "സന്തോഷം. വേണമെങ്കിൽ അടുത്ത ചോദ്യം ചോദിക്കൂ.",
}

EXPERT_NOTE = {
    "en": "A photo screening is not a diagnosis; ask an agricultural officer or KVK if you are concerned.",
    "kn": "ಚಿತ್ರ ಪರಿಶೀಲನೆ ರೋಗನಿರ್ಣಯವಲ್ಲ; ಚಿಂತೆ ಇದ್ದರೆ ಕೃಷಿ ಅಧಿಕಾರಿ ಅಥವಾ KVK ಅವರನ್ನು ಸಂಪರ್ಕಿಸಿ.",
    "hi": "फोटो स्क्रीनिंग निदान नहीं है; चिंता हो तो कृषि अधिकारी या KVK से पूछें।",
    "ml": "ചിത്രപരിശോധന രോഗനിർണയമല്ല; ആശങ്കയുണ്ടെങ്കിൽ കൃഷി ഉദ്യോഗസ്ഥനെയോ KVK-യെയോ സമീപിക്കുക.",
}

EXPERT_QUESTION = {
    "en": ("ask an expert", "when should i ask", "when to ask", "expert help", "get help"),
    "kn": ("ತಜ್ಞರನ್ನು ಯಾವಾಗ", "ಸಹಾಯ ಯಾವಾಗ"),
    "hi": ("विशेषज्ञ से कब", "मदद कब"),
    "ml": ("വിദഗ്ധനെ എപ്പോൾ", "സഹായം എപ്പോൾ"),
}
SIGNS_QUESTION = {
    "en": ("sign", "symptom", "check next", "look for"),
    "kn": ("ಲಕ್ಷಣ", "ಪರಿಶೀಲಿಸಬೇಕು"),
    "hi": ("लक्षण", "जाँचूँ", "देखना चाहिए"),
    "ml": ("ലക്ഷണം", "പരിശോധിക്കണം"),
}
CARE_QUESTION = {
    "en": ("care", "treat", "treatment", "manage", "what should i do", "next step", "advice"),
    "kn": ("ಆರೈಕೆ", "ಚಿಕಿತ್ಸೆ", "ಮುಂದಿನ ಕ್ರಮ"),
    "hi": ("देखभाल", "उपचार", "क्या करें", "अगला कदम"),
    "ml": ("പരിചരണം", "ചികിത്സ", "അടുത്ത നടപടി"),
}
EXPLAIN_QUESTION = {
    "en": ("explain", "why", "tell me more", "more detail", "what does that mean"),
    "kn": ("ವಿವರಿಸ", "ಅರ್ಥವೇನು"),
    "hi": ("समझा", "और बताइए", "मतलब"),
    "ml": ("വിശദീകരി", "കൂടുതൽ പറയൂ", "അർത്ഥം"),
}
CLASS_ALIASES = {
    "Healthy_Leaf": ("healthy leaf", "healthy leaves"),
    "Healthy_Nut": ("healthy nut", "healthy nuts"),
    "Mahali_Koleroga": ("mahali", "koleroga", "fruit rot"),
    "Yellow_Leaf": ("yellow leaf", "yellowing", "leaf spot", "leaf spotting"),
}


def online_chat_available():
    api_key = os.environ.get("CHATBOT_API_KEY", "").strip()
    endpoint = os.environ.get("CHATBOT_API_URL", "https://api.openai.com/v1/chat/completions").strip()
    model = os.environ.get("CHATBOT_MODEL", "gpt-4o-mini").strip()
    try:
        parsed_endpoint = urlsplit(endpoint)
    except ValueError:
        return False
    return bool(
        api_key
        and parsed_endpoint.scheme == "https"
        and parsed_endpoint.hostname
        and not parsed_endpoint.username
        and not parsed_endpoint.password
        and model
    )


def _text_items(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        if value.get("verify") is True:
            return
        for key, item in value.items():
            if key == "verify":
                continue
            if key in {"text", "display_name", "short_name"} and isinstance(item, str):
                yield item
            else:
                yield from _text_items(item)
    elif isinstance(value, list):
        for item in value:
            yield from _text_items(item)


def _safe_care_text(value):
    return not re.search(
        r"\b(?:bordeaux|spray|pesticide|fungicide|insecticide|antibiotic)\b|"
        r"\b\d+(?:\.\d+)?\s*(?:%|g\b|kg\b|ml\b|l\b|litres?\b|days?\b|weeks?\b)",
        value,
        flags=re.IGNORECASE,
    )


def _tokens(value):
    return {token.lower() for token in re.findall(r"[^\W_]+", value, flags=re.UNICODE) if len(token) > 2}


def _legacy_offline_answer(message, language, history=()):
    recent_topic = next(
        (turn["content"] for turn in reversed(history) if turn["role"] == "user"),
        "",
    )
    question = (message + " " + recent_topic).casefold()
    info = load_disease_info(language)
    if any(term in question for term in SCAN_TERMS.get(language, ())):
        return SCAN_HELP[language]
    if any(term in question for term in APP_TERMS.get(language, ())):
        return APP_HELP[language]
    if any(word in question for word in ("heatmap", "heat map", "cam", "score", "confidence", "scan", "result", "prediction", "സ്കോർ", "സ്കാൻ", "ಸ್ಕೋರ್", "जाँच", "स्कोर")):
        return SCAN_HELP[language]
    if any(word in question for word in ("how do i use", "how to use", "use the app", "history", "upload", "photo", "ಚಿತ್ರ", "ಬಳಸುವುದು", "कैसे इस्तेमाल", "फोटो", "ഉപയോഗം", "ചിത്രം")):
        return APP_HELP[language]

    if any(word in question for word in ("sign", "symptom", "look for", "लक्षण", "ಲಕ್ಷಣ", "ലക്ഷണം")):
        lines = []
        for details in info["classes"].values():
            signs = _text_items(details.get("check_signs", [])) or _text_items(details.get("signs_to_watch", []))
            first = next(iter(signs), None)
            if first:
                lines.append(f"{details.get('display_name', details.get('short_name', ''))}: {first}")
        return " ".join(lines) if lines else FALLBACK[language]
    if any(word in question for word in ("care", "treat", "treatment", "manage", "spray", "उपचार", "देखभाल", "ಆರೈಕೆ", "ಚಿಕಿತ್ಸೆ", "പരിചരണം", "ചികിത്സ")):
        lines = []
        for details in info["classes"].values():
            actions = (text for text in _text_items(details.get("what_to_do", [])) if _safe_care_text(text))
            first = next(iter(actions), None)
            if first:
                lines.append(f"{details.get('display_name', details.get('short_name', ''))}: {first}")
        if lines:
            return " ".join(lines) + " " + info.get("disclaimer", {}).get("text", "")

    query_tokens = _tokens(message)
    if not query_tokens:
        return FALLBACK[language]
    candidates = []
    for class_id, details in info["classes"].items():
        class_tokens = _tokens(details.get("display_name", "") + " " + details.get("short_name", ""))
        for field in ("summary", "signs_to_watch", "what_to_do", "what_it_means", "limits", "check_signs"):
            for text in _text_items(details.get(field, [])):
                if not _safe_care_text(text):
                    continue
                overlap = query_tokens & (_tokens(text) | class_tokens)
                if overlap:
                    candidates.append((len(overlap) / len(query_tokens), len(overlap), text))
    if not candidates:
        return FALLBACK[language]
    candidates.sort(key=lambda candidate: (candidate[0], candidate[1]), reverse=True)
    best_score = candidates[0][0]
    if best_score < 0.25:
        return FALLBACK[language]
    selected = []
    for score, _, text in candidates:
        if score < best_score * 0.75 or text in selected:
            continue
        selected.append(text)
        if len(selected) == 2:
            break
    answer = " ".join(selected)
    disclaimer = info.get("disclaimer", {}).get("text")
    if disclaimer and disclaimer not in answer:
        answer += " " + disclaimer
    return answer


def _class_from_context(message, history):
    context = [message, *(turn["content"] for turn in reversed(history))]
    for content in context:
        lowered = content.casefold()
        for class_id, aliases in CLASS_ALIASES.items():
            if any(alias in lowered for alias in aliases):
                return class_id
    return None


def _guide_text(details, field):
    value = details.get(field)
    if field == "summary" and isinstance(value, dict):
        value = [value]
    return list(_text_items(value))


def _not_already_said(text, history):
    normalized = re.sub(r"\W+", " ", text.casefold()).strip()
    previous_answers = (
        re.sub(r"\W+", " ", turn["content"].casefold()).strip()
        for turn in history
        if turn["role"] == "assistant"
    )
    return all(normalized not in previous for previous in previous_answers)


def _offline_answer(message, language, history=()):
    question = message.casefold().strip()
    info = load_disease_info(language)
    if question in {"okay", "ok", "thanks", "thank you", "ಧನ್ಯವಾದ", "धन्यवाद", "നന്ദി"}:
        return THANKS[language]
    if any(term in question for term in SCAN_TERMS.get(language, ())) or any(
        term in question for term in ("heatmap", "heat map", "cam", "score", "confidence", "scan result", "prediction")
    ):
        return SCAN_HELP[language]
    if any(term in question for term in APP_TERMS.get(language, ())) or any(
        phrase in question for phrase in ("how do i use", "how to use", "use the app", "scan history", "upload a photo")
    ):
        return APP_HELP[language]

    class_id = _class_from_context(message, history)
    is_expert_question = any(term in question for term in EXPERT_QUESTION[language])
    is_signs_question = any(term in question for term in SIGNS_QUESTION[language])
    is_care_question = any(term in question for term in CARE_QUESTION[language])
    is_explain_question = any(term in question for term in EXPLAIN_QUESTION[language])
    if not any((is_expert_question, is_signs_question, is_care_question, is_explain_question)) or class_id is None:
        return FALLBACK[language]

    details = info["classes"][class_id]
    if is_expert_question:
        candidates = _guide_text(details, "when_to_get_help") + _guide_text(details, "limits")
        answer = next((text for text in candidates if _not_already_said(text, history)), None)
        return answer or EXPERT_NOTE[language]
    if is_signs_question:
        candidates = _guide_text(details, "check_signs") or _guide_text(details, "signs_to_watch")
        answer = next((text for text in candidates if _not_already_said(text, history)), None)
        return answer or EXPERT_NOTE[language]
    if is_care_question:
        candidates = [
            text for text in _guide_text(details, "what_to_do")
            if _safe_care_text(text) and _not_already_said(text, history)
        ]
        return candidates[0] + " " + EXPERT_NOTE[language] if candidates else EXPERT_NOTE[language]
    if is_explain_question:
        candidates = (
            _guide_text(details, "what_it_means")
            + _guide_text(details, "possible_causes")
            + _guide_text(details, "check_signs")
            + _guide_text(details, "summary")
        )
        answer = next(
            (
                text for text in candidates
                if _safe_care_text(text) and _not_already_said(text, history)
            ),
            None,
        )
        return answer or FALLBACK[language]
    return FALLBACK[language]


def _online_answer(message, language, history=()):
    api_key = os.environ.get("CHATBOT_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Online chat is not configured on this server.")
    endpoint = os.environ.get("CHATBOT_API_URL", "https://api.openai.com/v1/chat/completions").strip()
    model = os.environ.get("CHATBOT_MODEL", "gpt-4o-mini").strip()
    try:
        parsed_endpoint = urlsplit(endpoint)
    except ValueError as exc:
        raise RuntimeError("The configured online chat endpoint is invalid.") from exc
    if parsed_endpoint.scheme != "https" or not parsed_endpoint.hostname or parsed_endpoint.username or parsed_endpoint.password:
        raise RuntimeError("The configured online chat endpoint must use HTTPS and must not contain credentials.")
    if not model:
        raise RuntimeError("The configured online chat model cannot be empty.")

    info = load_disease_info(language)
    reference = "\n".join(
        text
        for details in info["classes"].values()
        for field in ("display_name", "short_name", "summary", "check_signs", "possible_causes", "what_to_do", "when_to_get_help", "limits")
        for text in _text_items(details.get(field))
        if field not in {"what_to_do", "when_to_get_help"} or _safe_care_text(text)
    )
    reference += "\n" + info.get("disclaimer", {}).get("text", "")
    language_names = {"en": "English", "kn": "Kannada", "hi": "Hindi", "ml": "Malayalam"}
    system_prompt = (
        "You are ArecaLens, a cautious arecanut education assistant. Answer in "
        + language_names[language]
        + ". Keep answers concise and relevant. Treat the supplied reference as draft guidance, not verified medical/agricultural authority. "
        "Do not diagnose, prescribe pesticide doses or invent local recommendations. Explain that photo screening can be wrong, model scores are not diagnostic probabilities, "
        "and CAM heatmaps do not confirm disease. For unsupported or risky treatment questions, say so and refer to an agricultural officer/KVK/ICAR-CPCRI. "
        "Do not claim to have seen any image: none is sent. Reference material:\n"
        + reference[:12000]
    )
    data = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            *[
                {"role": turn["role"], "content": turn["content"]}
                for turn in history[-6:]
            ],
            {"role": "user", "content": message},
        ],
        "max_tokens": ONLINE_MAX_TOKENS,
        "temperature": 0.2,
    }).encode("utf-8")
    request = Request(endpoint, data=data, headers={
        "Authorization": "Bearer " + api_key,
        "Content-Type": "application/json",
    }, method="POST")
    try:
        with urlopen(request, timeout=ONLINE_TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read(256 * 1024).decode("utf-8"))
    except HTTPError as exc:
        try:
            provider_error = exc.read(4096).decode("utf-8", errors="replace")
            parsed_error = json.loads(provider_error)
            detail = parsed_error.get("error", {}).get("message", "")
        except (OSError, json.JSONDecodeError, AttributeError, TypeError):
            detail = ""
        if not isinstance(detail, str):
            detail = ""
        detail = detail.replace(api_key, "[redacted]")[:500]
        logger.warning("Online chat provider returned HTTP %s: %s", exc.code, detail or "no error detail")
        if exc.code in {401, 403}:
            message = "The online provider rejected the API key or its permissions. Verify the key and Gemini API access."
        elif exc.code == 404:
            message = "The online provider could not find the configured model or endpoint. Verify CHATBOT_MODEL and CHATBOT_API_URL."
        elif exc.code == 429:
            message = "The online provider quota or rate limit was reached. Check the provider's quota and billing."
        else:
            message = f"The online provider rejected the request (HTTP {exc.code}). Check the backend console for details."
        raise RuntimeError(message) from exc
    except (URLError, TimeoutError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise RuntimeError("The online provider is unavailable. Check the server configuration and connection.") from exc
    try:
        answer = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("The online provider returned an unreadable response.") from exc
    if isinstance(answer, list):
        answer = "\n".join(
            part["text"] for part in answer
            if isinstance(part, dict) and isinstance(part.get("text"), str)
        )
    if not isinstance(answer, str) or not answer.strip():
        raise RuntimeError("The online provider returned an empty answer.")
    return answer.strip()[:4000]


def chat_answer(message, mode="offline", language="en", history=()):
    if not isinstance(message, str) or not message.strip() or len(message) > MAX_MESSAGE_LENGTH:
        raise ValueError("Invalid question.")
    if mode == "offline":
        return _offline_answer(message.strip(), language, history)
    if mode == "online":
        return _online_answer(message.strip(), language, history)
    raise ValueError("Unsupported chat mode.")
