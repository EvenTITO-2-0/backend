from fastapi import status

from app.exceptions.base_exception import BaseHTTPException


class InscriptionAlreadyExists(BaseHTTPException):
    def __init__(self, event_id, user_id):
        super().__init__(
            status.HTTP_409_CONFLICT,
            "INSCRIPTION_ALREADY_EXISTS",
            (f"Inscription from user: {user_id} " f"to event: {event_id} already exists."),
            {"user_id": user_id, "event_id": event_id},
        )


class EventNotStarted(BaseHTTPException):
    def __init__(self, event_id, event_status):
        super().__init__(
            status.HTTP_409_CONFLICT,
            "EVENT_NOT_STARTED",
            (f"The event {event_id} has not started." f" The current event status is {event_status}"),
            {"event_status": event_status, "event_id": event_id},
        )


class InscriptionNotFound(BaseHTTPException):
    def __init__(self, event_id, inscription_id):
        super().__init__(
            status.HTTP_404_NOT_FOUND,
            "INSCRIPTION_NOT_FOUND",
            (f"Inscription {inscription_id} in event {event_id} not found"),
            {"inscription_id": inscription_id, "event_id": event_id},
        )


class MyInscriptionNotFound(BaseHTTPException):
    def __init__(self, event_id):
        super().__init__(
            status.HTTP_404_NOT_FOUND,
            "MY_INSCRIPTION_NOT_FOUND",
            (f"You dont have any inscription in the event {event_id}"),
            {"event_id": event_id},
        )
