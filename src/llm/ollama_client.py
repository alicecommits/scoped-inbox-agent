"""
Client for the local Ollama server, via its OpenAI-compatible endpoint.

The LLM serving layer is plumbing supporting the project, 
not the mechanism being demonstrated (that's the
OAuth code in src/auth/). Deliberately written against the generic
OpenAI-style chat completions shape rather than anything Ollama-specific,
so swapping backends later (LM Studio on an Apple Silicon, vLLM on a PC)
is a config change, not a rewrite.

Before this works, you need Ollama running with the model pulled:
    ollama pull qwen3:8b
    ollama serve   (usually starts automatically after install)
"""

import requests
from config.settings import settings


def chat(messages: list[dict], temperature: float = 0.0) -> str:
    """
    Send a chat completion request to the local Ollama server.

    Args:
        messages: list of {"role": "system"|"user"|"assistant", "content": str}
        temperature: 0.0 for consistent classification output; raise it
                     only if you want more varied/creative responses,
                     which you generally don't for this use case.

    Returns:
        The assistant's reply text (str).

    Raises:
        requests.HTTPError: if the Ollama server returns a non-2xx response
                             (e.g. server not running, model not pulled).
    """
    response = requests.post(
        f"{settings.OLLAMA_BASE_URL}/chat/completions",
        json={
            "model": settings.OLLAMA_MODEL,
            "messages": messages,
            "temperature": temperature,
        },
        timeout=120,  # local inference on modest hardware can be slow — give it room
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


def health_check() -> bool:
    """
    Quick sanity check that Ollama is up and the configured model exists.
    Useful to call once at startup before processing a whole batch of
    emails, rather than discovering the server is down on message 1 of 50.
    """
    try:
        response = requests.get(f"{settings.OLLAMA_BASE_URL}/models", timeout=5)
        response.raise_for_status()
        model_ids = [m["id"] for m in response.json().get("data", [])]
        return settings.OLLAMA_MODEL in model_ids
    except requests.RequestException:
        return False


if __name__ == "__main__":
    # Quick manual smoke test: `python -m src.llm.ollama_client`
    if not health_check():
        print(f"Ollama isn't reachable, or '{settings.OLLAMA_MODEL}' isn't pulled yet.")
        print(f"Try: ollama pull {settings.OLLAMA_MODEL}")
    else:
        reply = chat([{"role": "user", "content": "Reply with exactly one word: 'ready'."}])
        print(f"Ollama says: {reply.strip()}")
