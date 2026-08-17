"""FastAPI application entrypoint.

Run locally with: uvicorn app.main:app --reload --port 8000
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes.auth import router as auth_router
from app.api.routes.compare import router as compare_router
from app.api.routes.modeling import router as modeling_router
from app.api.routes.portfolio import router as portfolio_router
from app.api.routes.screener import router as screener_router
from app.api.routes.stocks import router as stocks_router
from app.api.routes.watchlist import router as watchlist_router
from app.core.config import get_settings
from app.db.base import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("stock_platform")

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    description=(
        "Research and analytics API for the Stock Market Research & Analytics "
        "Platform. Educational and research use only — not investment advice."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(stocks_router)
app.include_router(compare_router)
app.include_router(watchlist_router)
app.include_router(portfolio_router)
app.include_router(screener_router)
app.include_router(modeling_router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Pydantic's error dicts can carry the original exception object in
    # `ctx` (e.g. any custom @field_validator that raises ValueError) —
    # that's not JSON-serializable as-is, so stringify it rather than
    # passing exc.errors() straight through.
    safe_errors = []
    for error in exc.errors():
        error = dict(error)
        ctx = error.get("ctx")
        if isinstance(ctx, dict):
            error["ctx"] = {k: (str(v) if isinstance(v, BaseException) else v) for k, v in ctx.items()}
        safe_errors.append(error)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Invalid request parameters.", "errors": safe_errors},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Never leak stack traces / internals to the client; log server-side instead.
    logger.exception("Unhandled exception on %s %s", request.method, request.url)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred. Please try again."},
    )


@app.get("/health", tags=["meta"])
async def health_check() -> dict:
    return {"status": "ok", "environment": settings.environment}


@app.get("/", tags=["meta"])
async def root() -> dict:
    return {
        "name": settings.app_name,
        "docs": "/docs",
        "disclaimer": (
            "This platform is for educational and research purposes only "
            "and does not provide financial or investment advice."
        ),
    }
