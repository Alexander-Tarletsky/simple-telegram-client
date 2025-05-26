import logging
from typing import Any

logger = logging.getLogger(__name__)


async def send_welcome_message(client, user="me") -> None:
    """
    Send a welcome message to the user.
    """
    await client.send_message(
        user,
        "Welcome to the Vacancy Collector Application! "
        "You are successfully connected.",
    )


async def get_user_info(client, user_id, raise_exc=False) -> Any | None:
    """
    Retrieve basic user information.
    """
    me = await client.get_me()
    if not me:
        logger.error("Failed to retrieve basic info for user %s", user_id)
        if raise_exc:
            raise Exception("Failed to retrieve user information.")
        return None

    return me
