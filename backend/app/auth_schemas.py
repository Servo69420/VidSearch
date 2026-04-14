from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator


class RegisterRequest(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    password: str
    hobbies: list[str] = []

    @field_validator("email", mode="before")
    @classmethod
    def empty_str_to_none(cls, v):
        return None if v == "" else v


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = None
    surname: Optional[str] = None
    email: Optional[EmailStr] = None

    @field_validator("email", mode="before")
    @classmethod
    def empty_str_to_none(cls, v):
        return None if v == "" else v
