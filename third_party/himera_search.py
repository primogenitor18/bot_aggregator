import re
import aiohttp
from typing import Optional, Tuple
from types import MappingProxyType

from third_party.base import ThirdPartyRequest


class HimeraSearchRequest(ThirdPartyRequest):
    _digits_search = ("phone", "passport", "inn", "snils")
    _letters_search = ("name_standart", "email", "avto", "vin")

    def __init__(
        self,
        api_key: str,
        url: str = "https://api.himera-search.info/2.0",
        path_params: MappingProxyType = MappingProxyType({}),
        headers: MappingProxyType = MappingProxyType({}),
        **kwargs,
    ):
        self.api_key = api_key
        self.base_url = url
        _headers: dict = dict(headers)
        _headers["Content-Type"] = "application/x-www-form-urlencoded"
        super().__init__(url, path_params, MappingProxyType(_headers))

    async def _post_put_patch(
        self,
        client: aiohttp.ClientSession,
        data: MappingProxyType = MappingProxyType({}),
        method: str = "post",
    ) -> Tuple[int, dict]:
        form_data = aiohttp.FormData()
        form_data.add_field("key", self.api_key)
        for k, v in data.items():
            form_data.add_field(k, v)
        async with getattr(client, method)(
            self.url,
            data=form_data,
        ) as resp:
            status_code = resp.status
            response = await resp.json()
            return status_code, response

    async def _name_search(self, fts: str, *args, **kwargs) -> Tuple[int, dict]:
        fts_arr = fts.split(" ")
        _keys_arr = [
            "firstname", "lastname", "middlename"
        ]
        data = dict()
        for i, k in enumerate(_keys_arr):
            if i + 1 > len(fts_arr):
                break
            data[k] = fts_arr[i]
        self.url = f"{self.base_url}/name_standart"
        st, res = await self.request("post", MappingProxyType(data))
        self.url = self.base_url
        return st, res

    async def _inn_search(self, fts: str, *args, **kwargs) -> Tuple[int, dict]:
        st = 200
        res = dict()
        for t in ["inn_fl", "inn"]:
            self.url = f"{self.base_url}/{t}"
            st, res[t] = await self.request(
                "post", MappingProxyType({t: fts}),
            )
            self.url = self.base_url
        return st, res

    async def _ogrn_search(self, fts: str, *args, **kwargs) -> Tuple[int, dict]:
        self.url = f"{self.base_url}/inn"
        st, res = await self.request(
            "post", MappingProxyType({"ogrn": fts}),
        )
        self.url = self.base_url
        return st, res

    async def _pasport_search(self, fts: str, *args, **kwargs) -> Tuple[int, dict]:
        self.url = f"{self.base_url}/passport"
        st, res = await self.request(
            "post", MappingProxyType({"passport": fts}),
        )
        self.url = self.base_url
        return st, res

    async def _key_search(self, key: str, fts: str, *args, **kwargs) -> Tuple[int, dict]:
        self.url = f"{self.base_url}/{key}"
        st, res = await self.request(
            "post", MappingProxyType({key: fts}),
        )
        self.url = self.base_url
        return st, res

    async def search(self, fts: str, search_type: str = "", *args, **kwargs) -> Tuple[int, dict]:
        st = 200
        res = dict()
        if search_type:
            methods_arr = (search_type,)
        else:
            methods_arr = self._letters_search
            if len(fts.split(" ")) == 1 and re.match(r"\+{0,1}[0-9]+", fts):
                fts = re.match(r"\+{0,1}[0-9]+", fts).group()
                methods_arr = self._digits_search
        for method_name in methods_arr:
            method = getattr(self, f"_{method_name}_search", self._key_search)
            st, res[method_name] = await method(fts=fts, key=method_name)
        return st, res
