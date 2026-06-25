import hashlib
import hmac
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.api.deps import get_app_settings, get_db, get_meta_lead_client
from app.core.config import Settings
from app.schemas.meta import MetaWebhookEvent, MetaWebhookResponse
from app.services.calls import dispatch_call_attempt_in_background
from app.services.leads import ingest_meta_lead_event
from app.services.meta import MetaLeadClient
from app.services.providers import apply_exotel_status_callback
from app.services.queue import enqueue_call_dispatch

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.get("/meta/leadgen", response_class=PlainTextResponse)
def verify_meta_webhook(
    mode: str = Query(alias="hub.mode"),
    verify_token: str = Query(alias="hub.verify_token"),
    challenge: str = Query(alias="hub.challenge"),
    settings: Settings = Depends(get_app_settings),
) -> str:
    if mode != "subscribe" or verify_token != settings.meta_verify_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Verification failed")
    return challenge


@router.post("/meta/leadgen", response_model=MetaWebhookResponse)
async def receive_meta_webhook(
    request: Request,
    payload: MetaWebhookEvent,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
    meta_client: MetaLeadClient = Depends(get_meta_lead_client),
) -> MetaWebhookResponse:
    await _verify_meta_signature(request, settings)

    created = 0
    duplicates = 0
    call_attempt_ids: list[int] = []

    for entry in payload.entry:
        for change in entry.changes:
            if change.field != "leadgen" or not change.value.leadgen_id:
                continue

            result = await ingest_meta_lead_event(
                db=db,
                change_value=change.value,
                meta_client=meta_client,
                default_language=settings.default_language,
                raw_event=payload.model_dump(mode="json"),
            )
            if result.created:
                created += 1
                if result.call_attempt_id is not None:
                    call_attempt_ids.append(result.call_attempt_id)
                    if settings.auto_dispatch_calls:
                        # Prefer the durable Redis (RQ) queue; fall back to an in-process
                        # background task when Redis is not configured (local/dev).
                        if not enqueue_call_dispatch(result.call_attempt_id):
                            background_tasks.add_task(
                                dispatch_call_attempt_in_background,
                                result.call_attempt_id,
                            )
            else:
                duplicates += 1

    return MetaWebhookResponse(
        received=sum(len(entry.changes) for entry in payload.entry),
        created=created,
        duplicates=duplicates,
        scheduled_call_attempt_ids=call_attempt_ids,
    )


@router.post("/exotel/status")
async def receive_exotel_status_callback(
    request: Request,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        payload = await request.json()
    else:
        form = await request.form()
        payload = dict(form)

    attempt = apply_exotel_status_callback(db=db, payload=payload)
    return {
        "updated": attempt is not None,
        "attempt_id": attempt.id if attempt else None,
    }


async def _verify_meta_signature(request: Request, settings: Settings) -> None:
    if not settings.meta_app_secret:
        return

    signature_header = request.headers.get("x-hub-signature-256")
    if not signature_header or not signature_header.startswith("sha256="):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing Meta webhook signature",
        )

    raw_body = await request.body()
    expected_signature = hmac.new(
        settings.meta_app_secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()
    received_signature = signature_header.removeprefix("sha256=")

    if not hmac.compare_digest(received_signature, expected_signature):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Meta webhook signature",
        )
