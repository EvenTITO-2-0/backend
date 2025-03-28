from fastapi import status

from app.exceptions.base_exception import BaseHTTPException


class UserNotFound(BaseHTTPException):
    def __init__(self, user_id: str):
        super().__init__(status.HTTP_404_NOT_FOUND, "USER_NOT_FOUND", f"User {user_id} not found", {"user_id": user_id})


class UserWithEmailNotFound(BaseHTTPException):
    def __init__(self, email_user: str):
        super().__init__(
            status.HTTP_404_NOT_FOUND,
            "USER_WITH_EMAIL_NOT_FOUND",
            f"User with email {email_user} not found",
            {"email": email_user},
        )


class EmailAlreadyExists(BaseHTTPException):
    def __init__(self, email_str: str):
        super().__init__(
            status.HTTP_409_CONFLICT, "EMAIL_ALREADY_EXISTS", f"Email {email_str} already exists", {"email": email_str}
        )


class IdAlreadyExists(BaseHTTPException):
    def __init__(self, id_str):
        super().__init__(status.HTTP_409_CONFLICT, "ID_ALREADY_EXISTS", f"Id {id_str} already exists", {"id": id_str})


class CantRemoveLastAdmin(BaseHTTPException):
    def __init__(self):
        super().__init__(status.HTTP_409_CONFLICT, "CANT_REMOVE_LAST_ADMIN", "System must have at least 1 admin")
