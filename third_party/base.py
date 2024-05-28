import aiohttp
import json
from typing import Optional, Tuple
from types import MappingProxyType


class ThirdPartyRequest:
    def __init__(
        self,
        url: str,
        path_params: MappingProxyType = MappingProxyType({}),
        headers: MappingProxyType = MappingProxyType({}),
        **kwargs,
    ):
        self._url = self._build_url(url=url, path_params=dict(path_params))
        self.headers: dict = dict(headers)
        self.auth = None
        if kwargs.get("http_auth"):
            self.auth = aiohttp.BasicAuth(*kwargs.get("http_auth"))

    @property
    def url(self) -> str:
        return self._url

    @url.setter
    def url(self, value: str) -> None:
        self._url = value

    def _build_url(
        self,
        url: str,
        path_params: Optional[dict] = {},
    ) -> str:
        if not path_params:
            return url
        try:
            url = url.format(**path_params)
        except BaseException:
            pass
        finally:
            return url

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
            response = await resp.json()
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
            response = await resp.json()
            return status_code, response

    async def get(
        self,
        client: aiohttp.ClientSession,
        data: MappingProxyType = MappingProxyType({}),
    ) -> Tuple[int, dict]:
        return await self._get_delete(client=client, data=data, method="get")

    async def delete(
        self,
        client: aiohttp.ClientSession,
        data: MappingProxyType = MappingProxyType({}),
    ) -> Tuple[int, dict]:
        return await self._get_delete(client=client, data=data, method="delete")

    async def post(
        self,
        client: aiohttp.ClientSession,
        data: MappingProxyType = MappingProxyType({}),
    ) -> Tuple[int, dict]:
        return await self._post_put_patch(client=client, data=data, method="post")

    async def put(
        self,
        client: aiohttp.ClientSession,
        data: MappingProxyType = MappingProxyType({}),
    ) -> Tuple[int, dict]:
        return await self._post_put_patch(client=client, data=data, method="put")

    async def patch(
        self,
        client: aiohttp.ClientSession,
        data: MappingProxyType = MappingProxyType({}),
    ) -> Tuple[int, dict]:
        return await self._post_put_patch(client=client, data=data, method="patch")

    async def request(
        self,
        method: str,
        data: MappingProxyType = MappingProxyType({}),
    ) -> Tuple[int, dict]:
        async with aiohttp.ClientSession(
            headers=self.headers,
            auth=self.auth,
        ) as client:
            request_method = getattr(self, method)
            return await request_method(client=client, data=data)
