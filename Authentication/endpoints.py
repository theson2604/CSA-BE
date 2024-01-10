from fastapi import APIRouter, Depends, status
from Authentication.dependencies import AuthServiceDepend
from Authentication.schemas import LoginSchema

router = APIRouter()

@router.post("/login", status_code=status.HTTP_200_OK)
async def login(login_info: LoginSchema, authen_service: AuthServiceDepend):
    # await root_service.create_system_admin(admin)
    login_info = login_info.model_dump()
    return await authen_service.validate_user(email=login_info.get("email"), pwd=login_info.get("pwd"))