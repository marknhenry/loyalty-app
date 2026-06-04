"""Consistent JSON error responses (TE.2 / Story O.1)."""

import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("loyalty_app")


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, dict):
        error = detail
    else:
        error = {"code": "HTTP_ERROR", "message": str(detail)}

    return JSONResponse(
        status_code=exc.status_code,
        content={"error": error, "request_id": _request_id(request)},
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors = exc.errors()
    first = errors[0] if errors else {}
    field = ".".join(str(loc) for loc in first.get("loc", [])[1:]) or None
    message = first.get("msg", "Validation error")

    logger.warning(
        "Validation error on %s: %s",
        request.url.path,
        errors,
        extra={"request_id": _request_id(request)},
    )

    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": message,
                "field": field,
            },
            "request_id": _request_id(request),
        },
    )


async def unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    logger.exception(
        "Unhandled error on %s",
        request.url.path,
        extra={"request_id": _request_id(request)},
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
            },
            "request_id": _request_id(request),
        },
    )
