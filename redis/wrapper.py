import asyncio
import async_timeout
import traceback

from dataclasses import dataclass

from typing import Any, Dict, List, Optional, Union

from functools import wraps

from collections.abc import Callable

from .connector import OsintClientRedisConnection, OsintClientRedisTransport


@dataclass
class RedisConnectionTransportInfo:
    name: str
    conn_type: str = "create_connection" # Possible values: create_connection, create_hannel
    channel: Optional[str] = None
    main_listener: bool = False

    def __setattr__(self, name: str, value: Any):
        if name == "conn_type":
            if not hasattr(OsintClientRedisTransport, value):
                raise AttributeError(f"{OsintClientRedisTransport.__name__} not support {value} connection")
        super().__setattr__(name, value)


@dataclass
class RedisConnectionInfo:
    name: str
    host: str
    port: Union[str, int]
    db: Union[str, int]
    connections: List[RedisConnectionTransportInfo]
    main_listener: bool = False


class QueueManager(object):

    def __init__(
        self,
        init_redis_conns: List[RedisConnectionInfo] = [],
        sleeping_time: int = 5,
        *args,
        **kwargs,
    ):
        """
        Decorator that run function in while loop while read redis subscription
        Getting array of redis connection parameters that will be returned back to the executed function.
        As additional parameters there passes any additional parameters that will be returned back to the executed function.
        """
        self.sleeping_time = sleeping_time
        self.init_redis_conns: List[RedisConnectionInfo] = init_redis_conns
        self.redis_connections: Dict[str, OsintClientRedisConnection] = dict()
        self.main_queue_listener: str = ""
        self.main_queue_listener_transport: str = ""
        self.kwargs = kwargs

    def __call__(
        self,
        func: Callable,
        *args,
        **kwargs,
    ):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            await self._initiate_connection(self.init_redis_conns)
            message = dict()
            while True:
                message = await self._read_subscription(func.__code__.co_filename)
                await self._exec_wrapped_function(func, message, *args, **kwargs)
                await asyncio.sleep(self.sleeping_time)

        return wrapper

    async def _read_subscription(self, source: str = ""):
        message = dict()
        if self.main_queue_listener and self.main_queue_listener_transport:
            try:
                async with async_timeout.timeout(1):
                    message = await self.redis_connections[
                        self.main_queue_listener
                    ].transports[
                        self.main_queue_listener_transport
                    ].get_json()
            except asyncio.TimeoutError:
                message = dict()
            except Exception:
                print(traceback.format_exc())
                message = dict()

        return message

    async def _exec_wrapped_function(
        self,
        func: Callable,
        message: dict,
        *args,
        **kwargs,
    ):
        try:
            kwargs.update(self.kwargs)
            await func(
                redis_connections=self.redis_connections,
                message=message,
                *args,
                **kwargs,
            )
        except Exception:
            print(traceback.format_exc())

    async def _initiate_connection(
        self,
        init_redis_conns: List[RedisConnectionInfo],
    ):
        for init_conn in init_redis_conns:
            self.redis_connections[init_conn.name] = OsintClientRedisConnection(
                host=init_conn.host,
                port=int(init_conn.port),
                db=int(init_conn.db),
            )
            if init_conn.main_listener:
                self.main_queue_listener = init_conn.name
            for conn in init_conn.connections:
                await self.redis_connections[init_conn.name].add_transport(
                    conn_name=conn.name,
                    connection_type=conn.conn_type,
                    channel=conn.channel,
                )
                if conn.main_listener:
                    self.main_queue_listener_transport = conn.name
