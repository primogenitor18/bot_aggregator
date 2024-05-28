from typing import List

from pydantic import BaseModel


class SearchResponse(BaseModel):
    provider_name: str
    data: List[dict]
