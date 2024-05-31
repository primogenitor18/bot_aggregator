import uuid

from typing import List, Tuple
from types import MappingProxyType

from sqlalchemy.future import select

from models.session import AsyncSession
from models.models import Provider

from third_party.quick_osint import QuickOsintRequest


class ProviderManager:
    def __init__(self, name: str, s: AsyncSession):
        self.name = name
        self.session = s
        self.provider = None

    async def get_provider(self) -> Provider:
        self.provider = (
            await self.session.execute(
                select(Provider).filter(Provider.name == self.name)
            )
        ).scalars().first()
        return self.provider

    async def create_provider(self, auth_token: str) -> Provider:
        self.provider = Provider(name=self.name, auth_token=auth_token)
        self.session.add(self.provider)
        await self.session.flush()
        await self.session.refresh(self.provider)
        return self.provider

    @classmethod
    async def constructor(cls, name: str, s: AsyncSession) -> "ProviderManager":
        obj = cls(name, s)
        await obj.get_provider()
        return obj

    async def update_auth(self, auth_token: str):
        if not self.provider:
            await self.create_provider(auth_token)
        else:
            self.provider.auth_token = auth_token
        await self.session.commit()

    @classmethod
    async def get_providers(cls, s: AsyncSession) -> List[Provider]:
        providers = (
            await s.execute(select(Provider))
        ).scalars().all()
        return providers

    async def get_quickosint_user_info(self) -> Tuple[int, dict]:
        await self.get_provider()
        obj = QuickOsintRequest(
            "https://quickosintapi.com/api/v1/identity/userinfo",
            headers=MappingProxyType(
                {
                    "Authorization": f"Bearer {self.provider.auth_token}",
                    "X-ClientId": uuid.uuid4().hex,
                }
            ),
        )
        return await obj.get_user_info()
