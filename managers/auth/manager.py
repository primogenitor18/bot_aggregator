import datetime
import jwt
import re
import uuid

from typing import Optional, Tuple, Union

from fastapi import status

from sqlalchemy.future import select

from base_obj import password_hash, password_gen

from models.session import get_session
from models.models import User
from models.base import AnonymousUser, DefaultRoles

from config import ACCESS_TOKEN_LIFETIME, SERVER_SECRET, REFRESH_TOKEN_LIFETIME


class AuthManager:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self._user: Union[User, AnonymousUser] = AnonymousUser()

    @classmethod
    async def create_user(cls, username: str, password: str = "") -> Tuple[User, str]:
        if not cls.verify_password_strengh(password):
            password = password_gen()
        salt = uuid.uuid4().hex
        async with get_session() as s:
            user = User(
                username=username,
                password=f"{password_hash(password, salt)}${salt}",
                role=DefaultRoles.admin.value,
            )
            s.add(user)
            await s.flush()
            await s.refresh(user)
            await s.commit()
            return user, password

    @classmethod
    def verify_password_strengh(cls, password: str) -> bool:
        if not len(password) < 8:
            return False
        if not all(
            [
                re.search(r"[A-Z]+", password),
                re.search(r"[a-z]+", password),
                re.search(r"[0-9]+", password),
            ]
        ):
            return False
        return True

    async def get_user(self) -> Union[AnonymousUser, User]:
        if not self._user.is_anonymous:
            return self._user
        async with get_session() as s:
            user = (
                await s.execute(
                    select(User)
                    .filter(User.username == self.username)
                )
            ).scalars().first()
            if user:
                self._user = user
            return self._user

    def verify_password(self, user: User) -> bool:
        if self.password == user.password:
            return True
        try:
            pass_hash, salt = user.password.split("$")
        except ValueError:
            return False
        return password_hash(self.password, salt) == pass_hash

    def _create_token(self, lifetime: int) -> str:
        token_exp_date = datetime.datetime.now().timestamp() + lifetime
        return jwt.encode(
            {
                'user_id': self._user.id,
                'username': self._user.username,
                'password': self._user.password,
                'expiration_time': token_exp_date,
            },
            SERVER_SECRET,
            algorithm='HS256'
        )

    async def verify_user(self) -> bool:
        user = await self.get_user()
        if user.is_anonymous:
            return False
        if not self.verify_password(user):
            return False
        return True

    async def create_access_token(self) -> Tuple[str, bool]:
        st = await self.verify_user()
        if not st:
            return "", False
        access_token = self._create_token(ACCESS_TOKEN_LIFETIME)
        return access_token, True

    async def create_refresh_token(self) -> Tuple[str, bool]:
        st = await self.verify_user()
        if not st:
            return "", False
        refresh_token = self._create_token(REFRESH_TOKEN_LIFETIME)
        return refresh_token, True

    async def create_access_refresh_token(self) -> Tuple[str, str, bool]:
        st = await self.verify_user()
        if not st:
            return "", "", False
        access_token = self._create_token(ACCESS_TOKEN_LIFETIME)
        refresh_token = self._create_token(REFRESH_TOKEN_LIFETIME)
        return access_token, refresh_token, True

    @classmethod
    async def check_token(cls, token: str) -> Tuple[int, str, Union[AnonymousUser, User]]:
        try:
            token_info = jwt.decode(token, SERVER_SECRET, algorithms=['HS256'])
        except Exception as e:
            return status.HTTP_401_UNAUTHORIZED, 'wrong token type', AnonymousUser()
        else:
            user_info = AnonymousUser()
            async with get_session() as s:
                user_info = (
                    await s.execute(
                        select(User)
                        .filter(User.id == token_info['user_id'])
                    )
                ).scalars().first()
            if not user_info.is_anonymous:
                if user_info.password == token_info['password'] and \
                        token_info['expiration_time'] >= datetime.datetime.now().timestamp():
                    return status.HTTP_200_OK, 'user authenticated', user_info
                else:
                    return status.HTTP_401_UNAUTHORIZED, 'token expired', AnonymousUser()
            else:
                return status.HTTP_401_UNAUTHORIZED, 'no user', AnonymousUser()
