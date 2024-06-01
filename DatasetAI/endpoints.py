import re
from fastapi import APIRouter, HTTPException
from Authentication.dependencies import AuthCredentialDepend, AuthServiceDepend
from DatasetAI.schemas import DatasetConfigSchema
from DatasetAI.services import DatasetAIServices
from app.common.enums import SystemUserRole
from app.common.errors import HTTPBadRequest
from app.dependencies.authentication import protected_route
from dotenv import load_dotenv
import os

from app.tasks import activate_preprocess_dataset

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
        # return await service.config_preprocess_dataset(config, current_user_id, CREDENTIALS.credentials)
        return {"task_id": task.id}
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))
        
        
@router.get("/detail")
@protected_route([SystemUserRole.ADMINISTRATOR])
async def config(
    dataset_id_str: str,
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    try:
        db_str, current_user_id = CURRENT_USER.get("db"), CURRENT_USER.get("_id")
        regex_obj_str = r"^obj_\w+_\d{6}$"
        # obj_id_str
        match = re.search(regex_obj_str, dataset_id_str)
        if not match:
            raise ValueError(f"invalid 'dataset_id_str' {dataset_id_str}. It must be {regex_obj_str}.")
        
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))