import uuid
import urllib.parse
from typing import Optional, Tuple

from sqlalchemy.future import select

from models.session import get_session, AsyncSession
from models.models import Provider

from third_party.quick_osint import QuickOsintRequest


class SearchManager:
    def __init__(self, s: AsyncSession):
        self.session = s

    async def get_obj_quickosintrequest(self, fts: str) -> Optional[QuickOsintRequest]:
        provider = (
            await self.session.execute(
                select(Provider).filter(Provider.name == "quickosint")
            )
        ).scalars().first()
        if not provider:
            return None
        return QuickOsintRequest(
            url="https://quickosintapi.com/api/v1/search/detail/{query}",
            path_params={"query": urllib.parse.quote(fts)},
            headers={
                "Authorization": f"Bearer {provider.auth_token}",
                "X-ClientId": uuid.uuid4().hex,
            },
        )

    async def quickosintrequest(self, fts: str) -> Tuple[dict, bool]:
        res = dict()
        obj = await self.get_obj_quickosintrequest(fts)
        if not obj:
            return res, False
        st, res = await obj.request("get")
        if st >= 200 and st < 300:
            return res, True
        return res, False
