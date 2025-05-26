import logging
from uuid import UUID

from fastapi import APIRouter, Depends
from starlette import status
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.sessions import StringSession

from app.dependencies.auth import verify_api_key
from app.exceptions.exceptions import AuthTelegramException, NotFoundClientException
from app.main import TG_API_ID, TG_API_HASH
from app.models import Connection, AuthRequest, APIResponse
from app.storage import storage
from app.utils import send_welcome_message, get_user_info

logger = logging.getLogger(__name__)


router = APIRouter(dependencies=[Depends(verify_api_key)])

@router.post("/connect", response_model=APIResponse)
async def connect(connection: Connection) -> dict:
    """
    Connect to Telegram using the provided session data and user information.
    If the user is not authorized, send a code request to their phone.
    """
    user = connection.user

    client = TelegramClient(
        StringSession(connection.session_data),
        TG_API_ID,
        TG_API_HASH,
    )

    await client.connect()
    storage.add_unauthorized_client(user.id, client)

    # Check if the client is already authorized
    if not await client.is_user_authorized():
        logger.info(
            "User %s is not authorized. Sending code request to phone %s", user.id, user.phone
        )
        await client.send_code_request(user.phone)

        raise AuthTelegramException("User is not authorized. Code sent to phone.")

    # Check the 2FA status by sending a welcome message
    await check_2fa_status(client, user.id)

    # Check getting user information
    await get_user_info(client, user.id, raise_exc=True)
    logger.info("User: %s is authorized and connected with telegram.", user.id)

    # Move the client to the authorized clients storage
    await move_client_to_active(user.id)
    logger.info("User %s is authorized and connected.", user.id)

    # Return a successful response
    return {
        "status_code": status.HTTP_200_OK,
        "message": "Client is authorized and connected.",
        "data": {},
    }


@router.post("/authorize_client", response_model=APIResponse)
async def authorize_client(auth: AuthRequest) -> dict:
    """
    Authorize a client using the code sent to the user's phone and the 2FA password if required.
    """
    try:
        client = storage.get_unauthorized_client(auth.user_id)
    except KeyError as e:
        logger.error("Client with user_id %s not found in unauthorized clients.", auth.user_id)
        raise NotFoundClientException(str(e))

    f2a_password = {"password": auth.password} if auth.password else {}

    try:
        await client.sign_in(
            phone=auth.phone,
            code=auth.code,  # Code received from the user phone
            **f2a_password,
        )
    except SessionPasswordNeededError as e:
        logger.info("2FA password required for user %s with phone %s", auth.user_id, auth.phone)
        raise e
    else:
        logger.info(
            "User %s is authorized with phone %s", auth.user_id, auth.phone
        )

    # Check getting user information
    await get_user_info(client, auth.user_id, raise_exc=True)
    logger.info("User: %s is authorized and connected with telegram.", auth.user_id)

    # Check the 2FA status by sending a welcome message
    await check_2fa_status(client, auth.user_id)
    logger.info("Welcome message sent to user %s with phone %s", auth.user_id, auth.phone)

    # Move the client to the authorized clients storage
    await move_client_to_active(auth.user_id)
    logger.info("User %s is authorized and connected.", auth.user_id)

    # Return a successful response
    return {
        "status_code": status.HTTP_200_OK,
        "message": "Client is authorized and connected.",
        "data": {},
    }


@router.post("/disconnect/{user_id}", response_model=APIResponse)
async def disconnect(user_id: UUID) -> dict:
    """
    Disconnect the client associated with the given user_id.
    """
    try:
        client = storage.get_active_client(user_id)
    except KeyError as e:
        logger.error("Client with user_id %s not found in active clients.", user_id)
        raise NotFoundClientException(str(e))

    await client.disconnect()
    session_data = await client.session.save()
    # TODO: Encrypt session data
    # TODO: Send session data to the service
    storage.remove_active_client(user_id)

    logger.info("User %s has been disconnected.", user_id)
    return {
        "status_code": status.HTTP_200_OK,
        "message": "Client has been disconnected.",
        "data": {},
    }


async def check_2fa_status(client: TelegramClient, user_id: UUID):
    """
    Check if the user has 2FA enabled by sending a welcome message.
    If 2FA is enabled and the user has not provided a password, raise an exception.
    """
    try:
        await send_welcome_message(client)
    except SessionPasswordNeededError as e:  # This means the user has 2FA enabled
        logger.info("2FA password required for user %s", user_id)
        raise e
    else:
        logger.info("Welcome message sent successfully to user %s", user_id)


async def move_client_to_active(user_id: UUID):
    """
    Move the client associated with the given user_id from unauthorized to active clients.
    """
    try:
        storage.move_client_to_active(user_id)
    except KeyError:
        logger.error("Client with user_id %s not found in unauthorized clients.", user_id)
        raise NotFoundClientException(f"Client with user_id {user_id} not found.")
    else:
        logger.info("Client for user: %s has successfully connected.", user_id)
