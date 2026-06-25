from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.voice import HandoffEventRead, HandoffListResponse
from app.services.handoffs import list_handoffs

router = APIRouter(prefix="/handoffs", tags=["handoffs"])


@router.get("", response_model=HandoffListResponse)
def get_handoffs(
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> HandoffListResponse:
    items, total = list_handoffs(db, limit=limit, offset=offset)
    return HandoffListResponse(
        items=[HandoffEventRead.model_validate(item) for item in items],
        total=total,
    )
