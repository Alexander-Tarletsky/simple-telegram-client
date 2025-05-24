import logging
from typing import Dict
from uuid import UUID

from telethon import TelegramClient

logger = logging.getLogger(__name__)


class ClientStorage:
    def __init__(self):
        self._active_clients: Dict[UUID, TelegramClient] = {}  # {user_id: TelegramClient}
        self._unauthorized_clients: Dict[UUID, TelegramClient] = {}

    def add_active_client(self, user_id: UUID, client: TelegramClient) -> None:
        self._active_clients[user_id] = client

    def add_unauthorized_client(self, user_id: UUID, client: TelegramClient) -> None:
        self._unauthorized_clients[user_id] = client

    def move_client_to_active(self, user_id: UUID) -> None:
        """
        Move a client from unauthorized to active storage if it exists,
        otherwise raise a KeyError.
        """
        if user_id in self._unauthorized_clients:
            client = self._unauthorized_clients.pop(user_id)
            self._active_clients[user_id] = client
        else:
            raise KeyError(f"Client with user_id {user_id} not found in unauthorized clients.")

    def get_unauthorized_client(
        self,
        user_id: UUID,
        raise_exc: bool = True,
    ) -> TelegramClient | None:
        """
        Get a client from unauthorized storage by user_id.
        If raise_exc is True and the client is not found, raise KeyError.
        """
        client = self._unauthorized_clients.get(user_id)
        if client is None and raise_exc:
            raise KeyError(f"Client with user_id {user_id} not found in unauthorized clients.")
        return client

    def get_active_client(
        self,
        user_id: UUID,
        raise_exc: bool = True,
    ) -> TelegramClient | None:
        """
        Get a client from active storage by user_id.
        If raise_exc is True and the client is not found, raise KeyError.
        """
        client = self._active_clients.get(user_id)
        if client is None and raise_exc:
            raise KeyError(f"Client with user_id {user_id} not found in active clients.")
        return client

    def remove_active_client(self, user_id: UUID, raise_exc: bool = False) -> None:
        """
        Remove a client from active storage by user_id.
        """
        if user_id in self._active_clients:
            del self._active_clients[user_id]
        elif raise_exc:
            raise KeyError(f"Client with user_id {user_id} not found in active clients.")
        else:
            logger.warning(
                f"Client with user_id {user_id} not found in active clients after its stopping. "
                f"It has already been removed from active storage."
            )

    def remove_unauthorized_client(self, user_id: UUID, raise_exc: bool = False) -> None:
        """
        Remove a client from unauthorized storage by user_id.
        """
        if user_id in self._unauthorized_clients:
            del self._unauthorized_clients[user_id]
        elif raise_exc:
            raise KeyError(f"Client with user_id {user_id} not found in unauthorized clients.")
        else:
            logger.warning(
                f"Client with user_id {user_id} not found in unauthorized clients after its stopping. "
                f"It has already been removed from unauthorized storage."
            )


storage = ClientStorage()