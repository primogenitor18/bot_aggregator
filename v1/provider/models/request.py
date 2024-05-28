from pydantic import BaseModel


class ProviderRequest(BaseModel):
    name: str
    auth_token: str
