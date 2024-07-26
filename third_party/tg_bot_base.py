import re
import traceback
from dataclasses import dataclass, field
from collections import defaultdict
from bs4 import BeautifulSoup

from typing import List, Optional, Type

from telethon import events, errors
from telethon.tl.custom.messagebutton import MessageButton


@dataclass
class ActionRule:
    substr: str
    action: str
    parameters: defaultdict(dict) = field(default_factory=lambda: defaultdict(dict))

    def check_rule(self, text: str) -> bool:
        if self.substr.lower() in text.lower():
            return True
        return False


class EventHandler:

    def __init__(
        self, fts: str, rules: List[ActionRule], event: Optional[Type[events.common.EventBuilder]] = None
    ) -> None:
        self.event = event
        self.fts = fts
        self.rules = rules
        self._result = list()
        self._sent_fts_request: bool = False

    @property
    def result(self) -> list:
        return self._result

    def _find_button(self, text: str) -> Optional[MessageButton]:
        for button in self.event.message.buttons:
            if isinstance(button, list):
                button = button[0]
            if text.lower() in button.text.lower():
                return button

    async def disconnect(self) -> None:
        self.event.client.disconnect()

    async def click_button(self, text: str) -> None:
        button = self._find_button(text)
        if not button:
            self.event.client.disconnect()
        try:
            await button.click()
        except errors.rpcerrorlist.DataInvalidError:
            pass

    async def send_message(self) -> None:
        if not self._sent_fts_request:
            await self.event.client.send_message(self.event.chat, self.fts)
            self._sent_fts_request = True

    async def save_result(self) -> None:
        #  self._result = [self.message_to_dict()]
        if not self.event.message.media:
            return
        await self.parse_report()
        await self.disconnect()

    async def get_action(self) -> None:
        for rule in self.rules:
            if rule.check_rule(self.event.raw_text):
                method = getattr(self, rule.action, None)
                if method:
                    try:
                        await method(**rule.parameters)
                    except ConnectionError:
                        await self.event.client.connect()
                        await method(**rule.parameters)

    async def parse_report(self) -> list:
        if not self.event.message.media:
            return
        report_data = await self.event.message.download_media(file=bytes)
        try:
            report_content = report_data.decode("utf-8")
        except Exception:
            print(traceback.format_exc())
            return

        soup = BeautifulSoup(report_content, "html.parser")

        for card in soup.find_all("div", class_="db"):
            _obj = dict()
            for row in card.find_all("div", class_="row"):
                _obj[row.find("div", class_="row_left").string] = row.find("div", class_="row_right").string
            self._result.append(_obj.copy())
        if not self._result:
            self._result.append({"message": "no data"})

    def message_to_dict(self) -> dict:
        res = dict()
        for e in self.event.message.message.split("\n"):
            s = re.search(r"[0-9a-zA-Zа-яА-Я:]+\s[0-9a-zA-Zа-яА-Я]+", e)
            if not s:
                continue
            ss = s.group().split(":")
            if len(ss) < 2:
                continue
            if not ss[1]:
                continue
            res[ss[0]] = ss[1]
        return res

    async def handler(self, event) -> None:
        self.event = event
        await self.get_action()
