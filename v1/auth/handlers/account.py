from typing import Optional, Any, Union, List

from fastapi import (
    APIRouter,
    status,
    Response,
    Header,
    Request,
    Depends,
)

from v1.auth.models.response import AccountResponse

from response_models import Error40xResponse

from managers.permissions.permissions import check_auth

from models.session import get_session
from models.models import User


router = APIRouter(
    prefix="/v1/account",
    tags=["account"]
)


@router.get(
    "/info",
    responses={
        200: {
            "model": AccountResponse,
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
    response: Response,
    user: User = Depends(check_auth),
    status_code: Optional[Any] = Header(status.HTTP_200_OK, description="internal usage, not used by client"),
) -> Union[AccountResponse, Error40xResponse]:
    response = list()
    user_dict = user.as_dict()
    user_dict["role"] = user.role_str
    return AccountResponse.model_validate(user_dict)
