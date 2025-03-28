from fastapi import status

from app.exceptions.base_exception import BaseHTTPException


class AlreadyOrganizerExist(BaseHTTPException):
    def __init__(self, event_id, user_id):
        super().__init__(
            status.HTTP_409_CONFLICT,
            "ALREADY_ORGANIZER_EXIST",
            f"Already organizer for user_id: {user_id} in event: {event_id}",
            {"user_id": user_id, "event_id": event_id},
        )


class UserNotIsOrganizer(BaseHTTPException):
    def __init__(self, event_id, organizer_id):
        super().__init__(
            status.HTTP_404_NOT_FOUND,
            "USER_NOT_IS_ORGANIZER",
            f"Not exist organizer with user: {organizer_id} in event: {event_id}",
            {"organizer_id": organizer_id, "event_id": event_id},
        )


class AtLeastOneOrganizer(BaseHTTPException):
    def __init__(self, event_id, organizer_id):
        super().__init__(
            status.HTTP_409_CONFLICT,
            "AT_LEAST_ONE_ORGANIZER",
            f"There must be at least one organizer. Cannot delete {organizer_id} in event: {event_id}",
            {"organizer_id": organizer_id, "event_id": event_id},
        )
