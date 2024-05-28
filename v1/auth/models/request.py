from pydantic import BaseModel, Field


class Auth(BaseModel):
    """
        authentication body
    """
    username: str = Field(title="username of registered user")
    password: str = Field(None, title="user password")


class Refresh(BaseModel):
    refresh_token: str = Field(title="refresh token for update access")
