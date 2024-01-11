from typing_extensions import Annotated
from fastapi import APIRouter, Depends, HTTPException
from Authentication.dependencies import AuthCredentialDepend, AuthServiceDepend
from GroupObjects.schemas import GroupObjectSchema
from GroupObjects.services import GroupObjectServices
from app.common.enums import SystemUserRole
from app.dependencies.authentication import protected_route

router = APIRouter()

@router.post("/create")
@protected_route(SystemUserRole.ADMINISTRATOR)
async def create_group(
    group: GroupObjectSchema,
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    group_object_service = GroupObjectServices(CURRENT_USER.get("db"))
    return "Group Object has been created" if await group_object_service.create_group(group) else HTTPException(status_code=400, detail="Fail to create Group Object")