from typing import List
from typing_extensions import Annotated
from fastapi import APIRouter, Depends, HTTPException
from Authentication.dependencies import AuthCredentialDepend, AuthServiceDepend
from GroupObjects.schemas import GroupObjectSchema, UpdateGroupObjectSchema
from GroupObjects.services import GroupObjectServices
from app.common.enums import SystemUserRole
from app.common.errors import HTTPBadRequest
from app.dependencies.authentication import protected_route

router = APIRouter()

@router.post("/create")
@protected_route([SystemUserRole.ADMINISTRATOR])
async def create_group(
    group: GroupObjectSchema,
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    try:
        group_object_service = GroupObjectServices(CURRENT_USER.get("db"))
        return await group_object_service.create_group(group)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))

@router.post("/update-many")
@protected_route([SystemUserRole.ADMINISTRATOR])
async def update_many_groups(
    groups: List[UpdateGroupObjectSchema],
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    group_object_service = GroupObjectServices(CURRENT_USER.get("db"))
    return await group_object_service.update_many_groups(groups)

@router.post("/update-one")
@protected_route([SystemUserRole.ADMINISTRATOR])
async def update_one_group(
    group: UpdateGroupObjectSchema,
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    try:
        group_object_service = GroupObjectServices(CURRENT_USER.get("db"))
        await group_object_service.update_one_group(group)
        return "Group has been updated"
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))

@router.get("/get-detail-group")
@protected_route([SystemUserRole.ADMINISTRATOR])
async def get_detail_group_by_id(
    group_id: str,
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    try:
        group_object_service = GroupObjectServices(CURRENT_USER.get("db"))
        return await group_object_service.get_detail_group_by_id(group_id)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))

@router.get("/get-all-groups")
@protected_route([SystemUserRole.ADMINISTRATOR])
async def get_all_groups(
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    try:
        group_object_service = GroupObjectServices(CURRENT_USER.get("db"))
        return await group_object_service.get_all_groups()
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))

@router.get("/get-all-user-groups")
@protected_route([SystemUserRole.USER])
async def get_all_groups(
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    try:
        group_object_service = GroupObjectServices(CURRENT_USER.get("db"))
        return await group_object_service.get_all_user_groups(CURRENT_USER.get("_id"))
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))