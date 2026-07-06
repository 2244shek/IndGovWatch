"""
e-Gazette (egazette.gov.in) — the central Gazette of India portal has no RSS
feed or API. Its full search form is an ASP.NET postback page (session-based,
not scrape-friendly), but the homepage itself renders a plain HTML table of
"Recent Extra Ordinary Gazettes" — Ministry, Subject, Publish Date, Gazette ID,
Download link — with no login required. This scrapes that table.

Caveat: this is the one source in the pipeline that depends on page markup
rather than a stable feed/API contract. NIC occasionally changes table IDs or
column order on these portals — if this stops returning rows, re-check the
homepage HTML and adjust the header-matching logic below. This fragility (vs.
RSS/API sources) is itself a useful thing to note in interviews: it's why
real pipelines prefer official feeds when they exist and isolate scrapers
behind their own module so one brittle source can't take down the others.
"""
import re
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from app.config import settings

# A believable browser UA matters more here than on the RSS sources — a
# custom string like "IndGovWatch-bot" is exactly what a WAF fingerprints on.
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
}

GAZETTE_ID_PATTERN = re.compile(r"CG-DL-[A-Z]-\d{8}-\d+")


def _find_target_table(soup: BeautifulSoup):
    """Find the table whose header row mentions both 'Ministry' and 'Gazette'."""
    for table in soup.find_all("table"):
        header_text = table.get_text(" ", strip=True).lower()
        if "ministry" in header_text and "gazette id" in header_text:
            return table
    return None


def _parse_table(table) -> list[dict]:
    results = []
    for row in table.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) < 4:
            continue  # skip header/spacer rows

        cell_text = [c.get_text(strip=True) for c in cells]
        ministry, subject, publish_date = cell_text[0], cell_text[1], cell_text[2]
        gazette_id = next((t for t in cell_text if GAZETTE_ID_PATTERN.match(t)), "")
        if not gazette_id:
            continue  # not a real data row

        download_link = row.find("a", href=True)
        results.append({
            "ministry": ministry,
            "subject": subject,
            "publish_date": publish_date,
            "gazette_id": gazette_id,
            "href": download_link["href"] if download_link else None,
        })
    return results


def _parse_fallback_text(soup: BeautifulSoup) -> list[dict]:
    """If the table structure changed and _parse_table finds nothing, fall
    back to scanning raw text for gazette ID patterns near a link — coarser,
    but keeps the source alive until the table-parsing path is fixed."""
    results = []
    for link in soup.find_all("a", href=True):
        parent = link.find_parent()
        context = parent.get_text(" ", strip=True) if parent else ""
        match = GAZETTE_ID_PATTERN.search(context)
        if match:
            results.append({
                "ministry": "Unknown (fallback parse)",
                "subject": context[:200],
                "publish_date": "",
                "gazette_id": match.group(0),
                "href": link["href"],
            })
    return results


def fetch_recent_documents(base_url: str | None = None, max_items: int = 15) -> list[dict]:
    url = base_url or settings.egazette_url
    with httpx.Client(timeout=30, headers=HEADERS, follow_redirects=True) as client:
        resp = client.get(url)
        resp.raise_for_status()  # surfaces 403/blocked responses instead of swallowing them

    soup = BeautifulSoup(resp.text, "lxml")
    table = _find_target_table(soup)

    if table is not None:
        rows = _parse_table(table)
    else:
        print("[ingest] e-Gazette: target table not found — falling back to text scan")
        rows = _parse_fallback_text(soup)

    if not rows:
        raise ValueError(
            "e-Gazette: no gazette entries found via table or fallback parse — "
            "homepage markup has likely changed, check egazette.py"
        )

    results = []
    for row in rows[:max_items]:
        pdf_url = urljoin(url, row["href"]) if row["href"] else url
        results.append({
            "source": "egazette",
            "external_id": row["gazette_id"],
            "title": f"{row['ministry']}: {row['subject']}"[:250],
            "url": pdf_url,
            "published_date": row["publish_date"],
            "raw_text": f"{row['ministry']} — {row['subject']}",
        })
    return results
