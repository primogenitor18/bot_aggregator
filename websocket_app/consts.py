from enum import Enum
from typing import Literal, List, Optional, Union
from pydantic import BaseModel, Field


class SocketEvent(Enum):
    connect = "connect"
    code_request = "code_request"
    tg_bot_parse_result = "tg_bot_parse_result"


class SocketAction(Enum):
    task = "task"
    message = "message"


class TaskData(BaseModel):
    action: Literal["search"]
    target: str
    kwargs: dict


class SocketMessage(BaseModel):
    event_type: SocketEvent
    name: str
    data: Union[dict, list]
    task_data: Optional[TaskData] = None


class SocketExchangeMessage(BaseModel):
    except_sockets: List[Union[int, str]] = Field(default_factory=list)
    target_sockets: List[Union[int, str]] = Field(default_factory=list)
    recipients: List[Union[int, str]] = Field(default_factory=list)
    message: SocketMessage
    action: SocketAction = SocketAction.message
