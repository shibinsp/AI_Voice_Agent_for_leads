from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.entities import Lead
from app.schemas.lead import LeadListResponse, LeadRead

router = APIRouter(prefix="/leads", tags=["leads"])


@router.get("", response_model=LeadListResponse)
def list_leads(
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> LeadListResponse:
    items = db.scalars(
        select(Lead).order_by(Lead.created_at.desc()).offset(offset).limit(limit)
    ).all()
    total = db.scalar(select(func.count()).select_from(Lead)) or 0
    return LeadListResponse(
        items=[LeadRead.model_validate(item) for item in items],
        total=total,
    )


@router.get("/{lead_id}", response_model=LeadRead)
def get_lead(lead_id: int, db: Session = Depends(get_db)) -> LeadRead:
    lead = db.get(Lead, lead_id)
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")
    return LeadRead.model_validate(lead)
