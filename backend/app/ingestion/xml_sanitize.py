"""
Shared helper for parsing RSS feeds that are, in practice, not always
well-formed XML. PIB (and occasionally RBI/SEBI) publish feeds with:

  1. Unescaped ampersands in titles — "Research & Development" instead of
     "Research &amp; Development" — the single most common cause of
     "not well-formed (invalid token)" errors from strict XML parsers.
  2. Stray control characters that aren't valid in XML 1.0 at all (some CMS
     exports carry these through from Word/Excel source documents).

feedparser's strict parser aborts entirely on these rather than skipping the
bad part, so bozo=True + zero entries. Fix the two most common defects first,
then hand the cleaned text to feedparser — this recovers the feed in the
large majority of cases without needing a different library.
"""
import re
import feedparser

# XML 1.0 valid character ranges — strip anything outside these (control
# chars 0x00-0x08, 0x0B-0x0C, 0x0E-0x1F, plus a few high-range invalids)
_INVALID_XML_CHARS = re.compile(
    "[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x84\x86-\x9f\ufdd0-\ufdef\ufffe\uffff]"
)

# Match a bare "&" that isn't already the start of a valid entity
# (&amp; &lt; &gt; &quot; &apos; &#123; &#x1F;) and escape it.
_BARE_AMPERSAND = re.compile(r"&(?!amp;|lt;|gt;|quot;|apos;|#\d+;|#x[0-9a-fA-F]+;)")


def _sanitize(raw: bytes) -> str:
    text = raw.decode("utf-8", errors="replace")
    text = _INVALID_XML_CHARS.sub("", text)
    text = _BARE_AMPERSAND.sub("&amp;", text)
    return text


def parse_feed(raw_content: bytes, source_label: str):
    """Try parsing as-is first (cheapest path); if that fails to yield any
    entries, retry against the sanitized text before giving up."""
    parsed = feedparser.parse(raw_content)
    if parsed.entries:
        return parsed

    cleaned = _sanitize(raw_content)
    parsed = feedparser.parse(cleaned)
    if parsed.entries:
        return parsed

    # Still nothing — raise with whatever detail feedparser captured, so this
    # surfaces as a real IngestionLog error instead of a quiet empty list.
    raise ValueError(
        f"{source_label} feed did not yield any entries even after sanitizing "
        f"XML (bozo_exception={getattr(parsed, 'bozo_exception', 'unknown')})"
    )
