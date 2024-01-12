from typing_extensions import Annotated
from fastapi import APIRouter, Depends, HTTPException
from Authentication.dependencies import AuthCredentialDepend, AuthServiceDepend
from RootAdministrator.dependencies import RootAdminServiceDepend
from RootAdministrator.schemas import AdminSchema, UpdateAdminSchema, UserSchema, UpdateUserSchema
from app.common.enums import SystemUserRole
from app.dependencies.authentication import protected_route

router = APIRouter()

@router.post("/create-admin")
@protected_route(SystemUserRole.ROOT)
async def create_admin(
    admin: AdminSchema,
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    root_service: RootAdminServiceDepend, 
    CURRENT_USER = None
):
    return "Admin has been created" if await root_service.create_system_admin(admin) else HTTPException(status_code=400, detail="Fail to create Admin")

@router.get("/get-all-admins")
@protected_route(SystemUserRole.ROOT)
async def get_all_admins(
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    root_service: RootAdminServiceDepend,
    page: int = 1,
    page_size: int = 100,
    CURRENT_USER = None):
    res = {
        "count": await root_service.count_all_admin(),
        "data": await root_service.find_all_system_admins(page, page_size)
    }
    return res

@router.post("/update-admin")
@protected_route(SystemUserRole.ROOT)
async def update_admin(
    admin: UpdateAdminSchema,
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    root_service: RootAdminServiceDepend,
    CURRENT_USER = None):
    
    return "Admin has been updated" if await root_service.update_admin(admin) else HTTPException(status_code=400, detail="Fail to update Admin")

@router.post("/create-user")
@protected_route(SystemUserRole.ADMINISTRATOR)
async def create_user(
    user: UserSchema,
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    root_service: RootAdminServiceDepend,
    CURRENT_USER = None
):
    db = CURRENT_USER.get("db")
    res = await root_service.create_system_user(user, db)
    return res if res  else HTTPException(status_code=400, detail="Fail to create User")

@router.get("/get-all-users")
@protected_route(SystemUserRole.ADMINISTRATOR)
async def get_all_users(
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    root_service: RootAdminServiceDepend,
    page: int = 1,
    page_size: int = 100,
    CURRENT_USER = None
):
    
    db = CURRENT_USER.get("db")
    res = {
        "count": await root_service.count_all_company_user(db),
        "data": await root_service.find_all_company_users(db , page, page_size)
    }
    return res

@router.post("/update-user")
@protected_route(SystemUserRole.ADMINISTRATOR)
async def update_user(
    user: UpdateUserSchema,
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    root_service: RootAdminServiceDepend,
    CURRENT_USER = None):
    
    return "User has been updated" if await root_service.update_user(user) else HTTPException(status_code=400, detail="Fail to update User")