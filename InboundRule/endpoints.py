from celery.result import AsyncResult
from fastapi import APIRouter, Body, Form, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from Authentication.dependencies import AuthCredentialDepend, AuthServiceDepend
from InboundRule.services import InboundRule
from InboundRule.tasks import create_task
from Object.repository import ObjectRepository
from app.common.enums import SystemUserRole
from app.common.errors import HTTPBadRequest
from app.dependencies.authentication import protected_route

router = APIRouter()

@router.post("/tasks", status_code=201)
def run_task(payload = Body(...)):
    value = payload["value"]
    task = create_task.delay(value)
    return JSONResponse({"task_id": task.id})

@router.get("/tasks/{task_id}")
def get_status(task_id):
    task_result = AsyncResult(task_id)
    result = {
        "task_id": task_id,
        "task_status": task_result.status,
        "task_result": task_result.result
    }
    return JSONResponse(result)

@router.post("/inbound-file")
@protected_route([SystemUserRole.ADMINISTRATOR])
async def inbound_file(
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    object_id: str = Form(),
    mapping: str = Form(),
    file: UploadFile = File(...),
    CURRENT_USER = None
):
    try:
        db, user_id = CURRENT_USER.get("db"), CURRENT_USER.get("_id")
        obj_repo = ObjectRepository(db)
        obj = await obj_repo.find_one_by_id(object_id)
        if not obj:
            raise HTTPBadRequest(f"Not found {object_id} object by _id")
        
        inbound_rule_service = InboundRule(db, object_id, obj.get("obj_id"))
        # inbound_rule_service = InboundRule(db, object_id)
        return await inbound_rule_service.inbound_file({"file": file, "config": {"map": mapping, "object": object_id}}, user_id)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))
        
@router.post("/inbound-file_with_new_obj")
@protected_route([SystemUserRole.ADMINISTRATOR])
async def inbound_file(
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    # config: FileObjectSchema = Depends(),
    obj_name: str = Form(),
    group_obj_id: str = Form(),
    fields: str = Form(),
    map: str = Form(),
    file: UploadFile = File(...),
    CURRENT_USER = None
):
    try:
        db, user_id = CURRENT_USER.get("db"), CURRENT_USER.get("_id")
        inbound_rule_service = InboundRule(db)
        # inbound_rule_service = InboundRule(db, object_id)
        config = {
            "obj_name": obj_name,
            "group_obj_id": group_obj_id,
            "fields": fields,
            "map": map
        }
        return await inbound_rule_service.inbound_file_with_new_obj(user_id, config, file)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))