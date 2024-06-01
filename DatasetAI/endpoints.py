import re
from fastapi import APIRouter, HTTPException
from Authentication.dependencies import AuthCredentialDepend, AuthServiceDepend
from DatasetAI.schemas import DatasetConfigSchema
from DatasetAI.services import DatasetAIServices
from app.common.enums import ActionType, SystemUserRole
from app.common.errors import HTTPBadRequest
from app.dependencies.authentication import protected_route
from dotenv import load_dotenv
import os

from app.tasks import activate_preprocess_dataset, set_task_metadata

load_dotenv()

router = APIRouter()

@router.post("/preprocess")
@protected_route([SystemUserRole.ADMINISTRATOR])
async def config(
    config: DatasetConfigSchema,
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    try:
        db_str, current_user_id = CURRENT_USER.get("db"), CURRENT_USER.get("_id")
        config = config.model_dump()
        task = activate_preprocess_dataset.delay(db_str, config, current_user_id, CREDENTIALS.credentials)
        set_task_metadata(task.id, {"type": ActionType.PREPROCESS_DATASET})
        # return await service.config_preprocess_dataset(config, current_user_id, CREDENTIALS.credentials)
        return {"task_id": task.id, "type": ActionType.PREPROCESS_DATASET}
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))
        
        
@router.get("/get-detail-by-id")
@protected_route([SystemUserRole.ADMINISTRATOR])
async def get_detail_by_id(
    dataset_obj_id: str,
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    try:
        db_str, current_user_id = CURRENT_USER.get("db"), CURRENT_USER.get("_id")
        service = DatasetAIServices(db_str)
        return await service.get_detail(dataset_obj_id=dataset_obj_id)
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))
        
        
@router.get("/get-detail-by-id-str")
@protected_route([SystemUserRole.ADMINISTRATOR])
async def get_detail_by_id_str(
    dataset_obj_id_str: str,
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    try:
        regex_str = r"^obj_\w+_\d{6}$"
        match = re.search(regex_str, dataset_obj_id_str)
        if not match:
            raise ValueError(f"invalid 'dataset_obj_id_str' {dataset_obj_id_str}. It must be {regex_str}")
        
        db_str, current_user_id = CURRENT_USER.get("db"), CURRENT_USER.get("_id")
        service = DatasetAIServices(db_str)
        return await service.get_detail(dataset_obj_id_str=dataset_obj_id_str)
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))
        
        
@router.get("/get-all-models")
@protected_route([SystemUserRole.ADMINISTRATOR])
async def get_all_models(
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    try:        
        db_str, current_user_id = CURRENT_USER.get("db"), CURRENT_USER.get("_id")
        service = DatasetAIServices(db_str)
        return await service.get_all_models()
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))