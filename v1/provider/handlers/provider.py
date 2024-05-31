from typing import Optional, Any, Union, List

from fastapi import (
    APIRouter,
    status,
    Response,
    Header,
    Request,
    Depends,
    Query,
)

from v1.provider.models.request import ProviderRequest
from v1.provider.models.response import ProviderResponse, ProviderFullResponse, ProviderUserInfoResponse

from response_models import Error40xResponse

from managers.providers.manager import ProviderManager
from managers.permissions.permissions import check_admin, check_auth

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
        manager = await ProviderManager.constructor(provider.name, s, user)
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
    user: User = Depends(check_auth),
    status_code: Optional[Any] = Header(status.HTTP_200_OK, description="internal usage, not used by client"),
) -> Union[List[ProviderResponse], Error40xResponse]:
    async with get_session() as s:
        providers = await ProviderManager("", s, user).get_providers(s)
        return [
            ProviderResponse(name=p.name)
            for p in providers
        ]


@router.get(
    "/full/list",
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
async def providers_full_list_method(
    request: Request,
    response: Response,
    user: User = Depends(check_admin),
    status_code: Optional[Any] = Header(status.HTTP_200_OK, description="internal usage, not used by client"),
) -> Union[List[ProviderResponse], Error40xResponse]:
    async with get_session() as s:
        providers = await ProviderManager("", s, user).get_providers(s)
        return [
            ProviderFullResponse(
                name=p.name, auth_token=p.auth_token
            )
            for p in providers
        ]


@router.get(
    "/get_info",
    responses={
        200: {
            "model": ProviderUserInfoResponse,
        },
        401: {
            "model": Error40xResponse,
            "description": "wrong auth token",
        },
    },
    summary="authentication",
)
async def provider_info_method(
    request: Request,
    response: Response,
    user: User = Depends(check_auth),
    provider: str = Query(""),
    status_code: Optional[Any] = Header(status.HTTP_200_OK, description="internal usage, not used by client"),
) -> Union[ProviderUserInfoResponse, Error40xResponse]:
    if not provider:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return Error40xResponse(reason="provider not defined")
    async with get_session() as s:
        manager = ProviderManager(provider, s, user)
        if hasattr(manager, f"get_{provider}_user_info"):
            method = getattr(manager, f"get_{provider}_user_info")
            st, res = await method()
            if st == 200:
                info = res.get("items", [])
                if info:
                    return ProviderUserInfoResponse(
                        query_count_all=info[0].get("queryCountAll", 0),
                        query_count_api_limit=info[0].get("queryCountApiLimit", 0)
                    )
    response.status_code = status.HTTP_403_FORBIDDEN
    return Error40xResponse(reason="info not implemented for provider")
