from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models.chair import ChairModel
from app.database.models.event import EventModel, EventStatus
from app.database.models.inscription import InscriptionModel
from app.database.models.organizer import OrganizerModel
from app.database.models.reviewer import ReviewerModel
from app.repository.crud_repository import Repository
from app.schemas.events.public_event_with_roles import PublicEventWithRolesSchema
from app.schemas.events.roles import EventRole
from app.schemas.users.utils import UID


class EventsRepository(Repository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, EventModel)

    async def get_creator_id(self, event_id: UUID):
        conditions = self._primary_key_conditions(event_id)
        return await self._get_with_values(conditions, EventModel.creator_id)

    async def get_status(self, event_id: UUID):
        conditions = self._primary_key_conditions(event_id)
        return await self._get_with_values(conditions, EventModel.status)

    async def get_tracks(self, event_id: UUID):
        conditions = self._primary_key_conditions(event_id)
        return await self._get_with_values(conditions, EventModel.tracks)

    async def get_dates(self, event_id: UUID):
        conditions = self._primary_key_conditions(event_id)
        return await self._get_with_values(conditions, EventModel.dates)

    async def get_review_skeleton(self, event_id):
        conditions = self._primary_key_conditions(event_id)
        return await self._get_with_values(conditions, EventModel.review_skeleton)

    async def event_with_title_exists(self, title):
        conditions = [EventModel.title == title]
        return await self._exists_with_conditions(conditions)

    async def create(self, creator_id, event_create):
        new_event = EventModel(**event_create.model_dump(mode="json"), creator_id=creator_id)
        OrganizerModel(
            event=new_event,
            user_id=new_event.creator_id,
        )
        return await self._create(new_event)

    async def _check_role_exists(self, model, event_id: UUID, user_id: UID) -> bool:
        return await self._exists_with_conditions([model.event_id == event_id, model.user_id == user_id])

    async def get_roles(self, event_id: UUID, user_id: UID) -> list[EventRole]:
        roles = []
        if await self._check_role_exists(OrganizerModel, event_id, user_id):
            roles.append(EventRole.ORGANIZER)
        if await self._check_role_exists(ChairModel, event_id, user_id):
            roles.append(EventRole.CHAIR)
        if await self._check_role_exists(ReviewerModel, event_id, user_id):
            roles.append(EventRole.REVIEWER)

        inscription = await self.session.execute(
            select(InscriptionModel.roles).where(
                (InscriptionModel.event_id == event_id) & (InscriptionModel.user_id == user_id)
            )
        )
        inscription_roles = inscription.scalar_one_or_none()
        if inscription_roles:
            roles.extend([EventRole(role) for role in inscription_roles])
        return roles

    async def get_all_events_for_user(self, user_id: UID, offset: int, limit: int) -> list[PublicEventWithRolesSchema]:
        event_ids_subquery = (
            select(EventModel.id, EventModel.creation_date)
            .distinct()
            .outerjoin(InscriptionModel, InscriptionModel.event_id == EventModel.id)
            .outerjoin(OrganizerModel, OrganizerModel.event_id == EventModel.id)
            .outerjoin(ChairModel, ChairModel.event_id == EventModel.id)
            .outerjoin(ReviewerModel, ReviewerModel.event_id == EventModel.id)
            .where(
                (InscriptionModel.user_id == user_id)
                | (OrganizerModel.user_id == user_id)
                | (ChairModel.user_id == user_id)
                | (ReviewerModel.user_id == user_id)
            )
            .offset(offset)
            .limit(limit)
            .order_by(EventModel.creation_date.desc())
        ).subquery()

        query = (
            select(
                EventModel,
                select(InscriptionModel.roles)
                .where((InscriptionModel.event_id == EventModel.id) & (InscriptionModel.user_id == user_id))
                .label("inscription_roles"),
                select(1)
                .where((OrganizerModel.event_id == EventModel.id) & (OrganizerModel.user_id == user_id))
                .exists()
                .label("is_organizer"),
                select(1)
                .where((ChairModel.event_id == EventModel.id) & (ChairModel.user_id == user_id))
                .exists()
                .label("is_chair"),
                select(1)
                .where((ReviewerModel.event_id == EventModel.id) & (ReviewerModel.user_id == user_id))
                .exists()
                .label("is_reviewer"),
            )
            .join(event_ids_subquery, EventModel.id == event_ids_subquery.c.id)
            .options(selectinload(EventModel.event_slots))
        )

        result = await self.session.execute(query)
        events_with_roles_results = result.all()

        events_map = {}
        for event, inscription_roles, is_organizer, is_chair, is_reviewer in events_with_roles_results:
            if event.id not in events_map:
                roles = []
                if is_organizer:
                    roles.append(EventRole.ORGANIZER)
                if is_chair:
                    roles.append(EventRole.CHAIR)
                if is_reviewer:
                    roles.append(EventRole.REVIEWER)
                if inscription_roles:
                    roles.extend([EventRole(role) for role in inscription_roles])

                events_map[event.id] = PublicEventWithRolesSchema(
                    id=event.id,
                    title=event.title,
                    dates=event.dates,
                    description=event.description,
                    event_type=event.event_type,
                    location=event.location,
                    tracks=event.tracks,
                    status=event.status,
                    event_slots=event.event_slots,
                    roles=roles,
                )

        return list(events_map.values())

    async def get_all_events(
        self, offset: int, limit: int, status: EventStatus | None, title_search: str | None
    ) -> list[EventModel]:
        query = select(EventModel).offset(offset).limit(limit)
        if status is not None:
            query = query.where(EventModel.status == status)
        if title_search is not None:
            query = query.filter(EventModel.title.ilike(f"%{title_search}%"))
        result = await self.session.execute(query)
        return list(result.scalars().all())
