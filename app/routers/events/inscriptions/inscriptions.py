from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.authorization.admin_user_dep import IsAdminUsrDep
from app.authorization.inscripted_dep import verify_is_registered, IsRegisteredDep
from app.authorization.organizer_dep import IsOrganizerDep
from app.authorization.user_id_dep import verify_user_exists
from app.authorization.util_dep import or_
from app.schemas.inscriptions.inscription import InscriptionResponseSchema, InscriptionRequestSchema, \
    InscriptionUploadSchema, InscriptionDownloadSchema
from app.schemas.payments.payment import PaymentRequestSchema, PaymentUploadSchema, PaymentsResponseSchema, \
    PaymentDownloadSchema
from app.services.event_inscriptions.event_inscriptions_service_dep import EventInscriptionsServiceDep

inscriptions_events_router = APIRouter(
    prefix="/{event_id}/inscriptions",
    tags=["Event: Inscriptions"]
)


@inscriptions_events_router.post(
    path="",
    status_code=201,
    response_model=InscriptionResponseSchema,
    dependencies=[Depends(verify_user_exists)]
)
async def create_inscription(
        inscription: InscriptionRequestSchema,
        inscriptions_service: EventInscriptionsServiceDep
) -> InscriptionResponseSchema:
    return await inscriptions_service.inscribe_user_to_event(inscription)


@inscriptions_events_router.get(
    path="",
    status_code=200,
    response_model=List[InscriptionResponseSchema],
    dependencies=[or_(IsOrganizerDep, IsAdminUsrDep)]
)
async def read_event_inscriptions(
        inscriptions_service: EventInscriptionsServiceDep,
        offset: int = 0,
        limit: int = Query(default=100, le=100)
) -> List[InscriptionResponseSchema]:
    return await inscriptions_service.get_event_inscriptions(offset, limit)


@inscriptions_events_router.get(
    path="/my-inscription",
    status_code=200,
    response_model=InscriptionResponseSchema,
    dependencies=[Depends(verify_user_exists)]
)
async def read_my_inscriptions(
        inscriptions_service: EventInscriptionsServiceDep
) -> InscriptionResponseSchema:
    return await inscriptions_service.get_my_event_inscription()


@inscriptions_events_router.get(
    path="/{inscription_id}",
    status_code=200,
    response_model=InscriptionResponseSchema,
    dependencies=[or_(IsOrganizerDep, IsRegisteredDep)]
)
async def read_inscription(
        inscription_id: UUID,
        inscriptions_service: EventInscriptionsServiceDep,
) -> InscriptionResponseSchema:
    return await inscriptions_service.get_inscription(inscription_id)


@inscriptions_events_router.get(
    path="/{inscription_id}/affiliation",
    status_code=200,
    response_model=InscriptionDownloadSchema,
    dependencies=[or_(IsOrganizerDep, IsRegisteredDep)]
)
async def read_affiliation(
        inscription_id: UUID,
        inscriptions_service: EventInscriptionsServiceDep,
) -> InscriptionDownloadSchema:
    return await inscriptions_service.get_affiliation(inscription_id)


@inscriptions_events_router.put(
    path="/{inscription_id}",
    status_code=201,
    response_model=InscriptionUploadSchema,
    dependencies=[Depends(verify_is_registered)]
)
async def update_inscription(
        inscription_id: UUID,
        inscription: InscriptionRequestSchema,
        inscriptions_service: EventInscriptionsServiceDep
) -> InscriptionUploadSchema:
    return await inscriptions_service.update_inscription(inscription_id, inscription)


@inscriptions_events_router.put(
    path="/{inscription_id}/pay",
    status_code=201,
    response_model=PaymentUploadSchema,
    dependencies=[Depends(verify_is_registered)]
)
async def pay_inscription(
        inscription_id: UUID,
        payment_request: PaymentRequestSchema,
        inscription_service: EventInscriptionsServiceDep
) -> PaymentUploadSchema:
    return await inscription_service.pay(inscription_id, payment_request)


@inscriptions_events_router.get(
    path="/{inscription_id}/payments",
    status_code=200,
    response_model=List[PaymentsResponseSchema],
    dependencies=[or_(IsOrganizerDep, IsRegisteredDep)]
)
async def read_inscription_payments(
        inscription_id: UUID,
        inscription_service: EventInscriptionsServiceDep,
        offset: int = 0,
        limit: int = Query(default=100, le=100)
) -> List[PaymentsResponseSchema]:
    return await inscription_service.get_inscription_payments(inscription_id, offset, limit)


@inscriptions_events_router.get(
    path="/{inscription_id}/payments/{payment_id}",
    status_code=200,
    response_model=PaymentDownloadSchema,
    dependencies=[or_(IsOrganizerDep, IsRegisteredDep)]
)
async def read_inscription_payment(
        payment_id: UUID,
        inscription_id: UUID,
        inscription_service: EventInscriptionsServiceDep
) -> PaymentDownloadSchema:
    return await inscription_service.get_inscription_payment(inscription_id, payment_id)
