from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Regulation, AgentRun
from app.schemas import RegulationOut, AgentRunOut

router = APIRouter(prefix="/regulations", tags=["regulations"])


@router.get("", response_model=list[RegulationOut])
def list_regulations(
    domain: str | None = None,
    urgency: str | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(Regulation).filter(Regulation.processed == True)  # noqa: E712
    if domain:
        q = q.filter(Regulation.domain == domain)
    if urgency:
        q = q.filter(Regulation.urgency == urgency)
    return q.order_by(Regulation.ingested_at.desc()).limit(100).all()


@router.get("/{reg_id}", response_model=RegulationOut)
def get_regulation(reg_id: str, db: Session = Depends(get_db)):
    reg = db.query(Regulation).filter_by(id=reg_id).first()
    if not reg:
        raise HTTPException(status_code=404, detail="Not found")
    return reg


@router.get("/{reg_id}/audit", response_model=list[AgentRunOut])
def get_audit_trail(reg_id: str, db: Session = Depends(get_db)):
    return db.query(AgentRun).filter_by(regulation_id=reg_id).order_by(AgentRun.created_at).all()


@router.post("/{reg_id}/review")
def mark_reviewed(reg_id: str, db: Session = Depends(get_db)):
    reg = db.query(Regulation).filter_by(id=reg_id).first()
    if not reg:
        raise HTTPException(status_code=404, detail="Not found")
    reg.reviewed = True
    db.add(reg)
    db.commit()
    return {"ok": True}
