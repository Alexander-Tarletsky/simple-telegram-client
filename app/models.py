from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserChannel(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    description: str | None
    telegram_id: str
    is_active: bool


class User(BaseModel):
    id: UUID
    phone: str
    email: EmailStr
    channels: list[UserChannel] | None
    telegram_connection_id: UUID | None

    model_config = ConfigDict(extra="ignore")


class Connection(BaseModel):
    id: UUID
    session_data: str = Field(default="")
    is_active: bool
    user_id: UUID
    user: User
    tfa_password: str | None = None  # Optional 2FA password

    model_config = ConfigDict(extra="ignore")


class APIResponse(BaseModel):
    status_code: int
    message: str
    data: dict


class AuthRequest(BaseModel):
    user_id: UUID
    phone: str  # Phone number of the user
    code: str  # Code sent to the user's phone
    tfa_password: str | None = None  # Password for 2FA if required

    model_config = ConfigDict(extra="ignore")
