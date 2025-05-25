import logging

from fastapi import HTTPException
from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse
from telethon.errors import SessionPasswordNeededError

from app.exceptions.exceptions import AuthTelegramException

logger = logging.getLogger(__name__)


async def general_exception_handler(request: Request, exc: Exception):
    """
    Custom exception handler for general exceptions.
    Logs the error and returns a JSON response with the error details.
    """
    logger.error("An unexpected error occurred: %s", str(exc))
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "error": str(exc),
            "message": "Internal Server Error",
        },
        headers={
            "Content-Type": "application/json",
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Custom exception handler for HTTPException.
    Logs the error and returns a JSON response with the error details.
    """
    logger.error("HTTPException occurred: %s", str(exc.detail))
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": exc.status_code,
            "error": str(exc.detail),
            "message": str(exc.detail),
        },
        headers={
            "Content-Type": "application/json",
        },
    )


async def auth_telegram_exception_handler(request: Request, exc: AuthTelegramException):
    """
    Custom exception handler for AuthTelegramException.
    Logs the error and returns a JSON response with the error details.
    """
    logger.error("AuthTelegramException occurred: %s", str(exc.detail))
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": exc.status_code,
            "error": str(exc.detail),
            "message": str(exc.detail),
        },
        headers={
            "Content-Type": "application/json",
        },
    )


# 2FA password required exception handler
async def two_fa_password_required_handler(request: Request, exc: SessionPasswordNeededError):
    """
    Custom exception handler for 2FA password required exceptions.
    Logs the error and returns a JSON response with the error details.
    """
    logger.info("2FA password required: %s", str(exc))
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "status": status.HTTP_401_UNAUTHORIZED,
            "error": "Two-Factor Authentication Required",
            "message": "Please provide your 2FA password to continue.",
        },
        headers={
            "Content-Type": "application/json",
        },
    )
