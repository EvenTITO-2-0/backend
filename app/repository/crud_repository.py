from typing import Union

from pydantic import BaseModel
from sqlalchemy import and_, exists, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select


class Repository:
    """
    Base class for repositories
    """

    def __init__(self, session: AsyncSession, model):
        self.session = session
        self.model = model

    def _primary_key_conditions(self, id):
        return [self.model.id == id]

    async def exists(self, id) -> bool:
        conditions = self._primary_key_conditions(id)
        return await self._exists_with_conditions(conditions)

    async def _exists_with_conditions(self, conditions):
        query = select(exists().where(and_(*conditions)))
        result = await self.session.execute(query)
        return result.scalar()

    async def get(self, id):
        conditions = self._primary_key_conditions(id)
        return await self._get_with_conditions(conditions)

    async def _get_with_conditions(self, conditions: list, order_by=None):
        return await self._get_with_values(conditions, self.model, order_by)

    async def _get_with_values(self, conditions: list, values, order_by=None):
        query = select(values).where(and_(*conditions))
        if order_by is not None:
            query = query.order_by(order_by)
        query = query.limit(1)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def update(self, id, object_update: Union[BaseModel, dict]) -> bool:
        conditions = self._primary_key_conditions(id)

        if isinstance(object_update, BaseModel):
            values_data = object_update.model_dump(mode="json")
        else:
            values_data = object_update

        return await self._update_with_conditions(conditions, values_data)

    async def _update_with_conditions(self, conditions, object_update) -> bool:
        if isinstance(object_update, BaseModel):
            update_data = object_update.model_dump(mode="json")
        else:
            update_data = object_update

        query = update(self.model).where(and_(*conditions)).values(update_data)
        await self.session.execute(query)
        await self.session.commit()
        return True

    async def _get_many_with_conditions(self, conditions, offset: int, limit: int):
        query = select(self.model).where(and_(*conditions)).offset(offset).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def _get_many_with_values(self, conditions, values, offset: int, limit: int):
        query = select(values).where(and_(*conditions)).offset(offset).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_many(self, offset: int, limit: int):
        query = select(self.model).offset(offset).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def _count_with_conditions(self, conditions):
        query = select(func.count()).where(and_(*conditions))
        result = await self.session.execute(query)
        return result.scalar_one()

    async def create(self, object_create: BaseModel):
        db_in = self.model(**object_create.model_dump(mode="json"))
        return await self._create(db_in)

    async def _create(self, db_in):
        self.session.add(db_in)
        await self.session.commit()
        await self.session.refresh(db_in)
        return db_in

    async def remove(self, id):
        obj = await self.get(id)
        await self.session.delete(obj)
        await self.session.commit()
        return obj
