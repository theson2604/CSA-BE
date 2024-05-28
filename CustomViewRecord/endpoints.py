from typing import List
from fastapi import APIRouter, HTTPException
from Authentication.dependencies import AuthCredentialDepend, AuthServiceDepend
from CustomViewRecord.repository import CustomViewRecordRepository
from CustomViewRecord.schemas import CustomViewRecordSchema, UpdateCustomViewRecordSchema
from CustomViewRecord.services import CustomViewRecordService
from Object.repository import ObjectRepository
from app.common.enums import CustomViewRecordType, SystemUserRole
from app.common.errors import HTTPBadRequest
from app.dependencies.authentication import protected_route
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

@router.post("/create-custom-view-record")
@protected_route([SystemUserRole.ADMINISTRATOR, SystemUserRole.USER])
async def create_custom_view_record(
    view_record: CustomViewRecordSchema,
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    try:
        db_str, current_user_id = CURRENT_USER.get("db"), CURRENT_USER.get("_id")
        view_record_service = CustomViewRecordService(db_str)
        return await view_record_service.create_one_view(view_record, current_user_id)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
    if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))
    
@router.get("/get-one-by-id")
@protected_route([SystemUserRole.ADMINISTRATOR, SystemUserRole.USER])
async def get_one(
    id: str,
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    try:
        db_str, current_user_id = CURRENT_USER.get("db"), CURRENT_USER.get("_id")
        view_record_repo = CustomViewRecordRepository(db_str)
        if not (await view_record_repo.find_one_by_id(id)):
            raise HTTPBadRequest(f"Can not find Custom View Record component by id {id}")

        view_record_service = CustomViewRecordService(db_str)
        return await view_record_service.get_one_componet_by_id(id)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))
        
@router.get("/get-all-by-object-id")
@protected_route([SystemUserRole.ADMINISTRATOR, SystemUserRole.USER])
async def get_all_components_by_object_id(
    id: str,
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    try:
        db_str, current_user_id = CURRENT_USER.get("db"), CURRENT_USER.get("_id")
        view_record_service = CustomViewRecordService(db_str)
        return await view_record_service.get_all_components_by_object_id(id)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))
        
@router.post("/update-one-by-id")
@protected_route([SystemUserRole.ADMINISTRATOR, SystemUserRole.USER])
async def update_one(
    view_record: UpdateCustomViewRecordSchema,
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    try:
        db_str, current_user_id = CURRENT_USER.get("db"), CURRENT_USER.get("_id")
        view_record_repo = CustomViewRecordRepository(db_str)
        view_record_dump = view_record.model_dump()
        view_record_id = view_record_dump.get("view_record_id")
        if not view_record_id or not (await view_record_repo.find_one_by_id(view_record_id)):
            raise HTTPBadRequest(f"Can not find Custom View Record component by id {view_record_id}")

        view_record_service = CustomViewRecordService(db_str)
        return await view_record_service.update_one_by_id(view_record, current_user_id)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))

@router.delete("/delete-one-by-id")
@protected_route([SystemUserRole.ADMINISTRATOR, SystemUserRole.USER])
async def delete_one(
    id: str,
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    try:
        db_str, current_user_id = CURRENT_USER.get("db"), CURRENT_USER.get("_id")
        view_record_repo = CustomViewRecordRepository(db_str)
        if not (await view_record_repo.find_one_by_id(id)):
            raise HTTPBadRequest(f"Can not find Custom View Record component by id {id}")

        view_record_service = CustomViewRecordService(db_str)
        return await view_record_service.delete_one_by_id(id)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))
        
@router.delete("/delete-all-by-object-id")
@protected_route([SystemUserRole.ADMINISTRATOR, SystemUserRole.USER])
async def delete_all_by_object_id(
    id: str,
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    try:
        db_str, current_user_id = CURRENT_USER.get("db"), CURRENT_USER.get("_id")
        obj_repo = ObjectRepository(db_str)
        if not (await obj_repo.find_one_by_id(id)):
            raise HTTPBadRequest(f"Object with id {id} does not have any component")

        view_record_service = CustomViewRecordService(db_str)
        return await view_record_service.delete_all_by_object_id(id)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))