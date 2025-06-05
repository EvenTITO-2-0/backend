from typing import Annotated
from uuid import UUID

from fastapi import Depends

from app.authorization.caller_id_dep import CallerIdDep
from app.repository.payments_repository import PaymentsRepository
from app.repository.provider_account_repository import ProviderAccountRepository
from app.repository.events_repository import EventsRepository
from app.repository.repository import get_repository
from app.services.event_payments.event_payments_service import EventPaymentsService
from app.services.storage.event_inscription_storage_service_dep import EventInscriptionStorageServiceDep


class EventPaymentsServiceChecker:
    async def __call__(
        self,
        event_id: UUID,
        caller_id: CallerIdDep,
        storage_service: EventInscriptionStorageServiceDep,
        payments_repository: Annotated[PaymentsRepository, Depends(get_repository(PaymentsRepository))],
        provider_account_repository: Annotated[ProviderAccountRepository, Depends(get_repository(ProviderAccountRepository))],
        events_repository: Annotated[EventsRepository, Depends(get_repository(EventsRepository))],
    ) -> EventPaymentsService:
        return EventPaymentsService(
            storage_service,
            payments_repository,
            provider_account_repository,
            events_repository,
            event_id,
            caller_id,
        )


event_payments_checker = EventPaymentsServiceChecker()
EventPaymentsServiceDep = Annotated[EventPaymentsService, Depends(event_payments_checker)]
