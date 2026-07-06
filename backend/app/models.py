import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


def _uid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Regulation(Base):
    """Bronze/silver record: one ingested regulatory document."""
    __tablename__ = "regulations"

    id = Column(String, primary_key=True, default=_uid)
    source = Column(String, nullable=False)          # "federal_register" | "sec_edgar"
    external_id = Column(String, nullable=False, unique=True)
    title = Column(String, nullable=False)
    url = Column(String, nullable=False)
    published_date = Column(String, nullable=True)
    raw_text = Column(Text, nullable=True)
    ingested_at = Column(DateTime, default=_now)

    # Fields filled in by the agent pipeline
    domain = Column(String, nullable=True)           # e.g. "data privacy", "financial"
    urgency = Column(String, nullable=True)           # "low" | "medium" | "high"
    urgency_score = Column(Float, nullable=True)      # 0-1, from triage agent
    summary = Column(Text, nullable=True)
    impact_analysis = Column(Text, nullable=True)
    processed = Column(Boolean, default=False)
    reviewed = Column(Boolean, default=False)         # human-in-the-loop approval flag

    agent_runs = relationship("AgentRun", back_populates="regulation")


class AgentRun(Base):
    """Immutable audit log entry — one row per agent step, for governance/traceability."""
    __tablename__ = "agent_runs"

    id = Column(String, primary_key=True, default=_uid)
    regulation_id = Column(String, ForeignKey("regulations.id"), nullable=False)
    agent_name = Column(String, nullable=False)       # "triage" | "impact_analyst" | "summarizer"
    input_snapshot = Column(Text, nullable=True)
    output_snapshot = Column(Text, nullable=True)
    model_used = Column(String, nullable=True)
    created_at = Column(DateTime, default=_now)

    regulation = relationship("Regulation", back_populates="agent_runs")


class Alert(Base):
    """A finalized, human-approvable alert derived from a high-urgency regulation."""
    __tablename__ = "alerts"

    id = Column(String, primary_key=True, default=_uid)
    regulation_id = Column(String, ForeignKey("regulations.id"), nullable=False)
    message = Column(Text, nullable=False)
    urgency = Column(String, nullable=False)
    created_at = Column(DateTime, default=_now)
    acknowledged = Column(Boolean, default=False)


class IngestionLog(Base):
    """One row per source per ingestion cycle — makes silent failures visible.
    Without this, a source returning 0 items due to a blocked request looks
    identical to a source returning 0 items because there's genuinely nothing
    new. This table distinguishes the two."""
    __tablename__ = "ingestion_logs"

    id = Column(String, primary_key=True, default=_uid)
    source = Column(String, nullable=False)          # "pib" | "rbi" | "sebi" | "egazette"
    status = Column(String, nullable=False)          # "ok" | "error"
    item_count = Column(String, nullable=True)        # items returned (as string for simplicity)
    error_message = Column(Text, nullable=True)
    ran_at = Column(DateTime, default=_now)
