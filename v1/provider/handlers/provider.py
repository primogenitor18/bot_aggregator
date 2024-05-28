from typing import Optional, Any, Union, List

from fastapi import (
    APIRouter,
    status,
    Response,
    Header,
    Request,
    Depends,
)

from v1.provider.models.request import ProviderRequest
from v1.provider.models.response import ProviderResponse

from response_models import Error40xResponse

from managers.providers.manager import ProviderManager
from managers.permissions.permissions import check_admin

from models.session import get_session
from models.models import User


router = APIRouter(
    prefix="/v1/provider",
    tags=["provider"]
)


@router.post(
    "/manage",
    responses={
        200: {
            "model": ProviderResponse,
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
    provider: ProviderRequest,
    response: Response,
    user: User = Depends(check_admin),
    status_code: Optional[Any] = Header(status.HTTP_200_OK, description="internal usage, not used by client"),
) -> Union[ProviderResponse, Error40xResponse]:
    async with get_session() as s:
        manager = await ProviderManager.constructor(provider.name, s)
        await manager.update_auth(provider.auth_token)
        return ProviderResponse(
            name=manager.provider.name, auth_token=manager.provider.auth_token
        )


@router.get(
    "/list",
    responses={
        200: {
            "model": List[ProviderResponse],
        },
        401: {
            "model": Error40xResponse,
            "description": "wrong auth token",
        },
    },
    summary="authentication",
)
async def providers_list_method(
    request: Request,
    response: Response,
    user: User = Depends(check_admin),
    status_code: Optional[Any] = Header(status.HTTP_200_OK, description="internal usage, not used by client"),
) -> Union[List[ProviderResponse], Error40xResponse]:
    async with get_session() as s:
        providers = await ProviderManager.get_providers(s)
        return [
            ProviderResponse(
                name=p.name, auth_token=p.auth_token
            )
            for p in providers
        ]
