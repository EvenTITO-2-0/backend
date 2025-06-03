# backend/app/exceptions/provider_exceptions.py
from fastapi import status
from app.exceptions.base_exception import BaseHTTPException
from uuid import UUID
from app.exceptions.base_exceptions import BaseException

class ProviderAccountNotFound(BaseException):
    def __init__(self, event_id: UUID):
        super().__init__(f"Provider account not found for event {event_id}")

class ProviderAccountAlreadyExists(BaseException):
    def __init__(self, event_id: UUID):
        super().__init__(f"Provider account already exists for event {event_id}")

class InvalidProviderCredentials(BaseException):
    def __init__(self, message: str):
        super().__init__(f"Invalid provider credentials: {message}")