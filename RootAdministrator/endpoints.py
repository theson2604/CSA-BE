from typing_extensions import Annotated
from fastapi import APIRouter, Depends
from Authentication.dependencies import AuthCredentialDepend, AuthServiceDepend
from RootAdministrator.dependencies import RootAdminService
from RootAdministrator.schemas import AdminSchema
from app.common.enums import SystemUserRole
from app.dependencies.authentication import protected_route

router = APIRouter()

@router.post("/create-admin")
@protected_route(SystemUserRole.ROOT)
async def create_admin(admin: AdminSchema,
                       credentials: AuthCredentialDepend,
                       authen_service: AuthServiceDepend,
                       root_service: RootAdminService, 
                       current_user = None):
    
    await root_service.create_system_admin(admin)
    return "Admin has been created"