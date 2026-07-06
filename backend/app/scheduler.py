"""
APScheduler runs the ingest+process cycle on a timer inside the FastAPI process —
zero extra infrastructure. For a production version, swap this for an Airflow DAG
(see README) without touching pipeline.py at all.
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.database import SessionLocal
from app.pipeline import ingest_new_documents, process_unprocessed
from app.config import settings

scheduler = AsyncIOScheduler()


async def scheduled_cycle():
    db = SessionLocal()
    try:
        new_docs = await ingest_new_documents(db)
        processed = process_unprocessed(db)
        print(f"[scheduler] ingested {new_docs} new docs, processed {processed}")
    finally:
        db.close()


def start_scheduler():
    scheduler.add_job(
        scheduled_cycle,
        "interval",
        minutes=settings.ingestion_interval_minutes,
        id="regwatch_cycle",
        replace_existing=True,
    )
    scheduler.start()
