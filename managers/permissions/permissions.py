from fastapi import Request, HTTPException
from starlette import status

from sqlalchemy import and_, select

from models.session import get_session
from models.models import User
from models.base import DefaultRoles


async def check_auth(request: Request) -> User:
    if not request.user or request.user.is_anonymous:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You are not authenticated"
        )
    return request.user


async def check_admin(request: Request) -> User:
    await check_auth(request)
    if request.user.role != DefaultRoles.admin.value:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="You are not permitted"
        )
    return request.user
