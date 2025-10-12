from uuid import UUID

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.payment import PaymentModel
from app.database.models.work import WorkModel
from app.repository.crud_repository import Repository
from app.schemas.payments.payment import (
    PaymentRequestSchema,
    PaymentResponseSchema,
    PaymentStatusSchema,
    PaymentWorkSchema,
)


class PaymentsRepository(Repository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, PaymentModel)

    async def get_all_payments_for_event(self, event_id: UUID, offset: int, limit: int) -> list[PaymentResponseSchema]:
        conditions = [PaymentModel.event_id == event_id]
        return await self._get_payments(conditions, offset, limit)

    async def get_payment(self, event_id: UUID, inscription_id: UUID, payment_id: UUID) -> PaymentResponseSchema:
        conditions = [
            PaymentModel.event_id == event_id,
            PaymentModel.inscription_id == inscription_id,
            PaymentModel.id == payment_id,
        ]
        payment = await self._get_with_conditions(conditions)
        work_conditions = [WorkModel.id.in_(payment.works)]
        works = await self._get_many_with_values(work_conditions, WorkModel, 0, 100)
        return PaymentResponseSchema(
            id=payment.id,
            event_id=payment.event_id,
            inscription_id=payment.inscription_id,
            status=payment.status,
            works=[PaymentWorkSchema(id=work.id, title=work.title, track=work.track) for work in works or []],
            fare_name=payment.fare_name,
            creation_date=payment.creation_date,
            last_update=payment.last_update,
        )

    async def get_payments_for_inscription(
        self, event_id: UUID, inscription_id: UUID, offset: int, limit: int
    ) -> list[PaymentResponseSchema]:
        conditions = [PaymentModel.event_id == event_id, PaymentModel.inscription_id == inscription_id]
        return await self._get_payments(conditions, offset, limit)

    async def do_new_payment(self, event_id: UUID, inscription_id: UUID, payment_request: PaymentRequestSchema) -> UUID:
        new_payment = PaymentModel(**payment_request.model_dump(), event_id=event_id, inscription_id=inscription_id)
        return (await self._create(new_payment)).id

    async def update_status(self, event_id: UUID, payment_id: UUID, status: PaymentStatusSchema) -> bool:
        conditions = [PaymentModel.event_id == event_id, PaymentModel.id == payment_id]
        return await self._update_with_conditions(conditions, status)

    async def update_provider_fields(self, payment_id: UUID, fields: dict) -> None:
        await self.session.execute(update(PaymentModel).where(PaymentModel.id == payment_id).values(**fields))
        await self.session.commit()

    async def get_payment_id_by_preference_id(self, event_id: UUID, preference_id: str) -> UUID | None:
        conditions = [PaymentModel.event_id == event_id, PaymentModel.provider_preference_id == preference_id]
        obj = await self._get_with_conditions(conditions)
        return getattr(obj, "id", None)

    async def get_inscription_id_by_payment_id(self, event_id: UUID, payment_id: UUID) -> UUID | None:
        conditions = [PaymentModel.event_id == event_id, PaymentModel.id == payment_id]
        obj = await self._get_with_conditions(conditions)
        return getattr(obj, "inscription_id", None)

    async def _get_payments(self, conditions, offset: int, limit: int) -> list[PaymentResponseSchema]:
        res = await self._get_many_with_conditions(conditions, offset, limit)
        payments = []
        for row in res:
            work_conditions = [WorkModel.id.in_(row.works)]
            works = await self._get_many_with_values(work_conditions, WorkModel, 0, 100)
            payments.append(
                PaymentResponseSchema(
                    id=row.id,
                    event_id=row.event_id,
                    inscription_id=row.inscription_id,
                    status=row.status,
                    works=[PaymentWorkSchema(id=work.id, title=work.title, track=work.track) for work in works or []],
                    fare_name=row.fare_name,
                    creation_date=row.creation_date,
                    last_update=row.last_update,
                )
            )
        return payments
