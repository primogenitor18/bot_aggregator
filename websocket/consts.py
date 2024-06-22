from enum import Enum


class SocketEvent(Enum):
    connect = "connect"
    code_request = "code_request"
    tg_bot_parse_result = "tg_bot_parse_result"
