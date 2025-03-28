from app.exceptions.base_exception import BaseHTTPException


class AlreadyMemberExist(BaseHTTPException):
    def __init__(self, event_id, user_id, role):
        super().__init__(
            409,
            "ALREADY_MEMBER_EXIST",
            f"Already member for user_id: {user_id} in event: {event_id} with role: {role}",
            {"user_id": user_id, "event_id": event_id, "role": role},
        )


class MemberRoleNotSupported(BaseHTTPException):
    def __init__(self, role):
        super().__init__(409, "MEMBER_ROLE_NOT_SUPPORTED", f"Member Role {role} not supported.", {"role": role})
