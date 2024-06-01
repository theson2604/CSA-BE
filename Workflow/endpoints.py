
from typing import List
from fastapi import APIRouter, HTTPException
from Authentication.dependencies import AuthCredentialDepend, AuthServiceDepend
from Object.repository import ObjectRepository
from Object.schemas import ObjectSchema, ObjectWithFieldSchema
from Object.services import ObjectService
from Workflow.repository import WorkflowRepository
from Workflow.schemas import UpdateWorkflowSchema, WorkflowSchema, WorkflowWithActionSchema
from Workflow.services import WorkflowService
from app.common.enums import SystemUserRole
from app.common.errors import HTTPBadRequest
from app.dependencies.authentication import protected_route

router = APIRouter()

@router.post("/create-workflow")
@protected_route([SystemUserRole.ADMINISTRATOR, SystemUserRole.USER])
async def create_workflow(
    workflow: UpdateWorkflowSchema,
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    try:
        db_str, current_user_id = CURRENT_USER.get("db"), CURRENT_USER.get("_id")
        workflow_service = WorkflowService(db_str)
        return await workflow_service.create_workflow(workflow, current_user_id)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))
        
@router.post("/create-workflow-with-actions")
@protected_route([SystemUserRole.ADMINISTRATOR, SystemUserRole.USER])
async def create_workflow_with_actions(
    workflow_with_actions: WorkflowWithActionSchema,
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    try:
        db_str, current_user_id = CURRENT_USER.get("db"), CURRENT_USER.get("_id")
        workflow_service = WorkflowService(db_str)
        return await workflow_service.create_workflow_with_actions(workflow_with_actions, current_user_id)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))
        
@router.get("/get-all-workflows")
@protected_route([SystemUserRole.ADMINISTRATOR, SystemUserRole.USER])
async def get_all_workflows(
    object_id: str,
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    try:
        db_str, current_user_id = CURRENT_USER.get("db"), CURRENT_USER.get("_id")
        obj_repo = ObjectRepository(db_str)
        if not await obj_repo.find_one_by_id(object_id):
            raise HTTPBadRequest(f"Can not find object by id {object_id}")
        
        workflow_service = WorkflowService(db_str)
        return await workflow_service.get_all_workflows_by_object_id(object_id)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))
        
@router.get("/get-workflow-with-actions")
@protected_route([SystemUserRole.ADMINISTRATOR, SystemUserRole.USER])
async def get_all_workflows(
    workflow_id: str,
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    try:
        db_str, current_user_id = CURRENT_USER.get("db"), CURRENT_USER.get("_id")
        workflow_repo = WorkflowRepository(db_str)
        if not await workflow_repo.find_one_by_id(workflow_id):
            raise HTTPBadRequest(f"Can not find workflow by id {workflow_id}")
        
        workflow_service = WorkflowService(db_str)
        return await workflow_service.get_workflow_with_all_actions(workflow_id)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))
        
@router.post("/update-one-by-id")
@protected_route([SystemUserRole.ADMINISTRATOR, SystemUserRole.USER])
async def update_one(
    workflow: UpdateWorkflowSchema,
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    try:
        db_str, current_user_id = CURRENT_USER.get("db"), CURRENT_USER.get("_id")
        workflow_service = WorkflowService(db_str)
        return await workflow_service.update_one_workflow(workflow, current_user_id)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))
        
@router.post("/update-many")
@protected_route([SystemUserRole.ADMINISTRATOR, SystemUserRole.USER])
async def update_many(
    workflows: List[UpdateWorkflowSchema],
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    try:
        db_str, current_user_id = CURRENT_USER.get("db"), CURRENT_USER.get("_id")
        workflow_service = WorkflowService(db_str)
        return await workflow_service.update_many_workflows(workflows, current_user_id)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))
        
@router.delete("/delete-workflow-and-actions")
@protected_route([SystemUserRole.ADMINISTRATOR, SystemUserRole.USER])
async def delete_workflow_and_actions(
    id: str,
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    try:
        db_str, current_user_id = CURRENT_USER.get("db"), CURRENT_USER.get("_id")
        workflow_service = WorkflowService(db_str)
        return await workflow_service.delete_workflow_and_actions_by_id(id)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))