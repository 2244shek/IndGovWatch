"""
Ties the data-engineering layer (ingestion + storage) to the agentic layer
(LangGraph pipeline) and writes the audit trail. This is what the scheduler
calls on each tick, and what the manual /ingest/run endpoint calls too.
"""
from sqlalchemy.orm import Session
from app.models import Regulation, AgentRun, Alert, IngestionLog
from app.vectorstore import upsert_document
from app.agents.graph import run_pipeline
from app.ingestion import pib, rbi, sebi, egazette
from app.config import settings


async def ingest_new_documents(db: Session) -> int:
    """Pull from PIB, RBI, SEBI RSS feeds and the e-Gazette scraper, store any
    documents not already seen. Returns count of new documents. Each source
    returns its full current list on every fetch, so de-duplication against
    external_id is what makes this safe to call on every scheduler tick
    without creating duplicates.

    Each source's outcome (ok / error, item count, error detail) is written to
    IngestionLog — this is what makes a blocked/rejected request distinguishable
    from a source that genuinely has nothing new, instead of both looking like
    silent zeros in the feed."""
    new_count = 0

    named_fetchers = [
        ("pib", lambda: pib.fetch_recent_documents(settings.pib_rss_url)),
        ("rbi_notifications", lambda: rbi.fetch_recent_documents(settings.rbi_notifications_rss_url)),
        ("rbi_press", lambda: rbi.fetch_recent_documents(settings.rbi_press_rss_url)),
        ("sebi", lambda: sebi.fetch_recent_documents(settings.sebi_rss_url)),
        ("egazette", lambda: egazette.fetch_recent_documents(settings.egazette_url)),
    ]

    for source_name, fetch in named_fetchers:
        try:
            docs = fetch()
            db.add(IngestionLog(source=source_name, status="ok", item_count=str(len(docs))))
        except Exception as e:
            docs = []
            print(f"[ingest] {source_name} fetch failed: {e}")
            db.add(IngestionLog(source=source_name, status="error", error_message=str(e)[:2000]))
        db.commit()

        for doc in docs:
            if not doc.get("external_id"):
                continue
            exists = db.query(Regulation).filter_by(external_id=doc["external_id"]).first()
            if exists:
                continue
            reg = Regulation(**doc)
            db.add(reg)
            db.commit()
            db.refresh(reg)
            new_count += 1

    return new_count


def process_unprocessed(db: Session, limit: int = 10) -> int:
    """Run the agent pipeline on any regulation that hasn't been processed yet."""
    pending = db.query(Regulation).filter_by(processed=False).limit(limit).all()
    processed_count = 0

    for reg in pending:
        result = run_pipeline(
            title=reg.title,
            raw_text=reg.raw_text or "",
            source=reg.source,
            url=reg.url,
        )

        reg.domain = result["domain"]
        reg.urgency = result["urgency"]
        reg.urgency_score = result["urgency_score"]
        reg.impact_analysis = result["impact_analysis"]
        reg.summary = result["summary"]
        reg.processed = True
        db.add(reg)

        # Audit log — one immutable row per agent step
        for step in result["trace"]:
            db.add(AgentRun(
                regulation_id=reg.id,
                agent_name=step["agent"],
                input_snapshot=step["input"][:4000],
                output_snapshot=step["output"][:4000],
                model_used=settings.groq_model if settings.llm_provider == "groq" else settings.ollama_model,
            ))

        # Embed for future RAG context
        upsert_document(
            doc_id=reg.id,
            text=f"{reg.title}\n{reg.raw_text}",
            metadata={"source": reg.source, "domain": reg.domain or "other"},
        )

        # Auto-create an alert for medium/high urgency items (human still must acknowledge)
        if reg.urgency in ("medium", "high"):
            db.add(Alert(
                regulation_id=reg.id,
                message=reg.summary or reg.title,
                urgency=reg.urgency,
            ))

        db.commit()
        processed_count += 1

    return processed_count
