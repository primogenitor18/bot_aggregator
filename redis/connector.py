import json
import aioredis
from typing import Any, Optional, Union


class OsintClientRedisTransport:

    class Mock:
        async def get_json(self):
            return {}

    def __init__(self, host: str, port: int, db: int) -> None:
        self.host = host
        self.port = port
        self.db = db
        self.connection = None
        self.channel_name = None
        self.channel = None

    async def create_connection(self, *args, **kwargs) -> None:
        try:
            self.connection = aioredis.Redis(
                host=self.host,
                port=self.port,
                db=int(self.db),
            )
        except aioredis.ConnectionError:
            self.connection = None

    async def create_channel(self, channel: str) -> None:
        try:
            self.channel_name = channel
            await self.create_connection()
            self.channel = self.connection.pubsub()
            await self.channel.subscribe(self.channel_name)
        except (aioredis.ConnectionError, aioredis.PubSubError):
            self.channel = self.Mock()

    async def get_json(self) -> dict:
        try:
            message = await self.channel.get_message()
        except (aioredis.ConnectionError, aioredis.PubSubError):
            await self.create_channel(self.channel_name)
            message = await self.channel.get_message()
        try:
            return json.loads(message["data"])
        except Exception:
            return dict()

    async def publish_json(self, channel: str, data: dict) -> None:
        try:
            await self.connection.publish(channel, json.dumps(data))
        except aioredis.ConnectionError:
            await self.create_connection()
            if self.connection:
                await self.connection.publish(channel, json.dumps(data))

    async def get(self, key: Union[str, int]) -> Any:
        res = None
        try:
            res = await self.connection.get(key)
        except aioredis.ConnectionError:
            await self.create_connection()
            if self.connection:
                res = await self.connection.get(key)
        finally:
            return res

    async def delete(self, key: Union[str, int]) -> None:
        try:
            await self.connection.delete(key)
        except aioredis.ConnectionError:
            await self.create_connection()
            if self.connection:
                await self.connection.delete(key)

    async def set(
        self,
        key: Union[str, int],
        value: Union[str, int, list, dict, tuple],
    ) -> None:
        try:
            await self.connection.set(key, value)
        except aioredis.ConnectionError:
            await self.create_connection()
            if self.connection:
                await self.connection.set(key, value)


class OsintClientRedisConnection:
    def __init__(self, host: str, port: int, db: int) -> None:
        self.host = host
        self.port = port
        self.db = db
        self.transports = dict()

    async def add_transport(
        self,
        conn_name: str,
        db: Optional[int] = None,
        connection_type: Optional[str] = "create_connection",
        channel: Optional[str] = None,
    ) -> None:
        if not db:
            db = self.db
        self.transports[conn_name] = OsintClientRedisTransport(
            host=self.host,
            port=self.port,
            db=db,
        )
        await getattr(self.transports[conn_name], connection_type)(channel=channel)
