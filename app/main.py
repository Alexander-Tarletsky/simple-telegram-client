import logging
import os
import pathlib
from uuid import UUID

from fastapi import FastAPI, HTTPException
from starlette.responses import JSONResponse
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.sessions import StringSession

from app.exceptions import BaseCustomException
from app.models import Connection, AuthRequest
from app.storage import storage
from app.utils import send_welcome_message

logger = logging.getLogger(__name__)

API_ID = os.getenv("API_ID", "")
API_HASH = os.getenv("API_HASH", "")

BASE_ROOT = pathlib.Path(__file__).resolve().parent


app = FastAPI()


@app.post("/connect")
async def connect(connection: Connection) -> JSONResponse:
    """
    Connect to Telegram using the provided session data and user information.
    If the user is not authorized, send a code request to their phone.
    """
    user = connection.user

    client = TelegramClient(
        StringSession(connection.session_data),
        int(API_ID),
        API_HASH,
    )

    await client.connect()
    storage.add_unauthorized_client(user.id, client)

    # Check if the client is already authorized
    if not await client.is_user_authorized():
        logger.info("User %s is not authorized. Sending code request.", user.phone)
        await client.send_code_request(user.phone)

        return JSONResponse(
            status_code=401,
            content={
                "status": "code_sent",
                "message": "Code sent to your phone.",
                "user_id": user.id,
                "phone_number": user.phone,
            },
            headers={
                "WWW-Authenticate": "Bearer",
                "Content-Type": "application/json",
            }
        )

    # Check the 2FA status by sending a welcome message
    try:
        await send_welcome_message(client, user)
    except SessionPasswordNeededError as e:  # This means the user has 2FA enabled
        logger.info("2FA password required for user %s", user.phone)
        return JSONResponse(
            status_code=401,
            content={
                "status": "password_required",
                "error": str(e),
                "message": "2FA password required.",
                "user_id": user.id,
                "phone_number": user.phone,
            },
            headers={
                "WWW-Authenticate": "Bearer",
                "Content-Type": "application/json",
            }
        )
    except Exception as e:
        logger.error("Failed to send welcome message: %s", e)
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "error": str(e),
                "message": str(e),
                "user_id": user.id,
                "phone_number": user.phone,
            }
        )

    # Check getting user information
    me = await client.get_me()

    if not me:
        logger.error("Failed to retrieve user information.")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "error": "Failed to retrieve user information.",
                "message": "Failed to retrieve user information. Try to reconnect.",
                "user_id": user.id,
                "phone_number": user.phone,
            }
        )

    # Move the client to the authorized clients storage
    try:
        storage.move_client_to_active(user.id)
    except KeyError:
        logger.error("Client with user_id %s not found in unauthorized clients.", user.id)
        return JSONResponse(
            status_code=404,
            content={
                "status": "error",
                "error": "Client not found.",
                "message": "Client not found. Please connect first.",
                "user_id": user.id,
            },
            headers={
                "WWW-Authenticate": "Bearer",
                "Content-Type": "application/json",
            }
        )

    logger.info("User %s is authorized and connected.", user.id)
    return JSONResponse(
        status_code=200,
        content={
            "status": "authorized",
            "message": "Client is authorized and connected.",
            "user_id": user.id,
            "phone_number": user.phone,
            "telegram_user_id": me.id,
        },
        headers={
            "Content-Type": "application/json",
        }
    )


@app.post("/authorize_client")
async def authorize_client(auth: AuthRequest):
    """
    Authorize a client using the code sent to the user's phone and the 2FA password if required.
    """
    try:
        client = storage.get_unauthorized_client(auth.user_id)
    except KeyError:
        logger.error("Client with user_id %s not found in unauthorized clients.", auth.user_id)
        return JSONResponse(
            status_code=404,
            content={
                "status": "error",
                "error": "Client not found.",
                "message": "Client not found. Please connect first.",
                "user_id": auth.user_id,
            },
            headers={
                "WWW-Authenticate": "Bearer",
                "Content-Type": "application/json",
            }
        )

    f2a_password = {"password": auth.password} if auth.password else {}

    try:
        await client.sign_in(
            phone=auth.phone,
            code=auth.code,
            **f2a_password
        )
    except SessionPasswordNeededError as e:
        logger.info("2FA password required for user %s", auth.phone)
        return JSONResponse(
            status_code=401,
            content={
                "status": "password_required",
                "error": str(e),
                "message": "2FA password required.",
                "user_id": auth.user_id,
                "phone_number": auth.phone,
            },
            headers={
                "WWW-Authenticate": "Bearer",
                "Content-Type": "application/json",
            }
        )
    except Exception as e:
        logger.error("Failed to authorize client: %s", e)
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "error": "Failed to authorize client: %s" % str(e),
                "message": "Failed to authorize client: %s" % str(e),
                "user_id": auth.user_id,
                "phone_number": auth.phone,
            }
        )

    # Check getting user information
    me = await client.get_me()

    if not me:
        logger.error("Failed to retrieve user information.")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "error": "Failed to retrieve user information.",
                "message": "Failed to retrieve user information. Try to reconnect.",
                "user_id": auth.user_id,
                "phone_number": auth.phone,
            }
        )

    # Move the client to the authorized clients storage
    try:
        storage.move_client_to_active(auth.user_id)
    except KeyError:
        logger.error("Client with user_id %s not found in unauthorized clients.", auth.user_id)
        return JSONResponse(
            status_code=404,
            content={
                "status": "error",
                "error": "Client not found.",
                "message": "Client not found. Please connect first.",
                "user_id": auth.user_id,
            },
            headers={
                "WWW-Authenticate": "Bearer",
                "Content-Type": "application/json",
            }
        )

    logger.info("User %s is authorized and connected.", auth.user_id)
    return JSONResponse(
        status_code=200,
        content={
            "status": "authorized",
            "message": "Client is authorized and connected.",
            "user_id": auth.user_id,
            "phone_number": auth.phone,
        },
        headers={
            "Content-Type": "application/json",
        }
    )


@app.post("/disconnect/{user_id}")
async def disconnect(user_id: UUID):
    """
    Disconnect the client associated with the given user_id.
    """
    try:
        client = storage.get_active_client(user_id)
    except KeyError:
        logger.error("Client with user_id %s not found in active clients.", user_id)
        return JSONResponse(
            status_code=404,
            content={
                "status": "error",
                "error": "Client not found.",
                "message": "Client not found. Please connect first.",
                "user_id": user_id,
            },
            headers={
                "WWW-Authenticate": "Bearer",
                "Content-Type": "application/json",
            }
        )

    await client.disconnect()
    storage.add_unauthorized_client(user_id, client)
    session_data = await client.session.save()
    # TODO: await api.save_session(user_id, session_data)
    storage.remove_active_client(user_id)

    logger.info("User %s is disconnected.", user_id)
    return JSONResponse(
        status_code=200,
        content={
            "status": "disconnected",
            "message": "Client is disconnected.",
            "user_id": user_id,
        },
        headers={
            "Content-Type": "application/json",
        }
    )


# @app.exception_handler(BaseCustomException)
# async def custom_exception_handler(request, exc: BaseCustomException):
#     """
#     Custom exception handler for BaseCustomException.
#     """
#     logger.error("Custom exception occurred: %s", exc)
#     return JSONResponse(
#         status_code=exc.status_code,
#         content={
#             "status": "error",
#             "error": str(exc),
#             "message": str(exc),
#         },
#         headers={
#             "WWW-Authenticate": "Bearer",
#             "Content-Type": "application/json",
#         }
#     )





if __name__ == "__main__":
    # Use this for debugging purposes only
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8003, log_level="debug")