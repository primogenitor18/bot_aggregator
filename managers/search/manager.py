import uuid
import urllib.parse
from typing import Optional, Tuple
from types import MappingProxyType

from sqlalchemy.future import select

from models.session import get_session, AsyncSession
from models.models import Provider

from third_party.quick_osint import QuickOsintRequest
from third_party.himera_search import HimeraSearchRequest


class SearchManager:
    def __init__(self, s: AsyncSession):
        self.session = s

    async def _get_provider_info(self, provider: str) -> Optional[Provider]:
        return (
            await self.session.execute(
                select(Provider).filter(Provider.name == provider)
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
        for k, v in search_res.items():
            _sr_data = v.get("data", [])
            if not _sr_data:
                continue
            item_body = _sr_data[0]
            item_body["report"] = v.get("url")
            res["items"].append(item_body)
        return res, True

    async def search(
        self,
        fts: str,
        provider: str = "quickosint",
        country: str = "RU",
        search_type: str = "name",
    ) -> Tuple[dict, bool]:
        method = getattr(self, f"{provider}request")
        return await method(fts, country, search_type)
