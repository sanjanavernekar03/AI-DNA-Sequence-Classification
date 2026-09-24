import json
import logging
import urllib.error
import urllib.request
from typing import Any, Dict, List

from flask import current_app

logger = logging.getLogger(__name__)

class ChatbotServiceError(RuntimeError):
    """Raised when the local chatbot service cannot answer a request."""


def get_chatbot_response(
    user_message: str,
    current_page: str = "",
    language: str = "en",
    conversation: List[Dict[str, str]] | None = None,
) -> Dict[str, Any]:
    """Generate a real response from the configured local Ollama model."""
    message = user_message.strip()
    if not message:
        raise ChatbotServiceError("Message cannot be empty.")

    model = current_app.config.get("OLLAMA_MODEL", "llama3.2")
    base_url = current_app.config.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")

    try:
        response_text = _call_ollama(
            message,
            language,
            conversation or [],
            model,
            base_url,
        )
    except TimeoutError as exc:
        logger.warning("Ollama connection timed out: %s", exc)
        raise ChatbotServiceError("The AI model is warming up or taking longer to process. Please try sending your message again.") from exc
    except urllib.error.HTTPError as exc:
        logger.warning("Ollama returned HTTP status %s", exc.code)
        if exc.code == 404:
            # Fallback to model:latest if base model name threw 404
            if not model.endswith(":latest"):
                try:
                    response_text = _call_ollama(
                        message,
                        language,
                        conversation or [],
                        f"{model}:latest",
                        base_url,
                    )
                    return {"response": response_text, "language": language}
                except Exception:
                    pass
            raise ChatbotServiceError(f"The selected model '{model}' is not installed in Ollama. Pull it using 'ollama pull {model}'.") from exc
        raise ChatbotServiceError("The local chatbot service returned an error.") from exc
    except urllib.error.URLError as exc:
        logger.warning("Ollama connection failed: %s", exc)
        raise ChatbotServiceError("Ollama service is not reachable on http://127.0.0.1:11434. Please ensure Ollama is running.") from exc
    except json.JSONDecodeError as exc:
        logger.warning("Ollama returned invalid JSON")
        raise ChatbotServiceError("The local chatbot returned an invalid response.") from exc

    return {
        "response": response_text,
        "language": language,
    }


def _call_ollama(
    message: str,
    language: str,
    conversation: List[Dict[str, str]],
    model: str,
    base_url: str,
) -> str:
    system_prompt = (
        "You are DNAura Health & DNA Assistant. Answer arbitrary user questions "
        "clearly and accurately. Help users understand DNA analysis, mutations, "
        "similarity, classification, disease risk, hospitals, appointments, and "
        "general topics. Keep answers concise unless the user asks for detail. Never provide a medical diagnosis; recommend a qualified "
        "health professional for treatment decisions. "
        f"Respond in the requested language: {language}."
    )
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(
        {
            "role": item["role"],
            "content": item["content"],
        }
        for item in conversation[-10:]
        if item.get("role") in {"user", "assistant"}
        and isinstance(item.get("content"), str)
        and item["content"].strip()
    )
    messages.append({"role": "user", "content": message})

    payload = json.dumps({
        "model": model,
        "messages": messages,
        "stream": False,
        "keep_alive": "24h",
        "options": {
            "num_predict": 300,
            "temperature": 0.3,
        },
    }).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        result = json.loads(response.read().decode("utf-8"))

    response_text = result.get("message", {}).get("content", "").strip()
    if not response_text:
        raise ChatbotServiceError("The local chatbot returned an empty response.")
    return response_text
