"""
Single LLM entrypoint so the agent graph doesn't care which free backend is used.

Option A — Groq (default): free API key at https://console.groq.com, generous
free-tier limits, no credit card. Very fast inference on open models like Llama 3.1.

Option B — Ollama: 100% local, 100% free, no internet needed after the model is
pulled (`ollama pull llama3.1`). Set LLM_PROVIDER=ollama in .env to use this.
"""
import httpx
from app.config import settings


def _call_groq(prompt: str, system: str) -> str:
    from groq import Groq
    client = Groq(api_key=settings.groq_api_key)
    resp = client.chat.completions.create(
        model=settings.groq_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=800,
    )
    return resp.choices[0].message.content


def _call_ollama(prompt: str, system: str) -> str:
    payload = {
        "model": settings.ollama_model,
        "prompt": f"{system}\n\n{prompt}",
        "stream": False,
    }
    resp = httpx.post(f"{settings.ollama_base_url}/api/generate", json=payload, timeout=120)
    resp.raise_for_status()
    return resp.json().get("response", "")


def call_llm(prompt: str, system: str = "You are a precise regulatory analyst assistant.") -> str:
    if settings.llm_provider == "ollama":
        return _call_ollama(prompt, system)
    return _call_groq(prompt, system)
