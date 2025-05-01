from fastapi import status

from app.exceptions.base_exception import BaseHTTPException


class UserNotIsReviewer(BaseHTTPException):
    def __init__(self, event_id, reviewer_id):
        super().__init__(
            status.HTTP_404_NOT_FOUND,
            "USER_NOT_IS_REVIEWER",
            f"Not exist reviewer with user: {reviewer_id} in event: {event_id}",
            {"reviewer_id": reviewer_id, "event_id": event_id},
        )


class AlreadyReviewerExist(BaseHTTPException):
    def __init__(self, event_id, user_id, work_id):
        super().__init__(
            status.HTTP_409_CONFLICT,
            "ALREADY_REVIEWER_EXIST",
            f"Already reviewer user_id: {user_id} for work_id: {work_id} in event: {event_id}",
            {"user_id": user_id, "work_id": work_id, "event_id": event_id},
        )
