import uuid
import urllib.parse
from typing import Optional, Tuple, Union
from types import MappingProxyType

from sqlalchemy.future import select

from models.session import AsyncSession
from models.models import Provider, User
from models.base import AnonymousUser

from third_party.quick_osint import QuickOsintRequest
from third_party.himera_search import HimeraSearchRequest


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

    async def search(
        self,
        fts: str,
        provider: str = "quickosint",
        country: str = "RU",
        search_type: str = "name",
    ) -> Tuple[dict, bool]:
        method = getattr(self, f"{provider}request")
        return await method(fts=fts, country=country, search_type=search_type)
