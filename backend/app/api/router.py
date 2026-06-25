from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.api.routes import (
    agents,
    analytics,
    auth,
    call_attempts,
    enquiries,
    handoffs,
    health,
    integrations,
    leads,
    metrics,
    telephony_stream,
    voice_sessions,
    voice_stream,
    webhooks,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(metrics.router)
api_router.include_router(auth.router)
api_router.include_router(
    integrations.router,
    dependencies=[Depends(get_current_user)],
)
api_router.include_router(analytics.router, dependencies=[Depends(get_current_user)])
api_router.include_router(agents.router, dependencies=[Depends(get_current_user)])
api_router.include_router(leads.router, dependencies=[Depends(get_current_user)])
api_router.include_router(call_attempts.router, dependencies=[Depends(get_current_user)])
api_router.include_router(voice_sessions.router, dependencies=[Depends(get_current_user)])
# voice_stream is a WebSocket route; it authenticates via a token query param internally.
api_router.include_router(voice_stream.router)
# telephony_stream is the public Exotel media WebSocket; guarded by a shared secret token.
api_router.include_router(telephony_stream.router)
api_router.include_router(handoffs.router, dependencies=[Depends(get_current_user)])
api_router.include_router(webhooks.router)
# enquiries is the public self-serve enquiry-link endpoint (no operator auth).
api_router.include_router(enquiries.router)
