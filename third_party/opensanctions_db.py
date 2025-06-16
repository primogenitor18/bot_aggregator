from typing import Tuple

from neo4j import AsyncGraphDatabase


class OpensanctionsDbRequest:
    def __init__(self, url: str, username: str, password: str) -> None:
        self.driver = AsyncGraphDatabase.driver(url, auth=(username, password))

    def _name_search(self, fts: str, *args, **kwargs) -> str:
        return "toLower(p.name) CONTAINS toLower($fts)"

    def _pasport_search(self, fts: str, *args, **kwargs) -> str:
        return "p.passportNumber = $fts OR toLower(p.passportNumber) = toLower($fts)"

    def _inn_search(self, fts: str, *args, **kwargs) -> str:
        return "p.innCode = $fts OR toLower(p.innCode) = toLower($fts)"

    def _snils_search(self, fts: str, *args, **kwargs) -> str:
        return "p.vatCode = $fts OR toLower(p.vatCode) = toLower($fts)"

    def _ogrn_search(self, fts: str, *args, **kwargs) -> str:
        return (
            "p.registrationNumber = $fts OR toLower(p.registrationNumber) = toLower($fts)"
        )

    def _fts_search(self, fts: str, *args, **kwargs) -> str:
        return "toLower(p.alias) CONTAINS toLower($fts)"

    async def search(
        self, fts: str, search_type: str = "", *args, **kwargs
    ) -> Tuple[int, dict]:
        method = getattr(self, f"_{search_type}_search", self._fts_search)
        fts_query = method(fts=fts)
        query = "MATCH (p:Person) WHERE " + fts_query + " RETURN p LIMIT $limit"
        async with self.driver.session() as session:
            result = await session.run(query, fts=fts, limit=50)
            records = await result.data()
        return 200, {"items": [{k: v for k, v in item["p"].items()} for item in records]}
