from __future__ import annotations

import time

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.services.analytics import build_analytics_summary

router = APIRouter(tags=["metrics"])

_START = time.monotonic()


@router.get("/metrics")
def metrics(db: Session = Depends(get_db)) -> dict:
    """Lightweight operational metrics for monitoring/scraping (no auth, counts only)."""
    summary = build_analytics_summary(db)
    return {
        "uptime_seconds": round(time.monotonic() - _START, 1),
        "enquiries_total": summary["enquiries"]["total"],
        "calls_by_status": summary["calls"]["by_status"],
        "sessions_completed": summary["sessions"]["completed"],
        "handoffs_sent": summary["handoffs"]["sent"],
        "genuine_rate": summary["qualification"]["genuine_rate"],
    }
