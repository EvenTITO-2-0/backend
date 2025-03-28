from fastapi import status

from app.exceptions.base_exception import BaseHTTPException


class PaymentNotFound(BaseHTTPException):
    def __init__(self, event_id, payment_id):
        super().__init__(
            status.HTTP_404_NOT_FOUND,
            "PAYMENT_NOT_FOUND",
            f"Payment {payment_id} in event {event_id} not found",
            {"payment_id": payment_id, "event_id": event_id},
        )
