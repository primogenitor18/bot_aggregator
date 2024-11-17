from telethon import events

from third_party.telethon_client import TelethonRequest
from third_party.tg_bot_base import ActionRule, EventHandler


class DohodyagaBot:
    _name = "dohodyagabot"

    def __init__(self, obj: TelethonRequest, bot_name: str):
        self.obj = obj
        self.bot_name = bot_name

    async def search(self, fts: str, search_type: str) -> list:
        _btn_text = self._buttons_search_type_map.get(search_type)
        if not _btn_text:
            return list()
    
        async with self.obj.client:
            entity = await self.obj.client.get_entity(self.bot_name)
            handle_obj = EventHandler(
                fts=fts,
                rules=[
                    ActionRule(substr="Выберите нужное действие:", action="click_button", parameters={"text": "Показать команды для поиска"}),
                    ActionRule(substr="Выберите направление поиска", action="click_button", parameters={"text": "поиск по номеру телефона"}),
                    ActionRule(substr="Примеры команд для ввода:", action="send_message", parameters={}),
                    ActionRule(substr="Если информация не найдена, закажите «Расширенный поиск»", action="save_result", parameters={"from_media": False}),
                    ActionRule(substr="Учетная запись заблокирована до", action="disconnect", parameters={}),
                    ActionRule(substr="Поиск по России доступен лишь гражданам Российской Федерации", action="disconnect", parameters={}),
                ]
            )

            self.obj.client.add_event_handler(handle_obj.handler, events.NewMessage)
            self.obj.client.add_event_handler(handle_obj.handler, events.MessageEdited)

            try:
                await self.obj.client.send_message(entity, "/start")
            except ConnectionError:
                await self.obj.client.connect()
                await self.obj.client.send_message(entity, "/start")

            await self.obj.client.run_until_disconnected()

            return handle_obj.result.copy()
