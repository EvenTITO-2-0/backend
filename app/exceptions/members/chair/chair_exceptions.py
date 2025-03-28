from fastapi import status

from app.exceptions.base_exception import BaseHTTPException


class AlreadyChairExist(BaseHTTPException):
    def __init__(self, event_id, user_id):
        super().__init__(
            status.HTTP_409_CONFLICT,
            "ALREADY_CHAIR_EXIST",
            f"Already chair for user_id: {user_id} in event: {event_id}",
            {"user_id": user_id, "event_id": event_id},
        )


class UserNotIsChair(BaseHTTPException):
    def __init__(self, event_id, chair_id):
        super().__init__(
            status.HTTP_404_NOT_FOUND,
            "USER_NOT_IS_CHAIR",
            f"Not exist chair: {chair_id} in event: {event_id}",
            {"chair_id": chair_id, "event_id": event_id},
        )


class InvalidUpdateTrack(BaseHTTPException):
    def __init__(self, event_id, new_track, tracks):
        super().__init__(
            status.HTTP_409_CONFLICT,
            "INVALID_UPDATE_TRACK",
            f"Invalid track: {new_track}. The available tracks in event: {event_id} are {tracks}.",
            {"new_track": new_track, "event_id": event_id, "tracks": tracks},
        )
