import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import asyncio
import traceback
from contextlib import asynccontextmanager

from typing import Dict, List, Union

from fastapi import FastAPI, WebSocket, Query, WebSocketDisconnect

from models.models import User

from util.util import dumps_converter

from managers.auth.manager import AuthManager

from third_party.telethon_client import TelethonRequest

from config import (
    USE_TELETHON,
    REDIS_URI,
    REDIS_PORT,
    REDIS_PUBSUB_DB,
    WEBSOCKET_CHANNEL,
)

from redis.wrapper import (
    QueueManager,
    RedisConnectionInfo,
    RedisConnectionTransportInfo,
)

from websocket.consts import (
    SocketEvent,
    SocketExchangeMessage,
    SocketMessage,
    SocketAction,
)

from managers.search.tg_bots.poisk_cheloveka_telefonubot import PoiskChelovekaTelefonuBot


class ConnectionManager:
    _actions = {
        "search": {PoiskChelovekaTelefonuBot._name: PoiskChelovekaTelefonuBot}
    }

    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = dict()
        self.active_users: Dict[int, User] = dict()
        #  self.obj = TelethonRequest(None)
        self.lock = asyncio.Lock()

    async def check_telethon_session(self, websocket: WebSocket) -> None:
        async with self.lock:
            obj = TelethonRequest(None)
            if not await obj.is_logged_in():
                await self.send(websocket, {"event_type": SocketEvent.code_request.value})
                await obj.send_code_request()
                data = await websocket.receive_json()
                await obj.logging_in(data.get("token", ""))
                await obj.disconnect()
            obj.session.close()
            del obj

    async def run_task(self, message: SocketExchangeMessage) -> None:
        if not message.message.task_data:
            return
        async with self.lock:
            parse_obj = self._actions.get(
                message.message.task_data.action, {}
            ).get(message.message.task_data.target)
            if not parse_obj:
                return
            obj = TelethonRequest(None)
            instance = parse_obj(obj)
            try:
                res = await instance.search(**message.message.task_data.kwargs)
            except Exception:
                print(traceback.format_exc())
                res = [{"message": "Internal error"}]
            await self.broadcast(
                data={
                    "event_type": message.message.event_type.value,
                    "name": parse_obj._name,
                    "data": res,
                },
                recipients_ids=message.recipients,
                target_sockets=[str(s) for s in message.target_sockets if s],
                except_sockets=[str(s) for s in message.except_sockets if s],
            )
            obj.session.close()
            del obj

    @QueueManager(
        [
            RedisConnectionInfo(
                name="pubsub_connection",
                host=REDIS_URI,
                port=REDIS_PORT,
                db=REDIS_PUBSUB_DB,
                connections=[
                    RedisConnectionTransportInfo(
                        name="redis_pubsub_con",
                        conn_type="create_channel",
                        channel=WEBSOCKET_CHANNEL,
                        main_listener=True,
                    ),
                ],
                main_listener=True,
            ),
        ],
    )
    async def read_queue_message(
        self,
        message: dict,
        **kwargs,
    ) -> None:
        if not message:
            return
        message = SocketExchangeMessage.validate(message)
        if message.action.value == SocketAction.task.value:
            await self.run_task(message)
        else:
            await self.broadcast(
                data=message.message.dict(),
                recipients_ids=message.recipients,
                target_sockets=[str(s) for s in message.target_sockets if s],
                except_sockets=[str(s) for s in message.except_sockets if s],
            )

    async def connect(
            self, websocket: WebSocket, user: User
    ) -> None:
        await websocket.accept()
        if not self.active_connections.get(user.id):
            self.active_connections[user.id] = list()
            self.active_users[user.id] = user
        self.active_connections[user.id].append(websocket)
        await self.send(websocket, {"socket_id": id(websocket), "event_type": SocketEvent.connect.value})
        if USE_TELETHON:
            await self.check_telethon_session(websocket)

    async def disconnect(
            self, websocket: WebSocket, user: User
    ) -> None:
        self.active_connections[user.id].remove(websocket)
        if not self.active_connections[user.id]:
            self.active_users.pop(user.id, None)
            try:
                await websocket.close()
            except Exception as e:
                print("disconnect: ", traceback.format_exc())

    def _filter_accept_sockets(
            self,
            user_id: int,
            target_sockets: List[str] = [],
            except_sockets: List[str] = [],
    ) -> List[WebSocket]:
        _recipients = list()
        for connection in self.active_connections.get(user_id, []):
            if target_sockets and str(id(connection)) not in target_sockets:
                continue
            elif str(id(connection)) in except_sockets:
                continue
            _recipients.append(connection)
        return _recipients

    def _filter_recipients_sockets(
            self,
            recipients_ids: List[int] = [],
            target_sockets: List[str] = [],
            except_sockets: List[str] = [],
    ) -> List[WebSocket]:
        _recipients = list()
        for recipient_id in recipients_ids:
            _recipients.extend(
                self._filter_accept_sockets(
                    recipient_id, target_sockets, except_sockets
                )
            )
        return _recipients

    async def broadcast(
            self,
            data: dict,
            recipients_ids: List[int] = [],
            target_sockets: List[str] = [],
            except_sockets: List[str] = [],
    ) -> None:
        for connection in self._filter_recipients_sockets(
            recipients_ids, target_sockets, except_sockets,
        ):
            await self.send(connection, data)

    async def decline_connection(
        self, websocket: WebSocket, data: dict
    ) -> None:
        await websocket.accept()
        await self.send(websocket, data)
        await websocket.close()

    async def send(self, websocket: WebSocket, data: Union[dict, str]) -> None:
        if isinstance(data, dict):
            data = json.dumps(data, default=dumps_converter)
        try:
            await websocket.send_text(data)
        except Exception as e:
            await websocket.close()
            print("send: ", traceback.format_exc())


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.manager = ConnectionManager()
    app.listener_task = asyncio.create_task(app.manager.read_queue_message())
    yield
    app.listener_task.cancel()
    try:
        await app.listener_task
    except asyncio.CancelledError:
        print("Queue reader task canceled before shuting down")


app = FastAPI(title="API", version="1.0", lifespan=lifespan)


@app.websocket("/websocket")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query("", description="Auth token"),
):
    status_code, reason, user = await AuthManager.check_token(token)
    if user.is_anonymous:
        await websocket.app.manager.decline_connection(websocket, {"status": status_code, "reason": reason})
        return
    await websocket.app.manager.connect(websocket, user)
    try:
        while True:
            await websocket.receive_json()
    except WebSocketDisconnect:
        await websocket.app.manager.disconnect(websocket, user)
    except Exception as e:
        print("websocket_endpoint: ", traceback.format_exc())
