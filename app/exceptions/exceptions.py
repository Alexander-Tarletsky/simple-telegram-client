from fastapi import HTTPException
from starlette import status


class BaseCustomAppException(Exception):
    def __init__(
        self,
        # status_code: int,
        detail: str | None = None,
        # headers: dict | None = None,
    ) -> None:
        super().__init__(detail)
        # self.status_code = status_code
        self.detail = detail or "An error occurred."
        # self.headers = headers or {}


class AuthTelegramException(HTTPException):
    def __init__(self, msg: str | None = None) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=msg or "Unauthorized access.",
        )


class NotFoundClientException(HTTPException):
    def __init__(self, msg: str | None = None) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=msg or "User client not found."
        )
