import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from jose import JWTError

logger = logging.getLogger("autogst.exceptions")


def error_response(message: str, error_code: str, details: str = None, status_code: int = 500):
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "message": message,
            "error_code": error_code,
            "details": details,
        },
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning("Validation error on %s: %s", request.url, str(exc.errors()))
    return error_response(
        message="Request validation failed",
        error_code="VALIDATION_ERROR",
        details=str(exc.errors()),
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.error("Database error on %s: %s", request.url, str(exc))
    return error_response(
        message="A database error occurred",
        error_code="DATABASE_ERROR",
        details=str(exc) if logger.level <= logging.DEBUG else None,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


async def jwt_exception_handler(request: Request, exc: JWTError):
    logger.warning("JWT error on %s: %s", request.url, str(exc))
    return error_response(
        message="Authentication token is invalid or expired",
        error_code="AUTH_ERROR",
        status_code=status.HTTP_401_UNAUTHORIZED,
    )


async def generic_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception on %s: %s", request.url, str(exc), exc_info=True)
    return error_response(
        message="An unexpected error occurred",
        error_code="INTERNAL_ERROR",
        details=str(exc) if logger.level <= logging.DEBUG else None,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


async def http_exception_handler(request: Request, exc):
    from fastapi.exceptions import HTTPException
    logger.warning("HTTP %d on %s: %s", exc.status_code, request.url, exc.detail)
    return error_response(
        message=exc.detail,
        error_code=f"HTTP_{exc.status_code}",
        status_code=exc.status_code,
    )
