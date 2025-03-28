from fastapi import status

from app.exceptions.base_exception import BaseHTTPException


class TitleAlreadyExists(BaseHTTPException):
    def __init__(self, title, event_id):
        super().__init__(
            status.HTTP_409_CONFLICT,
            "TITLE_ALREADY_EXISTS",
            f"Work title {title} already exists for the event {event_id}",
            {"title": title, "event_id": event_id},
        )


class WorkNotFound(BaseHTTPException):
    def __init__(self, event_id, work_id):
        super().__init__(
            status.HTTP_404_NOT_FOUND,
            "WORK_NOT_FOUND",
            f"Work {work_id} in event {event_id} not found",
            {"work_id": work_id, "event_id": event_id},
        )


class NotIsMyWork(BaseHTTPException):
    def __init__(self, event_id, work_id):
        super().__init__(
            status.HTTP_404_NOT_FOUND,
            "NOT_IS_MY_WORK",
            f"Work {work_id} in event {event_id} not is yours",
            {"work_id": work_id, "event_id": event_id},
        )


class StatusNotAllowWorkUpdate(BaseHTTPException):
    def __init__(self, work_status, work_id):
        super().__init__(
            status.HTTP_409_CONFLICT,
            "STATUS_NOT_ALLOW_WORK_UPDATE",
            f"Status {work_status} on work {work_id} does not allow work update",
            {"work_id": work_id, "work_status": work_status},
        )


class CannotUpdateWorkAfterDeadlineDate(BaseHTTPException):
    def __init__(self, deadline_date, work_id):
        super().__init__(
            status.HTTP_409_CONFLICT,
            "CANNOT_UPDATE_WORK_AFTER_DEADLINE_DATE",
            f"Submission deadline {deadline_date} for work {work_id} already passed",
            {"work_id": work_id, "deadline_date": deadline_date},
        )


class CannotCreateWorkAfterDeadlineDate(BaseHTTPException):
    def __init__(self, deadline_date):
        super().__init__(
            status.HTTP_409_CONFLICT,
            "CANNOT_CREATE_WORK_AFTER_DEADLINE_DATE",
            f"Event submission deadline {deadline_date} for create work already passed",
            {"deadline_date": deadline_date},
        )


class CannotCreateWorkIfNotSpeakerInscription(BaseHTTPException):
    def __init__(self, event_id):
        super().__init__(
            status.HTTP_409_CONFLICT,
            "CANNOT_CREATE_WORK_IF_NOT_SPEAKER_INSCRIPTION",
            f"You cannot upload a work if you are not inscripted as a speaker in event {event_id}",
            {"event_id": event_id},
        )


class TrackNotExistInEvent(BaseHTTPException):
    def __init__(self, event_id, track):
        super().__init__(
            status.HTTP_409_CONFLICT,
            "TRACK_NOT_EXIST_IN_EVENT",
            f"Track: {track} not exist in event: {event_id}",
            {"event_id": event_id, "track": track},
        )
