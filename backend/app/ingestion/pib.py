"""
Press Information Bureau (PIB) — Government of India's official press release
agency. Free public RSS feeds, no API key, no auth. Docs/feed list:
https://pib.gov.in/ViewRss.aspx

Ministry-specific feeds exist too (each ministry has its own `reg=` param);
this uses the "all releases" English feed by default.

Note: we fetch with httpx + a browser-like User-Agent rather than letting
feedparser hit the URL directly. feedparser's default urllib UA gets silently
rejected or empty-bodied by several NIC-hosted sites — it doesn't raise, it
just returns zero entries, which looks identical to "no new items" unless you
fetch the raw response yourself and check the status code.
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
    url = feed_url or settings.pib_rss_url

    with httpx.Client(timeout=20, headers=HEADERS, follow_redirects=True) as client:
        resp = client.get(url)
        resp.raise_for_status()  # surfaces 403/timeout instead of swallowing it

    parsed = parse_feed(resp.content, source_label="PIB")

    results = []
    for entry in parsed.entries[:max_items]:
        # PIB RSS guids are stable per release — use as external_id
        external_id = entry.get("id") or entry.get("link")
        results.append({
            "source": "pib",
            "external_id": external_id,
            "title": entry.get("title", "").strip(),
            "url": entry.get("link", ""),
            "published_date": entry.get("published", ""),
            "raw_text": entry.get("summary", "") or entry.get("title", ""),
        })
    return results
