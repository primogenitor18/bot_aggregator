from telethon import events

from third_party.telethon_client import TelethonRequest
from third_party.tg_bot_base import ActionRule, EventHandler


class PoiskChelovekaTelefonuBot:
    _name = "poiskchelovekatelefonubot"
    _buttons_search_type_map = {
        "name": "поиск по имени",
        "phone": "поиск по номеру телефона",
        "email": "поиск по e-mail",
        "pasport": "поиск по номеру паспорта",
        "inn": "поиск по инн, снилс",
        "snils": "поиск по инн, снилс",
        "address": "поиск по ",
        "auto": "поиск по номеру авто",
        "ogrn": "",
    }

    def __init__(self, obj: TelethonRequest):
        self.obj = obj

    async def search(self, fts: str, search_type: str) -> list:
        _btn_text = self._buttons_search_type_map.get(search_type)
        if not _btn_text:
            return list()
    
        async with self.obj.client:
            entity = await self.obj.client.get_entity("@NetLayBot")
            handle_obj = EventHandler(
                fts=fts,
                rules=[
                    ActionRule(substr="Примеры Сообщений для Бота:", action="click_button", parameters={"text": "начать поиск"}),
                    ActionRule(substr="Выберите направление поиска", action="click_button", parameters={"text": _btn_text}),
                    ActionRule(substr="ОТЧЁТ ПО ЗАПРОСУ:", action="save_result", parameters={}),
                    ActionRule(substr="В ответ вы получите информацию по", action="send_message", parameters={}),
                    ActionRule(substr="Превышен суточный лимит поиска по запросу", action="disconnect", parameters={}),
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
