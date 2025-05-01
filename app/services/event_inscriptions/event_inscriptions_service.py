from uuid import UUID

from app.database.models.event import EventStatus
from app.database.models.inscription import InscriptionModel
from app.exceptions.inscriptions_exceptions import (
    EventNotStarted,
    InscriptionAlreadyExists,
    InscriptionNotFound,
    MyInscriptionNotFound,
)
from app.repository.inscriptions_repository import InscriptionsRepository
from app.schemas.inscriptions.inscription import (
    InscriptionDownloadSchema,
    InscriptionRequestSchema,
    InscriptionResponseSchema,
    InscriptionStatusSchema,
    InscriptionUploadSchema,
    InscriptionUserResponseSchema,
)
from app.schemas.payments.payment import (
    PaymentDownloadSchema,
    PaymentRequestSchema,
    PaymentsResponseSchema,
    PaymentUploadSchema,
)
from app.schemas.users.utils import UID
from app.services.event_payments.event_payments_service import EventPaymentsService
from app.services.events.events_configuration_service import EventsConfigurationService
from app.services.notifications.events_notifications_service import EventsNotificationsService
from app.services.services import BaseService
from app.services.storage.event_inscription_storage_service import EventInscriptionStorageService


class EventInscriptionsService(BaseService):
    def __init__(
        self,
        events_configuration_service: EventsConfigurationService,
        events_payment_service: EventPaymentsService,
        storage_service: EventInscriptionStorageService,
        inscriptions_repository: InscriptionsRepository,
        event_notification_service: EventsNotificationsService,
        event_id: UUID,
        user_id: UID,
    ):
        self.events_configuration_service = events_configuration_service
        self.events_payment_service = events_payment_service
        self.storage_service = storage_service
        self.inscriptions_repository = inscriptions_repository
        self.event_notification_service = event_notification_service
        self.event_id = event_id
        self.user_id = user_id

    async def inscribe_user_to_event(self, inscription: InscriptionRequestSchema) -> InscriptionUploadSchema:
        event_status = await self.events_configuration_service.get_event_status()
        if event_status != EventStatus.STARTED:
            raise EventNotStarted(self.event_id, event_status)

        if await self.inscriptions_repository.inscription_exists(self.event_id, self.user_id):
            raise InscriptionAlreadyExists(self.event_id, self.user_id)

        saved_inscription = await self.inscriptions_repository.inscribe(self.event_id, self.user_id, inscription)
        response = InscriptionUploadSchema(id=saved_inscription.id)
        if saved_inscription.affiliation is not None:
            upload_url = await self.storage_service.get_affiliation_upload_url(self.user_id, saved_inscription.id)
            response.upload_url = upload_url

        # Ending we send a notification email
        # TODO: enviar email al inscriptor ?
        await self.event_notification_service.notify_inscription(self.event_id, self.user_id)
        return response

    async def update_inscription(
        self, inscription_id: UUID, inscription_update: InscriptionRequestSchema
    ) -> InscriptionUploadSchema:
        my_inscription = await self.inscriptions_repository.get_user_inscription_by_id(
            self.user_id, self.event_id, inscription_id
        )
        if my_inscription is None:
            raise InscriptionNotFound(self.event_id, inscription_id)
        await self.inscriptions_repository.update_inscription(inscription_update, self.event_id, inscription_id)
        response = InscriptionUploadSchema(id=inscription_id)
        if inscription_update.affiliation is not None:
            upload_url = await self.storage_service.get_affiliation_upload_url(self.user_id, inscription_id)
            response.upload_url = upload_url
        return response

    async def get_event_inscriptions(self, offset: int, limit: int) -> list[InscriptionResponseSchema]:
        inscriptions = await self.inscriptions_repository.get_event_inscriptions(self.event_id, offset, limit)
        return list(map(EventInscriptionsService.map_to_schema, inscriptions))

    async def get_inscription(self, inscription_id: UUID) -> InscriptionResponseSchema:
        inscription = await self.inscriptions_repository.get(inscription_id)
        if inscription is None:
            raise InscriptionNotFound(self.event_id, inscription_id)
        return EventInscriptionsService.map_to_schema(inscription)

    async def get_affiliation(self, inscription_id: UUID) -> InscriptionDownloadSchema:
        inscription = await self.inscriptions_repository.get(inscription_id)
        if inscription is None:
            raise InscriptionNotFound(self.event_id, inscription_id)
        response = InscriptionDownloadSchema(id=inscription.id)
        if inscription.affiliation:
            download_url = await self.storage_service.get_affiliation_read_url(self.user_id, inscription.id)
            response.download_url = download_url
        return response

    async def get_my_event_inscription(self) -> InscriptionResponseSchema:
        inscription = await self.inscriptions_repository.get_event_user_inscription(self.event_id, self.user_id)
        if inscription is None:
            raise MyInscriptionNotFound(self.event_id)
        return EventInscriptionsService.map_to_schema(inscription)

    async def pay(self, inscription_id: UUID, payment_request: PaymentRequestSchema) -> PaymentUploadSchema:
        my_inscription = await self.inscriptions_repository.get_user_inscription_by_id(
            self.user_id, self.event_id, inscription_id
        )
        if my_inscription is None:
            raise InscriptionNotFound(self.event_id, inscription_id)

        # TODO cosas que PODRIAMOS validar pero no se si vale la pena
        # si me manda works que sean mios
        # si me manda works que la inscripcion sea de speaker
        # que exista la tarifa con el nombre de la que quiere pagar
        # limite de works a pagar harcodeado o que lo elija el organizador
        payment_id = await self.events_payment_service.pay_inscription(inscription_id, payment_request)
        upload_url = await self.storage_service.get_payment_upload_url(self.user_id, payment_id)
        return PaymentUploadSchema(id=payment_id, upload_url=upload_url)

    async def is_my_inscription(self, inscription_id: UUID) -> bool:
        my_inscription = await self.inscriptions_repository.get_user_inscription_by_id(
            self.user_id, self.event_id, inscription_id
        )
        return my_inscription is not None

    async def get_inscription_payments(
        self, inscription_id: UUID, offset: int, limit: int
    ) -> list[PaymentsResponseSchema]:
        return await self.events_payment_service.get_inscription_payments(inscription_id, offset, limit)

    async def get_inscription_payment(self, inscription_id: UUID, payment_id: UUID) -> PaymentDownloadSchema:
        payment = await self.events_payment_service.get_inscription_payment(inscription_id, payment_id)
        download_url = await self.storage_service.get_payment_read_url(self.user_id, payment_id)
        return PaymentDownloadSchema(
            **payment.model_dump(),
            download_url=download_url,
        )

    async def update_inscription_status(self, inscription_id: UUID, new_status: InscriptionStatusSchema) -> None:
        update_ok = await self.inscriptions_repository.update_status(self.event_id, inscription_id, new_status)
        if not update_ok:
            raise InscriptionNotFound(self.event_id, inscription_id)
        return

    @staticmethod
    def map_to_schema(model: InscriptionModel) -> InscriptionResponseSchema:
        return InscriptionResponseSchema(
            id=str(model.id),
            user_id=model.user_id,
            event_id=model.event_id,
            status=model.status,
            roles=model.roles,
            affiliation=model.affiliation,
            user=InscriptionUserResponseSchema(
                fullname=model.user.name + " " + model.user.lastname, email=model.user.email
            ),
        )
