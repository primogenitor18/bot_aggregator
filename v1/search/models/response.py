from typing import List

from pydantic import BaseModel


class SearchResponse(BaseModel):
    provider_name: str
    data: List[dict]


class ParsingTaskStartResponse(BaseModel):
    task_id: str


class ParsingTaskResultResponse(BaseModel):
    files: List[str]
    count: int = 0


class ParsingTaskResponse(BaseModel):
    id: int
    task_id: str
    filename: str
    status: str


class ParsingTasksListResponse(BaseModel):
    result: List[ParsingTaskResponse]
    count: int
