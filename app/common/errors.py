from fastapi import HTTPException

from app.common.enums import StatusCodeException


def HTTPBadRequest(detail: str) -> HTTPException:
    return HTTPException(StatusCodeException.BAD_REQUEST, detail=detail)