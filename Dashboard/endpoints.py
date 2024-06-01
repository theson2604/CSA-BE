from typing import List
from fastapi import APIRouter, HTTPException
from Authentication.dependencies import AuthCredentialDepend, AuthServiceDepend
from Dashboard.repository import DashboardRepository
from Dashboard.schemas import DashboardSchema, UpdateDashboardSchema
from Dashboard.services import DashboardService
from Object.repository import ObjectRepository
from RecordObject.repository import RecordObjectRepository
from app.common.enums import DashboardType, SystemUserRole
from app.common.errors import HTTPBadRequest
from app.dependencies.authentication import protected_route
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

@router.post("/create-dashboard")
@protected_route([SystemUserRole.ADMINISTRATOR, SystemUserRole.USER])
async def create_one(
    dashboard: DashboardSchema,
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    try:
        db_str, current_user_id = CURRENT_USER.get("db"), CURRENT_USER.get("_id")
        dashboard_service = DashboardService(db_str)
        return await dashboard_service.create_one_dashboard(dashboard, current_user_id)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
    if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))
    
@router.post("/create-many-dashboards")
@protected_route([SystemUserRole.ADMINISTRATOR, SystemUserRole.USER])
async def create_many(
    dashboards: List[DashboardSchema],
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    try:
        db_str, current_user_id = CURRENT_USER.get("db"), CURRENT_USER.get("_id")
        dashboard_service = DashboardService(db_str)
        return await dashboard_service.create_many_dashboards(dashboards, current_user_id)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
    if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))
    
@router.get("/get-one-by-id")
@protected_route([SystemUserRole.ADMINISTRATOR, SystemUserRole.USER])
async def get_one(
    id: str,
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    try:
        db_str, current_user_id = CURRENT_USER.get("db"), CURRENT_USER.get("_id")
        dashboard_service = DashboardService(db_str)
        return await dashboard_service.get_one_by_id(id)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))
        
@router.get("/get-all-by-object-id")
@protected_route([SystemUserRole.ADMINISTRATOR, SystemUserRole.USER])
async def get_all_dashboard_by_object_id(
    id: str,
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    try:
        db_str, current_user_id = CURRENT_USER.get("db"), CURRENT_USER.get("_id")
        obj_repo = ObjectRepository(db_str)
        if not (await obj_repo.find_one_by_id(id)):
            raise HTTPBadRequest(f"Can not find object by id {id}")

        dashboard_service = DashboardService(db_str)
        return await dashboard_service.get_all_by_object_id(id)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))
        
@router.get("/get-all")
@protected_route([SystemUserRole.ADMINISTRATOR, SystemUserRole.USER])
async def get_all(
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    try:
        db_str, current_user_id = CURRENT_USER.get("db"), CURRENT_USER.get("_id")
        dashboard_service = DashboardService(db_str)
        return await dashboard_service.get_all_components()
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))
        
@router.post("/update-one-by-id")
@protected_route([SystemUserRole.ADMINISTRATOR, SystemUserRole.USER])
async def update_one(
    dashboard: UpdateDashboardSchema,
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    try:
        db_str, current_user_id = CURRENT_USER.get("db"), CURRENT_USER.get("_id")
        dashboard_repo = DashboardRepository(db_str)
        dashboard_dump = dashboard.model_dump()
        dashboard_id = dashboard_dump.get("dashboard_id")
        if not dashboard_id or not (await dashboard_repo.find_one_by_id(dashboard_id)):
            raise HTTPBadRequest(f"Can not find Dashboard by id {dashboard_id}")

        dashboard_service = DashboardService(db_str)
        return await dashboard_service.update_one_by_id(dashboard, current_user_id)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))

@router.delete("/delete-one-by-id")
@protected_route([SystemUserRole.ADMINISTRATOR, SystemUserRole.USER])
async def delete_one(
    id: str,
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    try:
        db_str, current_user_id = CURRENT_USER.get("db"), CURRENT_USER.get("_id")
        dashboard_repo = DashboardRepository(db_str)
        if not (await dashboard_repo.find_one_by_id(id)):
            raise HTTPBadRequest(f"Can not find Dashboard by id {id}")

        dashboard_service = DashboardService(db_str)
        return await dashboard_service.delete_one_by_id(id)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))
        
@router.delete("/delete-all-by-object-id")
@protected_route([SystemUserRole.ADMINISTRATOR, SystemUserRole.USER])
async def delete_all_by_object_id(
    id: str,
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    try:
        db_str, current_user_id = CURRENT_USER.get("db"), CURRENT_USER.get("_id")
        obj_repo = ObjectRepository(db_str)
        if not (await obj_repo.find_one_by_id(id)):
            raise HTTPBadRequest(f"Object with id {id} does not have any dashboard")

        dashboard_service = DashboardService(db_str)
        return await dashboard_service.delete_all_by_object_id(id)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))