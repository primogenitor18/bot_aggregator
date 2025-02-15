from typing import Tuple
from types import MappingProxyType

from third_party.base import ThirdPartyRequest


class KeyscoreRequest(ThirdPartyRequest):
    def __init__(
        self,
        url: str = "https://api.keysco.re/search",
        path_params: MappingProxyType = MappingProxyType({}),
        headers: MappingProxyType = MappingProxyType({}),
        **kwargs,
    ):
        self.base_url = url
        super().__init__(url, path_params, headers)

    def _password_search(self, fts: str, *args, **kwargs) -> str:
        return {
          "terms": [fts],
          "types": ["url"],
          "source": "xkeyscore",
          "wildcard": False,
        }

    def _password_search(self, fts: str, *args, **kwargs) -> str:
        return {
          "terms": [fts],
          "types": ["password"],
          "source": "xkeyscore",
          "wildcard": False,
        }

    def _fts_search(self, fts: str, *args, **kwargs) -> str:
        return {
          "terms": [fts],
          "types": ["email"],
          "source": "xkeyscore",
          "wildcard": False,
        }

    async def search(
        self, fts: str, search_type: str = "", *args, **kwargs
    ) -> Tuple[int, dict]:
        method = getattr(self, f"_{search_type}_search", self._fts_search)
        fts = method(fts=fts)
        return await self.request("post", fts)
