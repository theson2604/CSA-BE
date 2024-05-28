from typing import List
from typing_extensions import Annotated
from fastapi import APIRouter, Depends, HTTPException
from Authentication.dependencies import AuthCredentialDepend, AuthServiceDepend
from MailService.repository import MailServiceRepository
from MailService.schemas import ScanMailSchema, SendMailSchema, EmailSchema, TemplateSchema
from MailService.services import MailServices
from Object.repository import ObjectRepository
from app.common.db_connector import DBCollections
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
        db, admin_id = CURRENT_USER.get("db"), CURRENT_USER.get("_id")
        email_dump = email.model_dump()
        mail_repo = MailServiceRepository(db, DBCollections.EMAIL_TEMPLATE)
        if not (await mail_repo.find_template_by_id(email_dump.get("template_id"))):
            raise HTTPBadRequest(f"Can not find template by template_id {email_dump.get("template_id")}")

        mail_service = MailServices(db)
        return await mail_service.create_email(email, admin_id)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))

@router.post("/send-email")
@protected_route([SystemUserRole.ADMINISTRATOR])
async def send_mail(
    mail: SendMailSchema,
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    try:
        mail_obj = mail.model_dump()
        db = CURRENT_USER.get("db")
        admin_id = CURRENT_USER.get("_id")
        object_id = mail_obj.get("object")

        obj_repo = ObjectRepository(db)
        obj = await obj_repo.find_one_by_id(object_id)
        if not obj:
            raise HTTPBadRequest(f"Not found {object_id} object by _id")
            
        mail_service = MailServices(db, obj.get("obj_id"))
        return await mail_service.send_one(mail, admin_id)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))
        
@router.post("/scan-email")
@protected_route([SystemUserRole.ADMINISTRATOR])
async def send_mail(
    mail: ScanMailSchema,
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    try:
        mail_obj = mail.model_dump()
        db = CURRENT_USER.get("db")
        admin_id = CURRENT_USER.get("_id")
        object_id = mail_obj.get("object")

        obj_repo = ObjectRepository(db)
        obj = await obj_repo.find_one_by_id(object_id)
        if not obj:
            raise HTTPBadRequest(f"Not found {object_id} object by _id")
            
        mail_service = MailServices(db, obj.get("obj_id"))
        return await mail_service.scan_email(mail, admin_id)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))
    
@router.post("/create-template")
@protected_route([SystemUserRole.ADMINISTRATOR])
async def create_template(
    template: TemplateSchema,
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    try:
        db = CURRENT_USER.get("db")
        mail_service = MailServices(db)
        return await mail_service.create_template(template)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))

@router.get("/get-all-templates")
@protected_route([SystemUserRole.ADMINISTRATOR])
async def get_all_templates(
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    try:
        db = CURRENT_USER.get("db")
        mail_service = MailServices(db)
        return await mail_service.get_all_templates()
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))

@router.get("/get-templates-by-object-id")
@protected_route([SystemUserRole.ADMINISTRATOR])
async def get_templates_by_object_id(
    object_id: str,
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    try:
        db = CURRENT_USER.get("db")
        mail_service = MailServices(db)
        return await mail_service.get_templates_by_object_id(object_id)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))
        