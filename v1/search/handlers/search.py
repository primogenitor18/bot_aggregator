from typing import Optional, Any, Union, List

from fastapi import (
    APIRouter,
    status,
    Response,
    Header,
    Request,
    Depends,
)

from v1.search.models.request import SearchRequest
from v1.search.models.response import SearchResponse

from response_models import Error40xResponse

from managers.search.manager import SearchManager
from managers.permissions.permissions import check_auth

from models.session import get_session
from models.models import User


router = APIRouter(
    prefix="/v1/search",
    tags=["search"]
)


@router.post(
    "/fts",
    responses={
        200: {
            "model": List[SearchResponse],
        },
        401: {
            "model": Error40xResponse,
            "description": "wrong auth token",
        },
    },
    summary="authentication",
)
async def provider_manage_method(
    request: Request,
    search: SearchRequest,
    response: Response,
    user: User = Depends(check_auth),
    status_code: Optional[Any] = Header(status.HTTP_200_OK, description="internal usage, not used by client"),
) -> Union[SearchResponse, Error40xResponse]:
    async with get_session() as s:
        manager = SearchManager(s, user)
        res, st = await manager.search(
            search.fts, search.provider, search.country, search.search_type
        )
        return SearchResponse(
            provider_name=search.provider,
            data=[i for i in res.get("items", []) if isinstance(i, dict)],
        )
