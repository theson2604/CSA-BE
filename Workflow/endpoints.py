
from fastapi import APIRouter, HTTPException
from Authentication.dependencies import AuthCredentialDepend, AuthServiceDepend
from Object.schemas import ObjectSchema, ObjectWithFieldSchema
from Object.services import ObjectService
from Workflow.schemas import WorkflowSchema, WorkflowWithActionSchema
from Workflow.services import WorkflowService
from app.common.enums import SystemUserRole
from app.common.errors import HTTPBadRequest
from app.dependencies.authentication import protected_route

router = APIRouter()

@router.post("/create-workflow")
@protected_route([SystemUserRole.ADMINISTRATOR, SystemUserRole.USER])
async def create_workflow(
    workflow: WorkflowSchema,
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
        
# @router.post("/create-object-with-fields")
# @protected_route([SystemUserRole.ADMINISTRATOR, SystemUserRole.USER])
# async def create_object_with_fields(
#     obj_with_fields: ObjectWithFieldSchema,
#     CREDENTIALS: AuthCredentialDepend,
#     AUTHEN_SERVICE: AuthServiceDepend,
#     CURRENT_USER = None
# ):
#     try:
#         db_str, current_user_id = CURRENT_USER.get("db"), CURRENT_USER.get("_id")
#         obj_service = ObjectService(db_str)
#         return await obj_service.create_object_with_fields(obj_with_fields, current_user_id)
#     except Exception as e:
#         if isinstance(e, HTTPException):
#             raise e
#         if isinstance(e, Exception):
#             raise HTTPBadRequest(str(e))
        
# @router.get("/get-all-objects-with-field-details")
# @protected_route([SystemUserRole.ADMINISTRATOR, SystemUserRole.USER])
# async def get_all_objects(
#     CREDENTIALS: AuthCredentialDepend,
#     AUTHEN_SERVICE: AuthServiceDepend,
#     CURRENT_USER = None
# ):
#     try:
#         db_str = CURRENT_USER.get("db")
#         obj_service = ObjectService(db_str)
#         return await obj_service.get_all_objects_with_field_details()
#     except Exception as e:
#         if isinstance(e, HTTPException):
#             raise e
#         if isinstance(e, Exception):
#             raise HTTPBadRequest(str(e))
        
# @router.get("/get-detail-object")
# @protected_route([SystemUserRole.ADMINISTRATOR, SystemUserRole.USER])
# async def get_detail_object_by_id(
#     id: str,
#     CREDENTIALS: AuthCredentialDepend,
#     AUTHEN_SERVICE: AuthServiceDepend,
#     CURRENT_USER = None
# ):
#     try:
#         db_str = CURRENT_USER.get("db")
#         obj_service = ObjectService(db_str)
#         return await obj_service.get_object_detail_by_id(id)
#     except Exception as e:
#         if isinstance(e, HTTPException):
#             raise e
#         if isinstance(e, Exception):
#             raise HTTPBadRequest(str(e))
        
# @router.delete("/delete-one")
# @protected_route([SystemUserRole.ADMINISTRATOR, SystemUserRole.USER])
# async def delete_one_object(
#     object_id: str,
#     CREDENTIALS: AuthCredentialDepend,
#     AUTHEN_SERVICE: AuthServiceDepend,
#     CURRENT_USER = None
# ):
#     try:
#         object_service = ObjectService(CURRENT_USER.get("db"))
#         await object_service.delete_one_object_by_id(object_id)
#         return "Object has been deleted"
#     except Exception as e:
#         if isinstance(e, HTTPException):
#             raise e
#         if isinstance(e, Exception):
#             raise HTTPBadRequest(str(e))