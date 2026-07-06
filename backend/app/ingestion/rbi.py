"""
Reserve Bank of India (RBI) — free public RSS feeds, no API key, no auth.
Feed list: https://rbi.org.in/Scripts/rss.aspx

Notifications feed = binding regulatory instructions (the most compliance-critical).
Press Releases feed = broader announcements, data releases, speeches context.

Fetched via httpx + browser-like headers, then handed to feedparser as bytes —
see the comment in pib.py for why this matters (default feedparser UA gets
silently rejected by several NIC-hosted sites).
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
    url = feed_url or settings.rbi_notifications_rss_url

    with httpx.Client(timeout=20, headers=HEADERS, follow_redirects=True) as client:
        resp = client.get(url)
        resp.raise_for_status()

    parsed = parse_feed(resp.content, source_label="RBI")

    results = []
    for entry in parsed.entries[:max_items]:
        external_id = entry.get("id") or entry.get("link")
        results.append({
            "source": "rbi",
            "external_id": external_id,
            "title": entry.get("title", "").strip(),
            "url": entry.get("link", ""),
            "published_date": entry.get("published", ""),
            "raw_text": entry.get("summary", "") or entry.get("title", ""),
        })
    return results
