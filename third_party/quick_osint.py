import aiohttp
from typing import Optional, Tuple
from types import MappingProxyType

from third_party.base import ThirdPartyRequest


class QuickOsintRequest(ThirdPartyRequest):
    def __init__(
        self,
        url: str,
        path_params: MappingProxyType = MappingProxyType({}),
        headers: MappingProxyType = MappingProxyType({}),
        cookies: MappingProxyType = MappingProxyType({}),
        **kwargs,
    ):
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
