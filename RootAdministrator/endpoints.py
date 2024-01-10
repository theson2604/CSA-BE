from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from RootAdministrator.schemas import AdminSchema
from RootAdministrator.services import IRootAdministratorServices, RootAdministratorServices
from app.common.enums import SystemUserRole
from app.dependencies.authentication import protected_route

router = APIRouter()
security = HTTPBearer()


@router.post("/create_admin")
@protected_route(SystemUserRole.ROOT)
async def create_admin(admin: AdminSchema,
                       credentials: HTTPAuthorizationCredentials = Depends(security),
                       root_service: IRootAdministratorServices = Depends(RootAdministratorServices)):
    # await root_service.create_system_admin(admin)
    return "Ok"