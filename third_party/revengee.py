import aiohttp
import json
from typing import Tuple
from types import MappingProxyType

from third_party.base import ThirdPartyRequest


class RevengeeRequest(ThirdPartyRequest):
    def __init__(
        self,
        url: str = "https://reveng.ee/",
        path_params: MappingProxyType = MappingProxyType({}),
        headers: MappingProxyType = MappingProxyType({}),
        cookies: MappingProxyType = MappingProxyType({}),
        **kwargs,
    ):
        self.base_url = url
        super().__init__(url, path_params, headers)
        self.session_id = ""

    async def _get_delete(
        self,
        client: aiohttp.ClientSession,
        data: MappingProxyType = MappingProxyType({}),
        method: str = "get",
    ) -> Tuple[int, dict]:
        async with getattr(client, method)(
            self.url,
            params=dict(data),
        ) as resp:
            status_code = resp.status
            response = {"response": await resp.text()}
            return status_code, response

    async def _post_put_patch(
        self,
        client: aiohttp.ClientSession,
        data: MappingProxyType = MappingProxyType({}),
        method: str = "post",
    ) -> Tuple[int, dict]:
        async with getattr(client, method)(
            self.url,
            data=json.dumps(dict(data)),
        ) as resp:
            status_code = resp.status
            response = {"response": await resp.text()}
            return status_code, response

    async def get_session(self) -> None:
        async with aiohttp.ClientSession() as client:
            async with client.get(self.url) as resp:
                print("Headers: ", resp.headers.get("Set-Cookie"))
                self.session_id = resp.headers.get("Set-Cookie")

    async def search(
        self, fts: str, *args, **kwargs
    ) -> Tuple[int, dict]:
        await self.get_session()
        self.url = f"{self.base_url}search?q={fts}"
        st, res = await self.request("get")
        self.url = self.base_url
        return st, res
