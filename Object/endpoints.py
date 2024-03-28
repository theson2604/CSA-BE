
from fastapi import APIRouter, HTTPException
from Authentication.dependencies import AuthCredentialDepend, AuthServiceDepend
from Object.schemas import ObjectSchema, ObjectWithFieldSchema
from Object.services import ObjectService
from app.common.enums import SystemUserRole
from app.common.errors import HTTPBadRequest
from app.dependencies.authentication import protected_route

router = APIRouter()

@router.post("/create-object")
@protected_route([SystemUserRole.ADMINISTRATOR, SystemUserRole.USER])
async def create_object(
    obj: ObjectSchema,
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    try:
        db_str, current_user_id = CURRENT_USER.get("db"), CURRENT_USER.get("_id")
        obj_service = ObjectService(db_str)
        return await obj_service.create_object_only(obj, current_user_id)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))
        
@router.post("/create-object-with-fields")
@protected_route([SystemUserRole.ADMINISTRATOR, SystemUserRole.USER])
async def create_object_with_fields(
    obj_with_fields: ObjectWithFieldSchema,
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    try:
        db_str, current_user_id = CURRENT_USER.get("db"), CURRENT_USER.get("_id")
        obj_service = ObjectService(db_str)
        return await obj_service.create_object_with_fields(obj_with_fields, current_user_id)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))
        
@router.get("/get-all-objects")
@protected_route([SystemUserRole.ADMINISTRATOR, SystemUserRole.USER])
async def get_all_objects(
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    try:
        db_str = CURRENT_USER.get("db")
        obj_service = ObjectService(db_str)
        return await obj_service.get_all_objects()
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))
        
@router.get("/get-detail-object")
@protected_route([SystemUserRole.ADMINISTRATOR, SystemUserRole.USER])
async def get_detail_object_by_id(
    id: str,
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    try:
        db_str = CURRENT_USER.get("db")
        obj_service = ObjectService(db_str)
        return await obj_service.get_object_detail_by_id(id)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))
        
@router.delete("/delete-one")
@protected_route([SystemUserRole.ADMINISTRATOR, SystemUserRole.USER])
async def delete_one_object(
    object_id: str,
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    try:
        object_service = ObjectService(CURRENT_USER.get("db"))
        await object_service.delete_one_object_by_id(object_id)
        return "Object has been deleted"
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))