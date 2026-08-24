"""Domain exceptions and global FastAPI exception handlers."""
from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


# ── Domain exception base ─────────────────────────────────────────────────────

class AppError(Exception):
    """Base class for all application-level errors."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    error_code: str = "APP_ERROR"

    def __init__(self, message: str, error_code: str | None = None) -> None:
        self.message = message
        if error_code:
            self.error_code = error_code
        super().__init__(message)


# ── Specific domain errors ────────────────────────────────────────────────────

class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "NOT_FOUND"


class AuthError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = "UNAUTHORIZED"


class ForbiddenError(AppError):
    status_code = status.HTTP_403_FORBIDDEN
    error_code = "FORBIDDEN"


class ConflictError(AppError):
    status_code = status.HTTP_409_CONFLICT
    error_code = "CONFLICT"


class ValidationError(AppError):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    error_code = "VALIDATION_ERROR"


class BusinessError(AppError):
    status_code = status.HTTP_400_BAD_REQUEST
    error_code = "BUSINESS_ERROR"


# ── Specific named errors ─────────────────────────────────────────────────────

class ZoneNotFoundError(NotFoundError):
    error_code = "ZONE_NOT_FOUND"


class AreaNotFoundError(NotFoundError):
    error_code = "AREA_NOT_FOUND"


class OrderNotFoundError(NotFoundError):
    error_code = "ORDER_NOT_FOUND"


class AgentNotFoundError(NotFoundError):
    error_code = "AGENT_NOT_FOUND"


class UserNotFoundError(NotFoundError):
    error_code = "USER_NOT_FOUND"


class RateNotConfiguredError(BusinessError):
    error_code = "RATE_NOT_CONFIGURED"


class InvalidCODConfigError(BusinessError):
    error_code = "INVALID_COD_CONFIGURATION"


class InvalidStatusTransitionError(BusinessError):
    error_code = "INVALID_STATUS_TRANSITION"


class AgentNotAvailableError(BusinessError):
    error_code = "AGENT_NOT_AVAILABLE"


class NoAvailableAgentError(BusinessError):
    error_code = "NO_AVAILABLE_AGENT"


class OrderAlreadyDeliveredError(BusinessError):
    error_code = "ORDER_ALREADY_DELIVERED"


class OrderNotEligibleForRescheduleError(BusinessError):
    error_code = "ORDER_NOT_ELIGIBLE_FOR_RESCHEDULE"


class OverlappingRateCardError(ConflictError):
    error_code = "OVERLAPPING_RATE_CARD"


class DuplicateEmailError(ConflictError):
    error_code = "DUPLICATE_EMAIL"


# ── Exception handlers ────────────────────────────────────────────────────────

def _error_response(status_code: int, error_code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"detail": message, "code": error_code},
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Attach global exception handlers to the FastAPI app."""

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return _error_response(exc.status_code, exc.error_code, exc.message)

    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc: Exception) -> JSONResponse:
        return _error_response(404, "NOT_FOUND", "The requested resource was not found.")

    @app.exception_handler(500)
    async def internal_error_handler(request: Request, exc: Exception) -> JSONResponse:
        return _error_response(500, "INTERNAL_SERVER_ERROR", "An unexpected error occurred.")
