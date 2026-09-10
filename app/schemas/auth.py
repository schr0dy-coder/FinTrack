"""Authentication & User Pydantic Schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    """Payload for user registration."""

    name: str = Field(..., min_length=2, max_length=100, json_schema_extra={"example": "John Doe"})
    email: EmailStr = Field(..., json_schema_extra={"example": "john@example.com"})
    password: str = Field(
        ..., min_length=6, max_length=128, json_schema_extra={"example": "StrongPassword123"}
    )


class UserLogin(BaseModel):
    """Payload for user authentication."""

    email: EmailStr = Field(..., json_schema_extra={"example": "john@example.com"})
    password: str = Field(..., json_schema_extra={"example": "StrongPassword123"})


class Token(BaseModel):
    """JWT Token response schema."""

    access_token: str
    token_type: str = "bearer"
    user_id: int
    name: str
    email: str
    role: str


class TokenPayload(BaseModel):
    """Decoded JWT payload."""

    sub: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[int] = None


class UserResponse(BaseModel):
    """User profile response."""

    id: int
    name: str
    email: str
    role: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
