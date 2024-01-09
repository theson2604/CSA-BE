from fastapi import APIRouter, Depends
from RootAdministrator.schemas import AdminSchema

from RootAdministrator.services import RootAdministratorServices


router = APIRouter()


@router.post("/create_admin")
async def create_admin(admin: AdminSchema, root_service: RootAdministratorServices = Depends(RootAdministratorServices)):
    await root_service.create_system_admin(admin)
    return "Ok"