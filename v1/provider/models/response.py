from pydantic import BaseModel


class ProviderResponse(BaseModel):
    name: str


class ProviderFullResponse(ProviderResponse):
    auth_token: str


class ProviderUserInfoResponse(BaseModel):
    query_count_all: int
    query_count_api_limit: int
