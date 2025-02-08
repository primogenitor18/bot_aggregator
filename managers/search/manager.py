import uuid
import urllib.parse
import json
from typing import Optional, Tuple, Union
from types import MappingProxyType
from bs4 import BeautifulSoup

from fastapi import BackgroundTasks

from sqlalchemy.future import select

from models.session import AsyncSession
from models.models import Provider, User
from models.base import AnonymousUser

from third_party.quick_osint import QuickOsintRequest
from third_party.himera_search import HimeraSearchRequest
from third_party.revengee import RevengeeRequest
from third_party.aleph import AlephRequest
from third_party.infotrackpeople import InfoTrackPeopleRequest
from third_party.osintkit import OsintKitRequest

from tasks.tg_bot_parse import run_bot_parsing

from config import USE_TELETHON

from base_obj import send_socket_event
from websocket.consts import SocketEvent, SocketAction
from managers.search.tg_bots.poisk_cheloveka_telefonubot import PoiskChelovekaTelefonuBot
from managers.search.tg_bots.orakulbot import OrakulBot


class SearchManager:
    def __init__(
        self, s: AsyncSession, user: Union[User, AnonymousUser] = AnonymousUser()
    ):
        self.session = s
        self.user = user

    async def _get_provider_info(self, provider: str) -> Optional[Provider]:
        return (
            await self.session.execute(
                select(Provider)
                .filter(
                    Provider.name == provider,
                    Provider.accessed_role <= self.user.role,
                )
            )
        ).scalars().first()

    async def get_obj_quickosintrequest(self, fts: str) -> Optional[QuickOsintRequest]:
        provider = await self._get_provider_info("quickosint")
        if not provider:
            return None
        return QuickOsintRequest(
            headers=MappingProxyType(
                {
                    "Authorization": f"Bearer {provider.auth_token}",
                    "X-ClientId": uuid.uuid4().hex,
                }
            ),
        )

    async def quickosintrequest(
        self, fts: str, country: str, search_type: str, *args, **kwargs
    ) -> Tuple[dict, bool]:
        res = dict()
        obj = await self.get_obj_quickosintrequest(fts)
        if not obj:
            return res, False
        st, res = await obj.search(fts, search_type, country)
        if st >= 200 and st < 300:
            return res, True
        return {}, False

    async def get_obj_himerasearchrequest(self, fts: str) -> Optional[HimeraSearchRequest]:
        provider = await self._get_provider_info("himerasearch")
        if not provider:
            return None
        return HimeraSearchRequest(provider.auth_token)

    async def himerasearchrequest(
        self, fts: str, search_type: str, *args, **kwargs
    ) -> Tuple[dict, bool]:
        res = {"items": []}
        obj = await self.get_obj_himerasearchrequest(fts)
        if not obj:
            return res, False
        st, search_res = await obj.search(fts, search_type)
        _items = search_res.get(search_type, {}).get("data", {})
        if isinstance(_items, dict):
            _items = list(_items.values())
        res["items"] = _items
        return res, True

    def _parse_revengee_response(self, html_doc: str) -> list:
        if not html_doc:
            return list()
        soup = BeautifulSoup(html_doc, "html.parser")
        res = list()
        tbody = soup.tbody
        if not tbody:
            return res
        for i, row in enumerate(tbody.find_all("tr", class_="search-result")):
            columns = row.find_all("td")
            link = columns[1].find("a")
            _item = {
                "link": "https://reveng.ee{}".format(link.get("href")) if link else None
            }
            person_info = {"Source": columns[-2].get_text().replace("\n", "")}
            for r in columns[2].find_all("tr"):
                cs = r.find_all("td")
                person_info[cs[0].get_text().replace("\n", "")] = cs[1].get_text().replace("\n", "")
            _item.update(person_info)
            res.append(_item.copy())
        return res

    async def get_obj_revengeerequest(self, fts: str) -> RevengeeRequest:
        return RevengeeRequest()

    async def revengeerequest(self, fts: str, *args, **kwargs) -> Tuple[dict, bool]:
        obj = await self.get_obj_revengeerequest(fts)
        st, search_res = await obj.search(fts)
        return {"items": self._parse_revengee_response(search_res.get("response", ""))}, True

    async def poiskchelovekatelefonubotrequest(
        self,
        fts: str,
        search_type: str,
        socket_id: int,
        user_id: int,
        background_tasks: Optional[BackgroundTasks] = None,
        *args,
        **kwargs,
    ) -> Tuple[dict, bool]:
        if not socket_id or not user_id or not background_tasks or not USE_TELETHON:
            return {"items": [{"response": "No data"}]}, True
        #  background_tasks.add_task(run_bot_parsing, fts, search_type, socket_id, user_id)
        await send_socket_event(
            redis_pubsub_con=kwargs["redis_connection"],
            s=self.session,
            data={
                "event_type": SocketEvent.tg_bot_parse_result.value,
                "name": "",
                "data": list(),
                "task_data": {
                    "action": "search",
                    "target": PoiskChelovekaTelefonuBot._name,
                    "kwargs": {"fts": fts, "search_type": search_type},
                }
            },
            target_sockets=[socket_id],
            accept_users=[user_id],
            action=SocketAction.task,
        )
        return {"items": [{"response": "Search in progress..."}]}, True

    async def orakulbotrequest(
        self,
        fts: str,
        search_type: str,
        socket_id: int,
        user_id: int,
        background_tasks: Optional[BackgroundTasks] = None,
        *args,
        **kwargs,
    ) -> Tuple[dict, bool]:
        if not socket_id or not user_id or not background_tasks or not USE_TELETHON:
            return {"items": [{"response": "No data"}]}, True
        #  background_tasks.add_task(run_bot_parsing, fts, search_type, socket_id, user_id)
        await send_socket_event(
            redis_pubsub_con=kwargs["redis_connection"],
            s=self.session,
            data={
                "event_type": SocketEvent.tg_bot_parse_result.value,
                "name": "",
                "data": list(),
                "task_data": {
                    "action": "search",
                    "target": OrakulBot._name,
                    "kwargs": {"fts": fts, "search_type": search_type},
                }
            },
            target_sockets=[socket_id],
            accept_users=[user_id],
            action=SocketAction.task,
        )
        return {"items": [{"response": "Search in progress..."}]}, True

    async def get_obj_alephrequest(self, fts: str) -> Optional[AlephRequest]:
        provider = await self._get_provider_info("aleph")
        if not provider:
            return None
        return AlephRequest(
            url="https://aleph.occrp.org/api/2/entities",
            headers=MappingProxyType({"Authorization": f"ApiKey {provider.auth_token}"}),
        )

    def _parse_aleph_response(self, req: dict) -> list:
        res = list()
        for obj in req.get("results", []):
            _prepared_obj = dict()
            for k, v in obj["properties"].items():
                if isinstance(v, list):
                    v = "; ".join([str(i) for i in v])
                _prepared_obj[k] = v
            _prepared_obj["collection_summary"] = obj["collection"]["summary"].replace("\n", "")
            _prepared_obj["collection_summary"] = _prepared_obj["collection_summary"].split("-")
            res.append(_prepared_obj.copy())
        return res

    async def alephrequest(
        self, fts: str, search_type: str, *args, **kwargs
    ) -> Tuple[dict, bool]:
        res = dict()
        obj = await self.get_obj_alephrequest(fts)
        if not obj:
            return res, False
        st, res = await obj.search(fts, search_type)
        if st >= 200 and st < 300:
            return {"items": self._parse_aleph_response(res)}, True
        return {}, False

    async def get_obj_infotrackpeoplerequest(self, fts: str) -> Optional[InfoTrackPeopleRequest]:
        provider = await self._get_provider_info("infotrackpeople")
        if not provider:
            return None
        return InfoTrackPeopleRequest(headers=MappingProxyType({"x-api-key": f"{provider.auth_token}"}))

    def _parse_infotrackpeople_response(self, req: dict) -> list:
        res = list()
        for base, obj in req.get("unique", {}).items():
            if not obj:
                continue
            if isinstance(obj[0], dict):
                obj = "\n".join(
                    [
                        ",".join(f"{k}: {v}" for k, v in it.items())
                        for it in obj
                    ]
                )
            else:
                obj = "\n".join([it for it in obj])
            res.append({base: obj})
        return res

    async def infotrackpeoplerequest(
        self, fts: str, country: str, search_type: str, *args, **kwargs
    ) -> Tuple[dict, bool]:
        res = dict()
        obj = await self.get_obj_infotrackpeoplerequest(fts)
        if not obj:
            return res, False
        st, res = await obj.search(fts, search_type, country)
        if st >= 200 and st < 300:
            return {"items": self._parse_infotrackpeople_response(res)}, True
        return {}, False

    async def get_obj_osintkitrequest(self, fts: str) -> Optional[OsintKitRequest]:
        provider = await self._get_provider_info("osintkit")
        if not provider:
            return None
        return OsintKitRequest(headers=MappingProxyType({"X-API-KEY": provider.auth_token}))

    async def osintkitrequest(
        self, fts: str, country: str, search_type: str, *args, **kwargs
    ) -> Tuple[dict, bool]:
        res = dict()
        obj = await self.get_obj_osintkitrequest(fts)
        if not obj:
            return res, False
        st, res = await obj.search(fts, search_type, country)
        if st >= 200 and st < 300:
            data = {"items": []}
            for obj in res.get("data", []):
                _obj = dict()
                for k, v in obj.items():
                    if isinstance(v, dict):
                        _obj[k] = json.dumps(v)
                    elif isinstance(v, list):
                        _obj[k] = "; ".join(str(i) for i in v)
                    else:
                        _obj[k] = v
                data["items"].append(_obj.copy())
            return data, True
        return {}, False

    async def search(
        self,
        fts: str,
        provider: str = "quickosint",
        country: str = "RU",
        search_type: str = "name",
        socket_id: int = 0,
        user_id: int = 0,
        background_tasks: Optional[BackgroundTasks] = None,
        *args,
        **kwargs,
    ) -> Tuple[dict, bool]:
        method = getattr(self, f"{provider}request")
        return await method(
            fts=fts,
            country=country,
            search_type=search_type,
            socket_id=socket_id,
            user_id=user_id,
            background_tasks=background_tasks,
            *args,
            **kwargs,
        )
