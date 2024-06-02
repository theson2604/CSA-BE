import re
from fastapi import APIRouter, HTTPException
from Authentication.dependencies import AuthCredentialDepend, AuthServiceDepend
from SentimentAnalysis.services import SentimentAnalysisServices
from app.common.enums import SystemUserRole
from app.common.errors import HTTPBadRequest
from app.dependencies.authentication import protected_route
from dotenv import load_dotenv
import os


load_dotenv()

router = APIRouter()
        
        
@router.get("/get-all-models-with-details")
@protected_route([SystemUserRole.ADMINISTRATOR])
async def get_all_models_with_details(
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    try:        
        db_str, current_user_id = CURRENT_USER.get("db"), CURRENT_USER.get("_id")
        service = SentimentAnalysisServices(db_str)
        return await service.get_all_models_with_details()
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))
        
        
@router.get("/get-all-models-prototype")
@protected_route([SystemUserRole.ADMINISTRATOR])
async def get_all_models_prototype(
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    try:        
        db_str, current_user_id = CURRENT_USER.get("db"), CURRENT_USER.get("_id")
        service = SentimentAnalysisServices(db_str)
        return await service.get_all_models_prototype()
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))