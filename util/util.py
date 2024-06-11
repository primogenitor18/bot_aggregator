import uuid
from datetime import date, datetime


def dumps_converter(p):
    if isinstance(p, datetime) or isinstance(p, date):
        return p.isoformat()
    elif isinstance(p, uuid.UUID):
        return p.hex
