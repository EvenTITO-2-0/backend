from uuid import UUID

from fastapi import status

from app.database.models.event import EventStatus
from app.database.models.user import UserRole
from app.exceptions.base_exception import BaseHTTPException


class InvalidEventSameTitle(BaseHTTPException):
    def __init__(self, title):
        super().__init__(
            status.HTTP_409_CONFLICT, "INVALID_EVENT_SAME_TITLE", f"Title {title} already in use", {"title": title}
        )


class EventNotFound(BaseHTTPException):
    def __init__(self, event_id):
        super().__init__(
            status.HTTP_404_NOT_FOUND, "EVENT_NOT_FOUND", f"Event {event_id} not found", {"event_id": event_id}
        )


class InvalidQueryEventNotCreatedNotAdmin(BaseHTTPException):
    def __init__(self, event_status: EventStatus | None, role: UserRole):
        super().__init__(
            status.HTTP_409_CONFLICT,
            "INVALID_QUERY_EVENT_NOT_CREATED_NOT_ADMIN",
            f"Invalid query for status: {event_status} while having the role: {role}",
            {"event_status": event_status, "role": role},
        )


class InvalidEventConfiguration(BaseHTTPException):
    def __init__(self):
        super().__init__(
            status.HTTP_409_CONFLICT, "INVALID_EVENT_CONFIGURATION", "Invalid event configuration for published"
        )


class InvalidCaller(BaseHTTPException):
    def __init__(self):
        super().__init__(status.HTTP_409_CONFLICT, "INVALID_CALLER", "Invalid caller for operation")


class CannotUpdateTracksAfterEventStarts(BaseHTTPException):
    def __init__(self, event_id: UUID):
        super().__init__(
            status.HTTP_409_CONFLICT,
            "CANNOT_UPDATE_TRACKS_AFTER_EVENT_STARTS",
            f"Cannot update tracks in event:{event_id} after its started.",
            {
                "event_id": event_id,
            },
        )
