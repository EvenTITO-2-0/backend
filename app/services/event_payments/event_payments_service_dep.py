from typing import Annotated
from uuid import UUID

from fastapi import Depends

from app.authorization.caller_id_dep import CallerIdDep
from app.repository.payments_repository import PaymentsRepository
from app.repository.repository import get_repository
from app.services.event_payments.event_payments_service import EventPaymentsService
from app.services.storage.event_inscription_storage_service_dep import EventInscriptionStorageServiceDep


class EventPaymentsServiceChecker:
    async def __call__(
        self,
        event_id: UUID,
        caller_id: CallerIdDep,
        storage_service: EventInscriptionStorageServiceDep,
        payments_repository: PaymentsRepository = Depends(get_repository(PaymentsRepository)),
    ) -> EventPaymentsService:
        return EventPaymentsService(storage_service, payments_repository, event_id, caller_id)


event_payments_checker = EventPaymentsServiceChecker()
EventPaymentsServiceDep = Annotated[EventPaymentsService, Depends(event_payments_checker)]
