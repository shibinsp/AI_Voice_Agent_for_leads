import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging, request_id_var
from app.db.session import init_db

settings = get_settings()
configure_logging()
logger = logging.getLogger("app.request")


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    logging.getLogger("app").info("startup complete: %s", settings.environment)
    yield


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    rid = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
    token = request_id_var.set(rid)
    start = time.perf_counter()
    try:
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = rid
        logger.info(
            "%s %s -> %s %.0fms",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response
    finally:
        request_id_var.reset(token)


app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "app": settings.app_name,
        "docs": "/docs",
        "api_prefix": settings.api_v1_prefix,
    }
