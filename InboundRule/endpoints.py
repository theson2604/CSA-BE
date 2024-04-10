from typing import List
from typing_extensions import Annotated
from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, File, Body
from Authentication.dependencies import AuthCredentialDepend, AuthServiceDepend
from InboundRule.schemas import FileSchema
from InboundRule.services import InboundRule
from app.common.enums import SystemUserRole
from app.common.errors import HTTPBadRequest
from app.dependencies.authentication import protected_route

router = APIRouter()

@router.post("/inbound-file")
@protected_route([SystemUserRole.ADMINISTRATOR, SystemUserRole.ADMINISTRATOR])
async def inbound_file(
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    config: FileSchema = Form(),
    file: UploadFile = File(...),
    CURRENT_USER = None
):
    try:
        db = CURRENT_USER.get("db")
        inbound_rule_service = InboundRule(db)
        return await inbound_rule_service.process_file({"file": file, "config": config})
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))