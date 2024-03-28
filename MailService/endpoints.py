from typing import List
from typing_extensions import Annotated
from fastapi import APIRouter, Depends, HTTPException
from Authentication.dependencies import AuthCredentialDepend, AuthServiceDepend
from MailService.schemas import SendMailSchema, EmailSchema
from MailService.services import MailServices
from app.common.enums import SystemUserRole
from app.common.errors import HTTPBadRequest
from app.dependencies.authentication import protected_route

router = APIRouter()

@router.post("/create-email")
@protected_route([SystemUserRole.ADMINISTRATOR])
async def create_email(
    email: EmailSchema,
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    try:
        db = CURRENT_USER.get("db")
        mail_service = MailServices(db)
        return await mail_service.create_email(email)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))

@router.post("/send")
@protected_route([SystemUserRole.ADMINISTRATOR])
async def send_mail(
    mail: SendMailSchema,
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    try:
        mail_service = MailServices()
        return await mail_service.send_one(mail)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))