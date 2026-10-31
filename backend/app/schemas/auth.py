import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)


class UserBase(StrictModel):
    email: EmailStr = Field(max_length=254)

    @field_validator("email")
    @classmethod
    def normalize(cls, value):
        return value.casefold()


class UserCreate(UserBase):
    password: str = Field(min_length=12, max_length=128)


class Login(UserBase):
    password: str = Field(min_length=1, max_length=128)


class UserDisplay(UserBase):
    id: uuid.UUID
    created_at: datetime
    verified: bool


class Token(StrictModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserDisplay


class TokenData(StrictModel):
    sub: str


class PasswordChange(StrictModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=12, max_length=128)


class PasswordReset(StrictModel):
    token: str = Field(pattern=r"^[a-f0-9]{64}$")
    new_password: str = Field(min_length=12, max_length=128)


class VerifyToken(StrictModel):
    password: str = Field(min_length=1, max_length=128)
    token: str = Field(pattern=r"^[a-f0-9]{64}$")


class DeleteAccount(StrictModel):
    password: str = Field(min_length=1, max_length=128)
