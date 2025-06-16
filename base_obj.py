import hashlib
import string
import random
import uuid
from typing import Union

from sqlalchemy import and_
from sqlalchemy.future import select

from config import LOCAL_SALT, WEBSOCKET_CHANNEL

from models.models import User
from models.session import AsyncSession

from websocket_app.consts import SocketAction


def password_hash(password, salt):
    return hashlib.sha512(
        password.encode("utf-8") + salt.encode("utf-8") + LOCAL_SALT.encode("utf-8")
    ).hexdigest()


def password_gen():
    password = uuid.uuid4().hex[:8]
    password = (
        random.choice(string.ascii_uppercase)
        + password
        + random.choice(string.ascii_uppercase)
    )
    return password


async def send_socket_event(
    redis_pubsub_con,
    s: AsyncSession,
    data: Union[dict, list],
    except_sockets: list = [],
    accept_users: list = [],
    exclude_users: list = [],
    only_accept_users: bool = False,
    target_sockets: list = [],
    action: SocketAction = SocketAction.message,
):
    if only_accept_users:
        recipients_filter = User.id.in_(accept_users)
    else:
        recipients_filter = and_(User.id.in_(accept_users), ~User.id.in_(exclude_users))
    recipients = (
        (await s.execute(select(User.id).filter(recipients_filter))).scalars().all()
    )
    await redis_pubsub_con.publish_json(
        WEBSOCKET_CHANNEL,
        {
            "except_sockets": except_sockets,
            "target_sockets": target_sockets,
            "recipients": recipients,
            "message": data,
            "action": action.value,
        },
    )
