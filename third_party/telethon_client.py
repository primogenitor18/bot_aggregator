import os

from telethon import TelegramClient

from config import (
    TG_API_ID,
    TG_API_HASH,
    TG_PHONE,
    BASEDIR,
    TELETHON_SESSION,
)


class MyTelegramClient(TelegramClient):
    def __init__(self, code_callback, *args, **kwargs):
        self.code_callback = code_callback
        super().__init__(*args,**kwargs)

    async def connect(self: 'TelegramClient') -> None:
        if not self.is_connected():
            await super().connect()

    async def is_logged_in(self) -> bool:
        await self.connect()
        return (await self.get_me()) is not None

    async def logging_in(self) -> None:
        await self.connect()
        await self.sign_in(TG_PHONE, code=self.tg_token)

    async def __aenter__(self):
        return await self.start(phone=TG_PHONE, code_callback=self.code_callback)


class TelethonRequest:
    def __init__(self, client_callback):
        self.client = MyTelegramClient(
            session=os.path.join(BASEDIR, TELETHON_SESSION),
            api_id=TG_API_ID,
            api_hash=TG_API_HASH,
            code_callback=client_callback,
        )

    async def is_logged_in(self):
        return await self.client.is_logged_in()

    async def logging_in(self, tg_token: str) -> None:
        await self.client.connect()
        await self.client.sign_in(TG_PHONE, code=tg_token)

    async def send_code_request(self) -> None:
        await self.client.send_code_request(TG_PHONE, force_sms=False)
