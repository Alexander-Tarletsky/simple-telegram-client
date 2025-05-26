from fastapi import HTTPException
from starlette import status


class BaseCustomAppException(Exception):
    def __init__(
        self,
        detail: str | None = None,
    ) -> None:
        self.detail = detail or "An error occurred."
        super().__init__(detail)


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
