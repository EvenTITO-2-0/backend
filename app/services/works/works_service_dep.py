from typing import Annotated
from uuid import UUID

from fastapi import Depends

from app.authorization.caller_id_dep import CallerIdDep
from app.authorization.user_id_dep import UserDep
from app.repository.repository import get_repository
from app.repository.works_repository import WorksRepository
from app.services.event_inscriptions.event_inscriptions_service_dep import EventInscriptionsServiceDep
from app.services.events.events_configuration_service_dep import EventsConfigurationServiceDep
from app.services.notifications.notifications_service_dep import EventsNotificationServiceDep
from app.services.works.works_service import WorksService


class Works:
    async def __call__(
        self,
        event_notification_service: EventsNotificationServiceDep,
        _: UserDep,
        caller_id: CallerIdDep,
        event_id: UUID,
        events_configuration_service: EventsConfigurationServiceDep,
        inscription_service: EventInscriptionsServiceDep,
        works_repository: WorksRepository = Depends(get_repository(WorksRepository)),
    ) -> WorksService:
        return WorksService(
            caller_id,
            event_id,
            events_configuration_service,
            event_notification_service,
            inscription_service,
            works_repository,
        )


auth_works_service = Works()
WorksServiceDep = Annotated[WorksService, Depends(auth_works_service)]
