from typing_extensions import Annotated
from fastapi import APIRouter, Depends
from Authentication.dependencies import AuthCredentialDepend, AuthServiceDepend
from RootAdministrator.dependencies import RootAdminService
from RootAdministrator.schemas import AdminSchema, UpdateAdminSchema
from app.common.enums import SystemUserRole
from app.dependencies.authentication import protected_route

router = APIRouter()

@router.post("/create-admin")
@protected_route(SystemUserRole.ROOT)
async def create_admin(
    admin: AdminSchema,
    credentials: AuthCredentialDepend,
    authen_service: AuthServiceDepend,
    root_service: RootAdminService, 
    current_user = None
):
    
    await root_service.create_system_admin(admin)
    return "Admin has been created"

@router.get("/get-all-admins")
@protected_route(SystemUserRole.ROOT)
async def get_all_admins(
    credentials: AuthCredentialDepend,
    authen_service: AuthServiceDepend,
    root_service: RootAdminService,
    page: int = 0,
    page_size: int = 100,
    current_user = None):
    
    return await root_service.find_all_system_admins(page, page_size)

@router.post("/update-admin")
@protected_route(SystemUserRole.ROOT)
async def update_admin(
    admin: UpdateAdminSchema,
    credentials: AuthCredentialDepend,
    authen_service: AuthServiceDepend,
    root_service: RootAdminService,
    current_user = None):
    
    return await root_service.update_admin(admin)