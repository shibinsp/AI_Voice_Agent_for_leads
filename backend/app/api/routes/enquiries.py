from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_app_settings, get_db
from app.core.config import Settings
from app.schemas.enquiry import EnquiryCreate, EnquiryStartResponse
from app.services.enquiries import create_enquiry

router = APIRouter(prefix="/enquiries", tags=["enquiries"])


@router.post("", response_model=EnquiryStartResponse, status_code=201)
def submit_enquiry(
    payload: EnquiryCreate,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> EnquiryStartResponse:
    """Public endpoint behind the shareable enquiry link. Creates the lead and starts a web
    voice session, returning a session-scoped token the browser uses to drive the call."""
    result = create_enquiry(db, payload=payload, settings=settings)
    return EnquiryStartResponse(
        lead_id=result.lead_id,
        session_id=result.session_id,
        token=result.token,
        language=result.language,
        opening_line=result.opening_line,
    )
