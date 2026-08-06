"""The AppError hierarchy and the single exception handler that renders it.

Every error the API can return to a client is one of the AppError subclasses
below, rendered through the one envelope shape in schemas/common.py:

    { "error": { "code": ..., "message": ..., "detail": ... } }

Does NOT let any other exception type reach the client as-is — the handler
registered in main.py catches unhandled exceptions too and maps them to a
generic 500 envelope so a traceback never reaches a caller.
"""
from __future__ import annotations

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.schemas.common import ErrorBody, ErrorEnvelope


class AppError(Exception):
    """Base class for all deliberately-raised API errors.

    Subclasses fix `code` and `status_code`; `message` and `detail` are
    supplied at raise time.
    """

    code: str = "INTERNAL_ERROR"
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, message: str, detail: str | None = None) -> None:
        self.message = message
        self.detail = detail
        super().__init__(message)


class ValidationAppError(AppError):
    code = "VALIDATION_ERROR"
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY


class ModelNotReadyError(AppError):
    code = "MODEL_NOT_READY"
    status_code = status.HTTP_409_CONFLICT


class JobNotFoundError(AppError):
    code = "JOB_NOT_FOUND"
    status_code = status.HTTP_404_NOT_FOUND


class EmptyDatasetError(AppError):
    code = "EMPTY_DATASET"
    status_code = status.HTTP_400_BAD_REQUEST


class BadCsvError(AppError):
    code = "BAD_CSV"
    status_code = status.HTTP_400_BAD_REQUEST


def _envelope(code: str, message: str, detail: str | None = None) -> dict:
    return ErrorEnvelope(error=ErrorBody(code=code, message=message, detail=detail)).model_dump()


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=_envelope(exc.code, exc.message, exc.detail))


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=_envelope("VALIDATION_ERROR", "Request failed validation.", str(exc.errors())),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_envelope("INTERNAL_ERROR", "An unexpected error occurred.", None),
    )
