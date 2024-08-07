from typing import Tuple

from third_party.base import ThirdPartyRequest


class AlephRequest(ThirdPartyRequest):
    async def search(
        self, fts: str, search_type: str = "", *args, **kwargs
    ) -> Tuple[int, dict]:
        params = {"q": fts, "limit": 50, "offset": 0}
        if search_type == "ogrn":
            params["filter:schemata"] = "Company"
        else:
            params["filter:schemata"] = "Person"
        return await self.request("get", data=params)
