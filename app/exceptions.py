from fastapi import HTTPException


class BaseCustomException(Exception):
    pass


class BaseHTTPException(HTTPException):
    def __init__(self, status_code: int, detail: str, **kwargs) -> None:
        super().__init__(status_code=status_code, detail=detail, **kwargs)
