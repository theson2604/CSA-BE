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

@router.post("/config-preprocess")
@protected_route([SystemUserRole.ADMINISTRATOR])
async def config(
    config: DatasetConfigSchema,
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    try:
        db_str, current_user_id = CURRENT_USER.get("db"), CURRENT_USER.get("_id")
        task = activate_preprocess_dataset.delay(db_str, config, current_user_id, CREDENTIALS.credentials)
        # return await service.config_preprocess_dataset(config, current_user_id, CREDENTIALS.credentials)
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))