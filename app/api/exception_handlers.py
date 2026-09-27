from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse

from app.api.schemas.errors import ErrorBody, ErrorDetail, ErrorResponse
from app.services.errors import (
    ApplicationError,
    Conflict,
    DependencyUnavailable,
    InvalidAssignment,
    InvalidInput,
    NotFound,
    PermissionDenied,
    RateLimited,
    Unauthenticated,
)

STATUS_CODES: dict[type[ApplicationError], int] = {
    NotFound: 404,
    PermissionDenied: 403,
    Conflict: 409,
    InvalidInput: 422,
    InvalidAssignment: 422,
    Unauthenticated: 401,
    DependencyUnavailable: 503,
    RateLimited: 429,
}


def error_response(request: Request, status: int, body: ErrorBody) -> JSONResponse:
    request_id = getattr(request.state, "request_id", str(uuid4()))
    payload = ErrorResponse(error=body, request_id=request_id)
    headers = {"X-Request-ID": request_id}
    if status == 401:
        headers["WWW-Authenticate"] = "Bearer"
    return JSONResponse(payload.model_dump(mode="json"), status, headers=headers)


async def application_error_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, ApplicationError)
    status = next(
        (status for error, status in STATUS_CODES.items() if isinstance(exc, error)),
        500,
    )
    response = error_response(
        request, status, ErrorBody(code=exc.code, message=exc.message)
    )
    if isinstance(exc, RateLimited):
        response.headers["Retry-After"] = str(exc.retry_after)
    return response


async def validation_error_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    # Never return raw input, validation context or user-provided error messages.
    details = [
        ErrorDetail(location=list(error["loc"]), code=error["type"])
        for error in exc.errors()
    ]
    return error_response(
        request,
        422,
        ErrorBody(code="validation_error", message="Invalid input.", details=details),
    )


async def http_error_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, HTTPException)
    code = "not_found" if exc.status_code == 404 else "http_error"
    return error_response(
        request, exc.status_code, ErrorBody(code=code, message="Request failed.")
    )


async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
    return error_response(
        request,
        500,
        ErrorBody(code="internal_error", message="An unexpected error occurred."),
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ApplicationError, application_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(HTTPException, http_error_handler)
    app.add_exception_handler(Exception, unexpected_error_handler)
