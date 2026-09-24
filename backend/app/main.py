import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.errors import generic_exception_handler, http_exception_handler, validation_exception_handler
from app.core.logging import configure_logging

configure_logging()
settings = get_settings()
logger = logging.getLogger("nirman_ai")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger.info("Request %s %s", request.method, request.url.path)
        response = await call_next(request)
        logger.info("Response %s %s %s", request.method, request.url.path, response.status_code)
        return response


from starlette.exceptions import HTTPException as StarletteHTTPException

app = FastAPI(
    title="NIRMAN AI API",
    version="0.1.0",
    description="Phase 1 foundation API for infrastructure monitoring intelligence",
    docs_url="/docs",
    redoc_url="/redoc",
)

allowed_origins = list(set(settings.cors_allowlist + [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "https://nirman-assist.vercel.app",
]))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestLoggingMiddleware)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)
app.include_router(api_router, prefix=settings.api_prefix)
