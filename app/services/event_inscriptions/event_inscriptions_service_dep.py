from typing import Annotated
from uuid import UUID

from fastapi import Depends

from app.authorization.caller_id_dep import CallerIdDep
from app.repository.inscriptions_repository import InscriptionsRepository
from app.repository.repository import get_repository
from app.services.event_inscriptions.event_inscriptions_service import EventInscriptionsService
from app.services.event_payments.event_payments_service_dep import EventPaymentsServiceDep
from app.services.events.events_configuration_service_dep import EventsConfigurationServiceDep
from app.services.notifications.notifications_service_dep import EventsNotificationServiceDep
from app.services.storage.event_inscription_storage_service_dep import EventInscriptionStorageServiceDep


class EventInscriptionsServiceChecker:
    async def __call__(
            self,
            event_id: UUID,
            caller_id: CallerIdDep,
            event_notification_service: EventsNotificationServiceDep,
            event_configuration_service: EventsConfigurationServiceDep,
            event_payment_service: EventPaymentsServiceDep,
            storage_service: EventInscriptionStorageServiceDep,
            inscriptions_repository: Annotated[InscriptionsRepository, Depends(get_repository(InscriptionsRepository))],
    ) -> EventInscriptionsService:
        return EventInscriptionsService(
            event_configuration_service,
            event_payment_service,
            storage_service,
            inscriptions_repository,
            event_notification_service,
            event_id,
            caller_id
        )


event_inscriptions_checker = EventInscriptionsServiceChecker()
EventInscriptionsServiceDep = Annotated[EventInscriptionsService, Depends(event_inscriptions_checker)]
