from typing import Optional

from pydantic import BaseModel, Field


class AuthResponse(BaseModel):
    access_token: Optional[str] = Field(description="jwt: Authorization: Bearer <access token>")
    refresh_token: Optional[str] = Field(description="jwt: refresh token")


class AccountResponse(BaseModel):
    id: int
    username: str
    blocked: bool
    role: str
