from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import IngestionLog
from app.pipeline import ingest_new_documents, process_unprocessed
from app.schemas import IngestResult, IngestionLogOut

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("/run", response_model=IngestResult)
async def run_ingest_now(db: Session = Depends(get_db)):
    """Manually trigger one ingestion + agent-processing cycle (also runs on a schedule)."""
    new_docs = await ingest_new_documents(db)
    processed = process_unprocessed(db)
    return IngestResult(new_documents=new_docs, processed_documents=processed)


@router.get("/status", response_model=list[IngestionLogOut])
def ingestion_status(db: Session = Depends(get_db)):
    """Latest log row per source — lets the dashboard show which sources are
    healthy vs. silently failing, instead of that only being visible in
    server console output."""
    sources = ["pib", "rbi_notifications", "rbi_press", "sebi", "egazette"]
    latest = []
    for source in sources:
        row = (
            db.query(IngestionLog)
            .filter_by(source=source)
            .order_by(IngestionLog.ran_at.desc())
            .first()
        )
        if row:
            latest.append(row)
    return latest
