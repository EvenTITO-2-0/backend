# backend/app/services/provider/provider_service_dep.py
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Path

from app.repository.events_repository import EventsRepository
from app.repository.provider_account_repository import ProviderAccountRepository
from app.repository.repository import get_repository
from app.services.provider.provider_service import ProviderService


class ProviderServiceChecker:
    async def __call__(
        self,
        event_id: Annotated[UUID, Path(...)],
        provider_account_repository: Annotated[
            ProviderAccountRepository, Depends(get_repository(ProviderAccountRepository))
        ],
        events_repository: Annotated[EventsRepository, Depends(get_repository(EventsRepository))],
    ) -> ProviderService:
        return ProviderService(provider_account_repository, events_repository, event_id)


provider_service_checker = ProviderServiceChecker()
ProviderServiceDep = Annotated[ProviderService, Depends(provider_service_checker)]
