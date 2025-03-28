from fastapi import APIRouter

from app.authorization.admin_user_dep import IsAdminUsrDep
from app.authorization.organizer_dep import IsOrganizerDep
from app.authorization.util_dep import or_
from app.schemas.storage.schemas import UploadURLSchema
from app.services.storage.event_storage_service import EventsStaticFiles
from app.services.storage.event_storage_service_dep import EventStorageServiceDep

events_media_router = APIRouter(prefix="/{event_id}/upload_url", tags=["Events: Multimedia"])


@events_media_router.get(path="/{media}", dependencies=[or_(IsOrganizerDep, IsAdminUsrDep)])
async def get_upload_url(media: EventsStaticFiles, storage_service: EventStorageServiceDep) -> UploadURLSchema:
    return await storage_service.get_upload_url(media)
