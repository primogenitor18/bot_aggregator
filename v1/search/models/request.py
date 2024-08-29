from typing import Literal

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    provider: str = Field("quickosint")
    fts: str
    country: Literal["RU", "UA", "BY", "KZ"] = Field("RU")
    search_type: Literal[
        "name",
        "phone",
        "email",
        "pasport",
        "inn",
        "snils",
        "address",
        "auto",
        "ogrn",
    ] = Field("name")


class TaskRestartRequest(BaseModel):
    task_id: int
