from typing import List
from uuid import UUID

from fastapi import APIRouter, Query

from app.authorization.admin_user_dep import IsAdminUsrDep
from app.authorization.organizer_dep import IsOrganizerDep
from app.authorization.util_dep import or_
from app.schemas.payments.payment import PaymentsResponseSchema, PaymentStatusSchema
from app.services.event_payments.event_payments_service_dep import EventPaymentsServiceDep

events_payments_router = APIRouter(prefix="/{event_id}/payments", tags=["Event: Payments"])


@events_payments_router.get(
    path="",
    status_code=200,
    response_model=List[PaymentsResponseSchema],
    dependencies=[or_(IsOrganizerDep, IsAdminUsrDep)],
)
async def read_event_payments(
    payments_service: EventPaymentsServiceDep, offset: int = 0, limit: int = Query(default=100, le=100)
) -> List[PaymentsResponseSchema]:
    return await payments_service.get_event_payments(offset, limit)


@events_payments_router.patch(
    path="/{payment_id}", status_code=204, response_model=None, dependencies=[or_(IsOrganizerDep, IsAdminUsrDep)]
)
async def change_payment_status(
    payment_id: UUID,
    payments_service: EventPaymentsServiceDep,
    status_modification: PaymentStatusSchema,
):
    await payments_service.update_payment_status(payment_id, status_modification)
