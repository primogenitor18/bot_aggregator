from typing import Optional, Any, Union

from fastapi import (
    APIRouter,
    status,
    Response,
    Header,
    Request,
)

from v1.auth.models.request import Auth, Refresh
from v1.auth.models.response import AuthResponse

from response_models import Error40xResponse

from managers.auth.manager import AuthManager


router = APIRouter(
    prefix="/v1/auth",
    tags=["auth"]
)


@router.post(
    "/login",
    responses={
        200: {
            "model": AuthResponse,
        },
        401: {
            "model": Error40xResponse,
            "description": "wrong auth token",
        },
    },
    summary="authentication",
)
async def auth_method(
    request: Request,
    auth: Auth,
    response: Response,
    status_code: Optional[Any] = Header(status.HTTP_200_OK, description="internal usage, not used by client"),
) -> Union[AuthResponse, Error40xResponse]:
    manager = AuthManager(auth.username, auth.password)
    access_token, refresh_token, st = await manager.create_access_refresh_token()
    if not st:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return Error40xResponse.parse_obj({"reason": "user was not found"})
    return AuthResponse(access_token=access_token, refresh_token=refresh_token)


@router.post(
    "/refresh",
    responses={
        200: {
            "model": AuthResponse,
        },
        401: {
            "model": Error40xResponse,
            "description": "wrong auth token",
        },
    },
    summary="authentication",
)
async def refresh_method(
    request: Request,
    refresh: Refresh,
    response: Response,
    status_code: Optional[Any] = Header(status.HTTP_200_OK, description="internal usage, not used by client"),
) -> Union[AuthResponse, Error40xResponse]:
    st_code, reason, user = await AuthManager.check_token(refresh.refresh_token)
    if user.is_anonymous:
        response.status_code = st_code
        return Error40xResponse.parse_obj({"reason": reason})
    manager = AuthManager(user.username, user.password)
    access_token, refresh_token, st = await manager.create_access_refresh_token()
    if not st:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return Error40xResponse.parse_obj({"reason": "user was not found"})
    return AuthResponse(access_token=access_token, refresh_token=refresh_token)
