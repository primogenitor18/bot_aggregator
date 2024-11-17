import re
import aiohttp
import urllib.parse
from typing import Optional, Tuple
from types import MappingProxyType

from third_party.base import ThirdPartyRequest


class InfoTrackPeopleRequest(ThirdPartyRequest):
    def __init__(
        self,
        url: str = "https://infotrackpeople.com/public-api/data/search",
        path_params: MappingProxyType = MappingProxyType({}),
        headers: MappingProxyType = MappingProxyType({}),
        cookies: MappingProxyType = MappingProxyType({}),
        **kwargs,
    ):
        self.url = url
        super().__init__(url, path_params, headers)
        self.headers["Content-Type"] = "application/json"

    async def search(
        self, fts: str, search_type: str = "", country: str = "", *args, **kwargs
    ) -> Tuple[int, dict]:
        method = getattr(self, f"_{search_type}_search", self._fts_search)
        data = method(fts=fts, country=country)
        return await self.request("post", data=MappingProxyType({"searchOptions":[data]}))

    def _name_search(self, fts: str, *args, **kwargs) -> dict:
        return {"type": "name", "query": fts}
        
    def _phone_search(self, fts: str, *args, **kwargs) -> dict:
        return {"type": "phone", "query": fts}
    
    def _email_search(self, fts: str, *args, **kwargs) -> dict:
        return {"type": "email", "query": fts}
    
    def _pasport_search(self, fts: str, *args, **kwargs) -> dict:
        return {"type": "passport", "query": fts}
    
    def _inn_search(self, fts: str, *args, **kwargs) -> dict:
        return {"type": "inn", "query": fts}
    
    def _snils_search(self, fts: str, *args, **kwargs) -> dict:
        return {"type": "snils", "query": fts}
    
    def _address_search(self, fts: str, *args, **kwargs) -> dict:
        return {"type": "address", "query": fts}
    
    def _auto_search(self, fts: str, *args, **kwargs) -> dict:
        return {"type": "plate_number", "query": fts}
    
    def _fts_search(self, fts: str, *args, **kwargs) -> dict:
        return {"type": "full_text", "query": fts}
