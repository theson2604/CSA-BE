import asyncio
from celery import chain, group
from celery.result import AsyncResult
from fastapi import APIRouter, Body, Form, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from Authentication.dependencies import AuthCredentialDepend, AuthServiceDepend
from InboundRule.services import InboundRule
from MailService.schemas import MailSchema
from app.tasks import create_task, add, division, test_scan_mail
from Object.repository import ObjectRepository
from app.common.enums import SystemUserRole
from app.common.errors import HTTPBadRequest
from app.dependencies.authentication import protected_route
from app.celery import celery, get_active

router = APIRouter()

@router.post("/tasks/get-task-ids")
def get_ids():
    results = []
    task_ids = []
    task_ids = celery.control.inspect().active() # {worker_name : [{task_info}]}
    # for key in task_ids.keys():
    #     return task_ids[key]
    # raise HTTPBadRequest(task_ids[list(task_ids.keys())[0]])
    for task_info in task_ids[list(task_ids.keys())[0]]:
        task_id = task_info["id"]
        result = AsyncResult(task_id)
            # raise Exception(f"REEEE: {result}")
        while not result.ready():
            asyncio.sleep(2)
        results.append({"task_id": task_id, "status": result.status, "result": result.result})
    return results

@router.post("/tasks/async")
@protected_route([SystemUserRole.ADMINISTRATOR])
async def send_mail(
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    mail: MailSchema,
    CURRENT_USER = None
):
    try:
        mail_obj = mail.model_dump()
        db = CURRENT_USER.get("db")
        admin_id = CURRENT_USER.get("_id")
        object_id = mail_obj.get("object")

        obj_repo = ObjectRepository(db)
        obj = await obj_repo.find_one_by_id(object_id)
        if not obj:
            raise HTTPBadRequest(f"Not found {object_id} object by _id")
        
        test_scan_mail.apply_async(args=(db, mail_obj, obj.get("obj_id"), admin_id))
        return True
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))

@router.post("/tasks/chain")
def test_chain(payload = Body(...)):
    num = payload["num"]
    task = group(create_task.s(7, 27), add.s(num, 11), create_task.s(3, 17), division.s(9, 0)).apply_async()
    print("CHAIN: ", task)
    return task.id

@router.post("/tasks")
def run_task(payload = Body(...)):
    value, t = payload["value"], payload["time"]
    task = create_task.delay(value, t)
    print(task)
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