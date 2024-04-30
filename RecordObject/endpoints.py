from typing import List
from fastapi import APIRouter, HTTPException
from Authentication.dependencies import AuthCredentialDepend, AuthServiceDepend
from Object.repository import ObjectRepository
from RecordObject.schemas import DeleteRecordSchema, RecordObjectSchema, UpdateRecordSchema
from RecordObject.search import ElasticsearchRecord
from RecordObject.services import RecordObjectService
from app.common.elastic import ElasticsearchBase
from app.common.enums import SystemUserRole
from app.common.errors import HTTPBadRequest
from app.dependencies.authentication import protected_route

router = APIRouter()

@router.post("/create-record")
@protected_route([SystemUserRole.ADMINISTRATOR, SystemUserRole.USER])
async def create_record(
    record: RecordObjectSchema,
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    try:
        db_str, current_user_id = CURRENT_USER.get("db"), CURRENT_USER.get("_id")
        record = record.model_dump()
        obj_id = record.get("object_id")
        obj_repo = ObjectRepository(db_str)
        obj = await obj_repo.find_one_by_id(obj_id)
        if not obj:
            raise HTTPBadRequest(f"Not found {obj_id} object by _id")
        
        record_service = RecordObjectService(db_str, obj.get("obj_id"), obj_id)
        return await record_service.create_record(record, current_user_id)
    
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))
        
@router.get("/get-all-records")
@protected_route([SystemUserRole.ADMINISTRATOR, SystemUserRole.USER])
async def get_all_records(
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    obj_id: str,
    page: int = 1,
    page_size: int = 100,
    CURRENT_USER = None,
    
):
    try:
        db_str, current_user_id = CURRENT_USER.get("db"), CURRENT_USER.get("_id")
        obj_repo = ObjectRepository(db_str)
        obj = await obj_repo.find_one_by_id(obj_id)
        if not obj:
            raise HTTPBadRequest(f"Not found {obj_id} object by _id")
        
        record_service = RecordObjectService(db_str, obj.get("obj_id"), obj_id)
        return await record_service.get_all_records_with_detail(obj_id, page, page_size)
    
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))
        
@router.get("/get-record-detail")
@protected_route([SystemUserRole.ADMINISTRATOR, SystemUserRole.USER])
async def get_record_detail(
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    record_id: str,
    obj_id: str,
    CURRENT_USER = None,
    
):
    try:
        db_str, current_user_id = CURRENT_USER.get("db"), CURRENT_USER.get("_id")
        obj_repo = ObjectRepository(db_str)
        obj = await obj_repo.find_one_by_id(obj_id)
        if not obj:
            raise HTTPBadRequest(f"Not found {obj_id} object by _id")
        
        record_service = RecordObjectService(db_str, obj.get("obj_id"), obj_id)
        return await record_service.get_one_record_by_id_with_detail(record_id, obj_id)
    
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))
        
        
@router.post("/health-check")
@protected_route([SystemUserRole.ADMINISTRATOR, SystemUserRole.USER])
async def health_check(
    obj_id: str,
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None,
):
    try:
        db_str, current_user_id = CURRENT_USER.get("db"), CURRENT_USER.get("_id")
        obj_repo = ObjectRepository(db_str)
        obj = await obj_repo.find_one_by_id(obj_id)
        if not obj:
            raise HTTPBadRequest(f"Not found {obj_id} object by _id")
        obj_id_str = obj.get("obj_id")
        elastic_service = ElasticsearchRecord(db_str, obj_id_str, obj_id)
        return await elastic_service.sync_docs()
    
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))


@router.post("/search")
@protected_route([SystemUserRole.ADMINISTRATOR, SystemUserRole.USER])
async def search_record(
    record: RecordObjectSchema,
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    page: int = 1,
    page_size: int = 10,
    CURRENT_USER = None,
):
    try:
        db_str, current_user_id = CURRENT_USER.get("db"), CURRENT_USER.get("_id")
        record = record.model_dump()
        obj_id = record.pop("object_id")
        obj_repo = ObjectRepository(db_str)
        obj = await obj_repo.find_one_by_id(obj_id)
        if not obj:
            raise HTTPBadRequest(f"Not found {obj_id} object by _id")
        obj_id_str = obj.get("obj_id")
        elastic_service = ElasticsearchRecord(db_str, obj_id_str, obj_id)
        return await elastic_service.search_record(record, page, page_size)
    
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))
        
@router.post("/update-one")
@protected_route([SystemUserRole.ADMINISTRATOR, SystemUserRole.USER])
async def update_record(
    record: UpdateRecordSchema,
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None,
):
    try:
        db_str, current_user_id = CURRENT_USER.get("db"), CURRENT_USER.get("_id")
        record = record.model_dump()
        obj_id = record.get("object_id")
        obj_repo = ObjectRepository(db_str)
        obj = await obj_repo.find_one_by_id(obj_id)
        if not obj:
            raise HTTPBadRequest(f"Not found {obj_id} object by _id")
        
        record_service = RecordObjectService(db_str, obj.get("obj_id"), obj_id)
        return await record_service.update_one_record(record, current_user_id)
    
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))
        
@router.delete("/delete-one")
@protected_route([SystemUserRole.ADMINISTRATOR, SystemUserRole.USER])
async def update_record(
    delete: DeleteRecordSchema,
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None,
):
    try:
        db_str, current_user_id = CURRENT_USER.get("db"), CURRENT_USER.get("_id")
        delete = delete.model_dump()
        obj_id = delete.get("object_id")
        obj_repo = ObjectRepository(db_str)
        obj = await obj_repo.find_one_by_id(obj_id)
        if not obj:
            raise HTTPBadRequest(f"Not found {obj_id} object by _id")
        
        record_service = RecordObjectService(db_str, obj.get("obj_id"), obj_id)
        return await record_service.delete_one_record(delete.get("record_id"), delete.get("replace"))
    
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))