from datetime import datetime
from pydantic import BaseModel


class RegulationOut(BaseModel):
    id: str
    source: str
    title: str
    url: str
    published_date: str | None
    domain: str | None
    urgency: str | None
    urgency_score: float | None
    summary: str | None
    impact_analysis: str | None
    easy_view_headline: str | None
    easy_view_explanation: str | None
    processed: bool
    reviewed: bool
    ingested_at: datetime

    class Config:
        from_attributes = True


class AgentRunOut(BaseModel):
    id: str
    agent_name: str
    input_snapshot: str | None
    output_snapshot: str | None
    model_used: str | None
    created_at: datetime

    model_config = {
        "from_attributes": True,
        "protected_namespaces": (),
    }


class AlertOut(BaseModel):
    id: str
    regulation_id: str
    message: str
    urgency: str
    acknowledged: bool
    created_at: datetime

    class Config:
        from_attributes = True


class IngestResult(BaseModel):
    new_documents: int
    processed_documents: int


class IngestionLogOut(BaseModel):
    id: str
    source: str
    status: str
    item_count: str | None
    error_message: str | None
    ran_at: datetime

    class Config:
        from_attributes = True
