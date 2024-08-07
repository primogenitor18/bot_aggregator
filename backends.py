import datetime

import jwt
from fastapi import Request
from sqladmin.authentication import AuthenticationBackend
from sqlalchemy import and_
from sqlalchemy.future import select

from models.session import get_session
from models.models import User
from models.base import DefaultRoles

from managers.auth.manager import AuthManager


class AdminAuthenticationBackend(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username, password = form["username"], form["password"]

        manager = AuthManager(username, password)
        async with get_session() as s:
            user = (
                await s.execute(
                    select(User)
                    .filter(
                        and_(
                            User.username == username,
                            User.role == DefaultRoles.admin.value,
                        )
                    )
                )
            ).scalars().first()
            if user:
                manager._user = user

        access_token, _, st = await manager.create_access_refresh_token()
        if not st:
            return False

        request.session.update({"token": access_token})

        return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")

        if not token:
            return False

        try:
            code, reason, user_info = await AuthManager.check_token(token=token)
        except Exception:
            return False
        else:
            if user_info.is_anonymous or user_info.role != DefaultRoles.admin.value:
                return False
        return True
