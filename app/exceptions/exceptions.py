from fastapi import HTTPException
from starlette import status


class CustomAppException(Exception):
    def __init__(self, name: str):
        self.name = name


class AuthTelegramException(HTTPException):
    def __init__(self, msg: str | None = None) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=msg or "Unauthorized access.",
        )


# class BaseHTTPException(HTTPException):
#     def __init__(self, status_code: int, detail: str, **kwargs) -> None:
#         super().__init__(status_code=status_code, detail=detail, **kwargs)

