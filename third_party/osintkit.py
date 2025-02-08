import aiohttp
from typing import Tuple
from types import MappingProxyType

from third_party.base import ThirdPartyRequest


class OsintKitRequest(ThirdPartyRequest):
    def __init__(
        self,
        url: str = "https://api.osintkit.net/v1/search/",
        path_params: MappingProxyType = MappingProxyType({}),
        headers: MappingProxyType = MappingProxyType({}),
        **kwargs,
    ):
        self.base_url = url
        super().__init__(url, path_params, headers)

    def _password_search(self, fts: str, *args, **kwargs) -> dict:
        return {"filters[logins.password]": fts}

    def _name_search(self, fts: str, *args, **kwargs) -> dict:
        return {"filters[names]": fts}

    def _phone_search(self, fts: str, *args, **kwargs) -> dict:
        return {"filters[phones]": fts}

    def _email_search(self, fts: str, *args, **kwargs) -> dict:
        return {"filters[emails]": fts}

    def _pasport_search(self, fts: str, *args, **kwargs) -> dict:
        return {"filters[documents.passports.serial]": fts}

    def _inn_search(self, fts: str, *args, **kwargs) -> dict:
        return {"filters[inn]": fts}

    def _snils_search(self, fts: str, *args, **kwargs) -> dict:
        return {"filters[snils]": fts}

    def _address_search(self, fts: str, *args, **kwargs) -> dict:
        return {"filters[address]": fts}

    def _auto_search(self, fts: str, *args, **kwargs) -> dict:
        return {"filters[vehicles.plate_number]": fts}

    def _fts_search(self, fts: str, *args, **kwargs) -> str:
        return {"filters[names]": fts}

    async def search(
        self, fts: str, search_type: str = "", *args, **kwargs
    ) -> Tuple[int, dict]:
        method = getattr(self, f"_{search_type}_search", self._fts_search)
        fts = method(fts=fts)
        return await self.request("get", fts)

    async def get_user_info(self) -> Tuple[int, dict]:
        try:
            st, res = await self.request("get")
        except Exception:
            return 500, {}
        else:
            return st, res
