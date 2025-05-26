import logging
import os

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

logger = logging.getLogger(__name__)

TG_API_ID = os.getenv("TG_API_ID", "")
TG_API_HASH = os.getenv("TG_API_HASH", "")

# BASE_ROOT = pathlib.Path(__file__).resolve().parent


app = FastAPI()

app.include_router(
    endpoints.router,
    prefix="/api/v1",
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