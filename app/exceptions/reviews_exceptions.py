from fastapi import status

from app.exceptions.base_exception import BaseHTTPException


class IsNotWorkRevisionPeriod(BaseHTTPException):
    def __init__(self, event_id, work_id):
        super().__init__(
            status.HTTP_409_CONFLICT,
            "IS_NOT_WORK_REVISION_PERIOD",
            f"Cannot do review because is not work revision period for work: {work_id} in event: {event_id}",
            {"work_id": work_id, "event_id": event_id},
        )


class CannotPublishReviews(BaseHTTPException):
    def __init__(self, event_id, work_id):
        super().__init__(
            status.HTTP_409_CONFLICT,
            "CANOT_PUBLISH_REVIEWS",
            f"Cannot publish reviews because they dont pertain to the work: {work_id} in event: {event_id}",
            {"work_id": work_id, "event_id": event_id},
        )


class AlreadyReviewExist(BaseHTTPException):
    def __init__(self, event_id, work_id, submission_id):
        super().__init__(
            status.HTTP_409_CONFLICT,
            "ALREADY_REVIEW_EXIST",
            (
                f"Cannot add review because it already exists. work: {work_id} "
                f"event: {event_id}; submission: {submission_id}"
            ),
            {"work_id": work_id, "event_id": event_id, "submission_id": submission_id},
        )
