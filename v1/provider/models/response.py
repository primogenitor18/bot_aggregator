from pydantic import BaseModel


class ProviderResponse(BaseModel):
    name: str
    auth_token: str
