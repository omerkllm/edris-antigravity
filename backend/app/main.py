from __future__ import annotations

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.middleware import RateLimitMiddleware
from app.api.routes import router as api_router


def _parse_allowed_origins(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


@asynccontextmanager
async def lifespan(_: FastAPI):
    load_dotenv()
    yield


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan, title="AI Opportunity Inbox Copilot")

    allowed_origins = _parse_allowed_origins(os.getenv("ALLOWED_ORIGINS"))
    if allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.add_middleware(RateLimitMiddleware, max_requests=10, window_seconds=60)
    app.include_router(api_router)

    @app.exception_handler(Exception)
    async def _unhandled_exception_handler(_: Request, __: Exception):
        return JSONResponse(status_code=500, content={"detail": "Internal processing error"})

    return app


app = create_app()

