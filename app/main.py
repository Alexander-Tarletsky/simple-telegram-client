import logging

from fastapi import FastAPI, HTTPException
from telethon.errors import SessionPasswordNeededError

from app.api.v1 import endpoints
from app.exceptions.exceptions import AuthTelegramException, NotFoundClientException
from app.exceptions.handlers import (
    general_exception_handler,
    http_exception_handler,
    auth_telegram_exception_handler,
    two_fa_password_required_handler,
    not_found_client_exception_handler,
)
from config import settings

logger = logging.getLogger(__name__)


app = FastAPI()

app.include_router(
    endpoints.router,
    prefix=settings.API_V1_STR,
    tags=["v1"],
)


app.add_exception_handler(Exception, general_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(AuthTelegramException, auth_telegram_exception_handler)
app.add_exception_handler(SessionPasswordNeededError, two_fa_password_required_handler)
app.add_exception_handler(NotFoundClientException, not_found_client_exception_handler)


if __name__ == "__main__":
    # Use this for debugging purposes only
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8003, log_level="debug")