from fastapi import status

from app.exceptions.base_exception import BaseHTTPException


class SubmissionNotFound(BaseHTTPException):
    def __init__(self, event_id, work_id):
        super().__init__(
            status.HTTP_404_NOT_FOUND,
            "SUBMISSION_NOT_FOUND",
            f"Submission from Work {work_id} in event {event_id} not found",
            {"work_id": work_id, "event_id": event_id},
        )
