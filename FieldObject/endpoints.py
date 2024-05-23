from typing import List
from fastapi import APIRouter, HTTPException
from Authentication.dependencies import AuthCredentialDepend, AuthServiceDepend
from FieldObject.schemas import FieldObjectSchema, UpdateFieldObjectSchema
from FieldObject.services import FieldObjectService
from app.common.enums import SystemUserRole
from app.common.errors import HTTPBadRequest
from app.dependencies.authentication import protected_route
from dotenv import load_dotenv
import os

load_dotenv()

router = APIRouter()

@router.post("/create-field")
@protected_route([SystemUserRole.ADMINISTRATOR, SystemUserRole.USER])
async def create_field(
    field: FieldObjectSchema,
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    try:
        db_str, current_user_id = CURRENT_USER.get("db"), CURRENT_USER.get("_id")
        field_obj_service = FieldObjectService(db_str)
        return await field_obj_service.create_one_field(field)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))
        

@router.post("/update-one-field")
@protected_route([SystemUserRole.ADMINISTRATOR, SystemUserRole.USER])
async def update_one_field(
    field: UpdateFieldObjectSchema,
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    try:
        db_str, current_user_id = CURRENT_USER.get("db"), CURRENT_USER.get("_id")
        field_obj_service = FieldObjectService(db_str)
        return await field_obj_service.update_one_field(field)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))
        
        
@router.post("/update-sorting-fields")
@protected_route([SystemUserRole.ADMINISTRATOR, SystemUserRole.USER])
async def update_sorting_fields(
    fields: List[str],
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    try:
        db_str, current_user_id = CURRENT_USER.get("db"), CURRENT_USER.get("_id")
        field_obj_service = FieldObjectService(db_str)
        await field_obj_service.update_sorting(fields)
        return "ok"
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))

@router.delete("/delete-one")
@protected_route([SystemUserRole.ADMINISTRATOR, SystemUserRole.USER])
async def delete_one_field(
    field_id: str,
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    try:
        field_service = FieldObjectService(CURRENT_USER.get("db"))
        await field_service.delete_one_field_by_id(field_id)

        return "Field has been deleted"
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))
        
@router.get("/test")
# @protected_route([SystemUserRole.ADMINISTRATOR, SystemUserRole.USER])
async def test(
    # CREDENTIALS: AuthCredentialDepend,
    # AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    try:
        # field_service = FieldObjectService(CURRENT_USER.get("db"))
        # await field_service.get_all_fields_by_obj_id(obj_id)

        return os.environ.get("ELASTIC_PASSWORD")
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))