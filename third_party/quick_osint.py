import re
import aiohttp
import urllib.parse
from typing import Optional, Tuple
from types import MappingProxyType

from third_party.base import ThirdPartyRequest


class QuickOsintRequest(ThirdPartyRequest):
    def __init__(
        self,
        url: str = "https://quickosintapi.com/api/v1/search/detail/{query}",
        path_params: MappingProxyType = MappingProxyType({}),
        headers: MappingProxyType = MappingProxyType({}),
        cookies: MappingProxyType = MappingProxyType({}),
        **kwargs,
    ):
        self.base_url = url
        super().__init__(url, path_params, headers)
        self.cookies: dict = dict(cookies)

    async def request(
        self,
        method: str,
        data: MappingProxyType = MappingProxyType({}),
    ) -> Tuple[int, dict]:
        async with aiohttp.ClientSession(
            headers=self.headers,
            cookies=self.cookies,
        ) as client:
            request_method = getattr(self, method)
            return await request_method(client=client, data=data)

    def _password_search(self, fts: str, *args, **kwargs) -> str:
        return f"pas {fts}"

    def _pasport_search(self, fts: str, *args, **kwargs) -> str:
        return f"pasp {fts}"

    def _name_search(self, fts: str, country: str, *args, **kwargs) -> str:
        return f"{country}|{fts}"

    def _inn_search(self, fts: str, country: str, *args, **kwargs) -> str:
        return f"inn|{country} {fts}"

    def _phone_search(self, fts: str, *args, **kwargs) -> str:
        if re.match(r"[0-9]+", fts):
            return re.match(r"[0-9]+", fts).group()
        return ""

    def _fts_search(self, fts: str, *args, **kwargs) -> str:
        return fts

    async def search(
        self, fts: str, search_type: str = "", country: str = "", *args, **kwargs
    ) -> Tuple[int, dict]:
        method = getattr(self, f"_{search_type}_search", self._fts_search)
        fts = method(fts=fts, country=country)
        self.url = self._build_url(
            self.base_url, {"query": urllib.parse.quote(fts)}
        )
        return await self.request("get")

    async def get_user_info(self) -> Tuple[int, dict]:
        try:
            st, res = await self.request("get")
        except Exception:
            return 500, {}
        else:
            return st, res
