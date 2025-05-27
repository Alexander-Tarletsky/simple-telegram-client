import logging
from uuid import UUID

from fastapi import APIRouter, Depends
from starlette import status
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.sessions import StringSession

from app.config import settings
from app.dependencies.auth import verify_api_key
from app.exceptions.exceptions import AuthTelegramException, NotFoundClientException
from app.models import Connection, AuthRequest, APIResponse
from app.security.crypto import decrypt_session, encrypt_session
from app.services.session import send_encrypted_session
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

    # Decrypt the session data
    session_data = decrypt_session(connection.session_data)

    client = TelegramClient(
        StringSession(session_data),
        settings.TG_API_ID,
        settings.TG_API_HASH,
    )

    storage.add_unauthorized_client(user.id, client)
    logger.info("Connecting to Telegram for user %s with phone %s", user.id, user.phone)
    await client.connect()

    # Check if the client is already authorized
    if not await client.is_user_authorized():
        logger.info(
            "User %s is not authorized. Sending code request to phone %s", user.id, user.phone
        )
        await client.send_code_request(user.phone)

        raise AuthTelegramException("User is not authorized. Code sent to phone.")

    # Check the 2FA status by sending a welcome message
    await check_2fa_status(client, user.id)
    # TODO: Check if the user has provided a 2FA password

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

    tfa_password = {"password": auth.tfa_password or {}}  # Use an empty dict if no password is provided

    try:
        logger.info("Authorizing user %s with phone %s", auth.user_id, auth.phone)
        await client.sign_in(
            phone=auth.phone,
            code=auth.code,  # Code received from the user phone
            **tfa_password,
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
    await send_encrypted_session(user_id, encrypt_session(session_data))
    logger.info("Session data for user %s has been sent to the storage service.", user_id)

    storage.remove_active_client(user_id)

    logger.info("User %s has been disconnected from Telegram.", user_id)
    return {
        "status_code": status.HTTP_200_OK,
        "message": "User %s has been disconnected." % user_id,
        "data": {},
    }


async def check_2fa_status(client: TelegramClient, user_id: UUID, raise_exc: bool = False):
    """
    Check if the user has 2FA enabled by sending a welcome message.
    If 2FA is enabled and the user has not provided a password, raise an exception.
    """
    try:
        await send_welcome_message(client)
    except SessionPasswordNeededError as e:  # This means the user has 2FA enabled
        logger.info("2FA password required for user %s", str(user_id))
        # TODO: Check if the user has provided a 2FA password
        raise e
    else:
        logger.info("Welcome message sent successfully to user %s", str(user_id))


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
