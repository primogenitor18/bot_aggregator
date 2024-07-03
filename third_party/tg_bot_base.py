import re
from dataclasses import dataclass, field
from collections import defaultdict

from typing import List, Optional, Type

from telethon import events
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
        self.result = dict()

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
        await button.click()

    async def send_message(self) -> None:
        await self.event.client.send_message(self.event.chat, self.fts)

    async def save_result(self) -> None:
        self.result = self.message_to_dict()
        await self.disconnect()

    async def get_action(self) -> None:
        for rule in self.rules:
            if rule.check_rule(self.event.raw_text):
                method = getattr(self, rule.action, None)
                if method:
                    await method(**rule.parameters)

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
