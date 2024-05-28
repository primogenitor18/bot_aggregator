from typing import Optional

from pydantic import BaseModel


class Error40xResponse(BaseModel):
    reason: Optional[str]
