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
    import time
    import re
    from groq import Groq, RateLimitError
    client = Groq(api_key=settings.groq_api_key)
    
    max_retries = 5
    base_delay = 4.0
    
    for attempt in range(max_retries):
        try:
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
        except RateLimitError as e:
            if attempt == max_retries - 1:
                raise e
            delay = base_delay * (2 ** attempt)
            err_msg = str(e)
            match = re.search(r"try again in ([\d\.]+)s", err_msg)
            if match:
                delay = float(match.group(1)) + 1.5
            print(f"[groq] Rate limit hit. Retrying in {delay:.2f} seconds... (Attempt {attempt + 1}/{max_retries})")
            time.sleep(delay)


def _call_ollama(prompt: str, system: str) -> str:
    payload = {
        "model": settings.ollama_model,
        "prompt": f"{system}\n\n{prompt}",
        "stream": False,
    }
    resp = httpx.post(f"{settings.ollama_base_url}/api/generate", json=payload, timeout=120)
    resp.raise_for_status()
    return resp.json().get("response", "")


def _call_nvidia(prompt: str, system: str) -> str:
    headers = {
        "Authorization": f"Bearer {settings.nvidia_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.nvidia_model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ],
        "temperature": 1.0,
        "top_p": 0.95,
        "max_tokens": 16384,
        "chat_template_kwargs": {"thinking": False},
        "stream": False
    }
    
    import time
    max_retries = 5
    base_delay = 2.0
    
    for attempt in range(max_retries):
        try:
            resp = httpx.post(
                "https://integrate.api.nvidia.com/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=60.0
            )
            if resp.status_code == 429:
                delay = base_delay * (2 ** attempt)
                print(f"[nvidia] Rate limit 429 hit. Retrying in {delay} seconds...")
                time.sleep(delay)
                continue
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            delay = base_delay * (2 ** attempt)
            print(f"[nvidia] API call failed, retrying in {delay}s... Error: {e}")
            time.sleep(delay)


CITIZEN_IMPACT_SYSTEM_PROMPT = (
    "You are a public-interest translator. Translate bureaucratic Indian legal and regulatory notifications "
    "into plain English for the everyday citizen.\n"
    "Strictly replace all bureaucratic terms (e.g. Gazette ID, Notification numbers, sub-sections, legal references) "
    "with plain English. You must address and answer the following questions clearly:\n"
    "- Who wins? (Which groups/individuals benefit, and why?)\n"
    "- Who loses? (Which groups/individuals are adversely affected or face new restrictions?)\n"
    "- What changes for an ordinary citizen tomorrow morning?\n"
    "Focus on concrete, real-world impacts. Keep your response brief, clear, and highly scannable."
)

LAYMAN_EXPLAINER_SYSTEM_PROMPT = (
    "You are a master communicator who explains complex government policies to laymen.\n"
    "Your job is to read the document and generate a single, highly engaging, clean, jargon-free headline (1 sentence) "
    "in plain English.\n"
    "Strictly avoid bureaucratic terminology, notification numbers, dates, gazette IDs, or legal jargon. "
    "Focus purely on what the policy is about in simple terms that anyone can understand instantly."
)


def call_llm(prompt: str, system: str = "You are a precise regulatory analyst assistant.") -> str:
    if settings.llm_provider == "ollama":
        return _call_ollama(prompt, system)
    elif settings.llm_provider == "nvidia":
        return _call_nvidia(prompt, system)
    return _call_groq(prompt, system)
