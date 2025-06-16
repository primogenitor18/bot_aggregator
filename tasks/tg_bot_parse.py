from models.session import get_session

from third_party.telethon_client import TelethonRequest

from redis.connector import OsintClientRedisConnection

from config import REDIS_URI, REDIS_PORT, REDIS_PUBSUB_DB, REDIS_DB

from .consts import BOT_PARSE_OBJS_ARR

from base_obj import send_socket_event

from websocket_app.consts import SocketEvent


async def run_bot_parsing(fts: str, search_type: str, socket_id: int, user_id: int):
    redis_connection = OsintClientRedisConnection(
        host=REDIS_URI, port=REDIS_PORT, db=REDIS_DB
    )
    await redis_connection.add_transport(conn_name="redis_pubsub_con", db=REDIS_PUBSUB_DB)
    obj = TelethonRequest(None)
    async with get_session() as s:
        for parse_obj in BOT_PARSE_OBJS_ARR:
            instance = parse_obj(obj)
            res = await instance.search(fts, search_type)
            await send_socket_event(
                redis_pubsub_con=redis_connection.transports["redis_pubsub_con"],
                s=s,
                data={
                    "event_type": SocketEvent.tg_bot_parse_result.value,
                    "name": parse_obj._name,
                    "data": res,
                },
                target_sockets=[socket_id],
                accept_users=[user_id],
            )
