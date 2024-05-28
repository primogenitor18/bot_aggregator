from pydantic import BaseModel


class SearchRequest(BaseModel):
    fts: str
