from typing_extensions import Annotated
from fastapi import APIRouter, Depends, HTTPException
from Authentication.dependencies import AuthCredentialDepend, AuthServiceDepend
from GroupObjects.schemas import GroupObjectSchema, UpdateGroupObjectSchema
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

@router.post("/update")
@protected_route(SystemUserRole.ADMINISTRATOR)
async def update_group(
    group: UpdateGroupObjectSchema,
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    group_object_service = GroupObjectServices(CURRENT_USER.get("db"))
    return "Group Object has been updated" if await group_object_service.update_group(group) else HTTPException(status_code=400, detail="Fail to update Group Object")

@router.get("/get-detail-group")
@protected_route(SystemUserRole.ADMINISTRATOR)
async def get_detail_group_by_id(
    group_id: str,
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    group_object_service = GroupObjectServices(CURRENT_USER.get("db"))
    group = await group_object_service.get_detail_group_by_id(group_id)
    return group if group else HTTPException(status_code=400, detail="No Group Object")

@router.get("/get-all-groups")
@protected_route(SystemUserRole.ADMINISTRATOR)
async def get_all_groups(
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    group_object_service = GroupObjectServices(CURRENT_USER.get("db"))
    groups = await group_object_service.get_all_groups()
    return groups if groups else HTTPException(status_code=400, detail="No Group Object")