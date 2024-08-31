import uuid
from datetime import date, datetime

from typing import Any


def dumps_converter(p):
    if isinstance(p, datetime) or isinstance(p, date):
        return p.isoformat()
    elif isinstance(p, uuid.UUID):
        return p.hex


class CleanedDict:
    def __init__(self, obj: dict):
        self.obj = obj

    def _clean_value(self, value: Any) -> Any:
        method = getattr(self, f"_{type(value).__name__}", None)
        if method:
            return method(value)
        return value

    def _dict(self, obj: dict) -> dict:
        res = dict()
        for k, v in obj.items():
            if not v:
                continue
            res[k] = self._clean_value(v)
        return res

    def _list(self, obj: list) -> list:
        res = list()
        for v in obj:
            if not v:
                continue
            res.append(self._clean_value(v))
        return res

    @property
    def clean_data(self) -> dict:
        return self._dict(self.obj)
