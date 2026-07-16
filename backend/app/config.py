"""
Central configuration. Every default here is free:
- SQLite for the database (zero setup, zero cost)
- Chroma embedded vector store (runs in-process, zero cost)
- Groq as the default LLM provider: https://console.groq.com — free API key,
  generous free-tier rate limits, no credit card required.
- Or set LLM_PROVIDER=ollama to use a fully local model (e.g. `ollama pull llama3.1`)
  with zero API calls and zero cost at all.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- Database ---
    database_url: str = "sqlite:///./indgovwatch.db"

    # --- Vector store ---
    chroma_persist_dir: str = "./chroma_data_india"

    # --- LLM provider: "groq", "ollama", or "nvidia" ---
    llm_provider: str = "groq"
    groq_api_key: str = ""            # get free at console.groq.com
    groq_model: str = "llama-3.1-8b-instant"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"

    nvidia_api_key: str = ""
    nvidia_model: str = "deepseek-ai/deepseek-v4-pro"

    # --- Ingestion sources (public, free, no key required) ---
    pib_rss_url: str = "https://www.pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=1&reg=1"          # PIB, all releases, English
    rbi_notifications_rss_url: str = "https://www.rbi.org.in/notifications_rss.xml"  # RBI, binding notifications
    rbi_press_rss_url: str = "https://www.rbi.org.in/pressreleases_rss.xml"          # RBI, press releases
    sebi_rss_url: str = "https://www.sebi.gov.in/sebirss.xml"                        # SEBI, press releases/circulars/orders
    egazette_url: str = "https://egazette.gov.in/"                                   # scraped, see ingestion/egazette.py
    ingestion_interval_minutes: int = 360   # every 6 hours

    # --- CORS ---
    frontend_origin: str = "http://localhost:5173"

    class Config:
        env_file = ".env"


settings = Settings()
