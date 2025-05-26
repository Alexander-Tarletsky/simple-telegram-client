import logging
import os
from uuid import UUID

import aiohttp

logger = logging.getLogger(__name__)

MAIN_SERVICE_URL = os.getenv("MAIN_SERVICE_URL")


# TODO: Implement separate way to send session data. Use a Celery task or a background worker.
async def send_encrypted_session(user_id: UUID, encrypted_session_data: str) -> None:
    """
    Send the encrypted session data to the storage service.
    """
    url = f"{MAIN_SERVICE_URL}/store_session/{str(user_id)}"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json={"session_data": encrypted_session_data}) as response:
            if response.status != 200:
                logger.error("Failed to send session data for user %s: %s", user_id, response.status)
                # raise Exception(f"Failed to send session data: {response.status}")
            return await response.json()