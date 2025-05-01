from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException

from app.services.event_inscriptions.event_inscriptions_service_dep import EventInscriptionsServiceDep


class IsRegistered:
    async def __call__(self, inscription_id: UUID, inscription_service: EventInscriptionsServiceDep) -> bool:
        return await inscription_service.is_my_inscription(inscription_id)


IsRegisteredDep = Annotated[bool, Depends(IsRegistered())]


class VerifyIsRegistered:
    async def __call__(self, is_my_inscription: IsRegisteredDep) -> None:
        if not is_my_inscription:
            raise HTTPException(status_code=403)


verify_is_registered = VerifyIsRegistered()
RegisteredDep = Annotated[None, Depends(verify_is_registered)]
