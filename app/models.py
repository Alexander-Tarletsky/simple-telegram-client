from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserChannel(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    description: str | None
    telegram_id: str
    is_active: bool


class User(BaseModel):
    phone: str
    email: EmailStr
    channels: list[UserChannel] | None
    telegram_connection_id: UUID | None


class Connection(BaseModel):
    id: UUID
    session_data: str = Field(default="")
    is_active: bool
    user_id: UUID
    user: User


# class ResponseDetails(BaseModel):
#     status: str
#     error: str | None
#     message: str
#     user_id: UUID
#     phone_number: str | None


class APIResponse(BaseModel):
    status_ok: bool
    details: dict = Field(default={})
    data: dict = Field(default={})


class AuthRequest(BaseModel):
    user_id: UUID
    phone: str  # Phone number of the user
    code: str  # Code sent to the user's phone
    password: str | None = None  # Password for 2FA if required
