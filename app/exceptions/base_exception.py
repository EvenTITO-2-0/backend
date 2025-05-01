from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder


class BaseHTTPException(HTTPException):
    def __init__(self, status_code: int, errorcode: str, message: str, params: dict = None):
        super().__init__(
            status_code=status_code,
            detail=jsonable_encoder(
                {"errorcode": errorcode, "message": message, "params": params if params is not None else {}}
            ),
        )
