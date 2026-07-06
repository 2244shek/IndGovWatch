"""
SEBI (Securities and Exchange Board of India) — free public RSS feed, no API
key, no auth. Feed covers press releases, circulars, and orders/rulings.
Source: https://www.sebi.gov.in/rss.html

Fetched via httpx + browser-like headers, then handed to feedparser as bytes —
see the comment in pib.py for why this matters.
"""
import httpx
from app.config import settings
from app.ingestion.xml_sanitize import parse_feed

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}


def fetch_recent_documents(feed_url: str | None = None, max_items: int = 15) -> list[dict]:
    url = feed_url or settings.sebi_rss_url

    with httpx.Client(timeout=20, headers=HEADERS, follow_redirects=True) as client:
        resp = client.get(url)
        resp.raise_for_status()

    parsed = parse_feed(resp.content, source_label="SEBI")

    results = []
    for entry in parsed.entries[:max_items]:
        external_id = entry.get("id") or entry.get("link")
        results.append({
            "source": "sebi",
            "external_id": external_id,
            "title": entry.get("title", "").strip(),
            "url": entry.get("link", ""),
            "published_date": entry.get("published", ""),
            "raw_text": entry.get("summary", "") or entry.get("title", ""),
        })
    return results
