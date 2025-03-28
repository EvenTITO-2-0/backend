from fastapi import status

from app.exceptions.base_exception import BaseHTTPException


class ExpirationDateException(BaseHTTPException):
    def __init__(self):
        super().__init__(
            status.HTTP_409_CONFLICT,
            "EXPIRATION_DATE_EXCEPTION",
            "Application expired",
        )
