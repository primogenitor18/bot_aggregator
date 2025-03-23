from typing import Tuple
from types import MappingProxyType

from third_party.base import ThirdPartyRequest


class TeletypeRequest(ThirdPartyRequest):
    def __init__(
        self,
        url: str = "api.usersbox.ru/v1/search",
        path_params: MappingProxyType = MappingProxyType({}),
        headers: MappingProxyType = MappingProxyType({}),
        **kwargs,
    ):
        self.base_url = url
        super().__init__(url, path_params, headers)

    async def search(
        self, fts: str, search_type: str = "", *args, **kwargs
    ) -> Tuple[int, dict]:
        method = getattr(self, f"_{search_type}_search", self._fts_search)
        fts = method(fts=fts)
        return await self.request("get", {"q": fts})
