from typing import List
from fastapi import APIRouter, HTTPException
from Action.schemas import ActionSchema, UpdateActionSchema
from Action.services import ActionService
from Authentication.dependencies import AuthCredentialDepend, AuthServiceDepend
from app.common.enums import SystemUserRole
from app.common.errors import HTTPBadRequest
from app.dependencies.authentication import protected_route
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

@router.post("/create-action")
@protected_route([SystemUserRole.ADMINISTRATOR, SystemUserRole.USER])
async def create_action(
    action: ActionSchema,
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    try:
        db_str, current_user_id = CURRENT_USER.get("db"), CURRENT_USER.get("_id")
        action_service = ActionService(db_str)
        return await action_service.create_one_action(action, current_user_id)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))
        
@router.get("/get-action-details")
@protected_route([SystemUserRole.ADMINISTRATOR, SystemUserRole.USER])
async def get_action(
    action_id: str,
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    try:
        db_str, current_user_id = CURRENT_USER.get("db"), CURRENT_USER.get("_id")
        action_service = ActionService(db_str)
        return await action_service.get_action_details(action_id)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))
        
@router.post("/update-one-by-id")
@protected_route([SystemUserRole.ADMINISTRATOR, SystemUserRole.USER])
async def update_one(
    action: UpdateActionSchema,
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    try:
        db_str, current_user_id = CURRENT_USER.get("db"), CURRENT_USER.get("_id")
        action_service = ActionService(db_str)
        return await action_service.update_one_action(action)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))
        
@router.delete("/delete-action")
@protected_route([SystemUserRole.ADMINISTRATOR, SystemUserRole.USER])
async def delete_action(
    id: str,
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    try:
        db_str, current_user_id = CURRENT_USER.get("db"), CURRENT_USER.get("_id")
        action_service = ActionService(db_str)
        return await action_service.delete_one_action_by_id(id)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))
