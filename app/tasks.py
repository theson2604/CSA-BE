import asyncio
import json
from celery.result import AsyncResult
from celery.schedules import crontab, schedule
from typing import List, Tuple

from fastapi import WebSocket
from DatasetAI.schemas import DatasetConfigSchema
from DatasetAI.services import DatasetAIServices
from FieldObject.repository import FieldObjectRepository
from FieldObject.schemas import FieldObjectSchema
from FieldObject.services import FieldObjectService
from InboundRule.services import InboundRule
from MailService.repository import MailServiceRepository
from MailService.services import MailServices
from Notification.services import NotificationService
from Object.repository import ObjectRepository
from RecordObject.models import RecordObjectModel
from RecordObject.repository import RecordObjectRepository
from RecordObject.services import RecordObjectService
from app.celery import celery as clr, redis_client
import time

from app.common.db_connector import DBCollections
from app.common.enums import ActionType, TaskStatus
from app.common.utils import get_current_hcm_datetime

async def monitor_tasks(clients: List[WebSocket]):
    while True:
        tasks_info = clr.control.inspect().active() # {worker_name : [{task_info}]}
        await asyncio.sleep(0.1)
        for task_id in tasks_info[list(tasks_info.keys())[0]]:
            result = AsyncResult(task_id["id"])
            if result.ready():
                await NotificationService.send_one(task_id["id"], result, clients)
            else:
                print("NOT READY")

# @clr.task()
# def monitor_tasks():
#     tasks_info = clr.control.inspect().active() # {worker_name : [{task_info}]}
#     asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.1))
#     for task_id in tasks_info[list(tasks_info.keys())[0]]:
#         result = AsyncResult(task_id["id"])
#         if result.ready():
#             asyncio.get_running_loop().run_until_complete(NotificationService.send_one(task_id["id"], result))
#         else:
#             print("NOT READY")

def set_task_metadata(task_id: str, metadata: dict):
    return redis_client.set(task_id, json.dumps(metadata))

def get_task_metadata(task_id: str):
    return redis_client.get(task_id)

def print_info(self):
    print(f"{self.name} has parent with task id {self.request.parent_id}")
    print(f"chain of {self.name}: {self.request.chain}")
    print(f"self.request.id: {self.request.id}")

@clr.task(bind=True)
def add(self, a, t):
    # print_info(self)

    # time.sleep(t)
    return a+1

@clr.task()
def test_scan_mail(db: str, mail: dict, obj_id: str, admin_id: str):
    mail_service = MailServices(db, obj_id)
    # result = async_to_sync(record_repo.find_one_by_id)(id = "6621547dd478411eb0ad46a6")
    result = asyncio.get_event_loop().run_until_complete(mail_service.scan_email(mail, admin_id))

    return result

@clr.task()
def scan_email() -> List[dict]:
    mail_repo = MailServiceRepository()
    system_emails = asyncio.get_event_loop().run_until_complete(mail_repo.find_many_email({}, {"created_at": 0, "modified_at": 0}))
    for system_email in system_emails:
        mail_service = MailServices(system_email.get("db_str"), DBCollections.REPLY_EMAIL)
        contents = asyncio.get_event_loop().run_until_complete(mail_service.scan_email(system_email))

    return contents

# @clr.task()
# def scan_email():
#     return asyncio.run(scan_email_async())

async def scan_email_async():
    mail_repo = MailServiceRepository()
    system_emails = await mail_repo.find_many_email({}, {"email": 1, "db_str": 1})
    
    async def process_email(system_email):
        db_str = system_email.get("email")
        mail_service = MailServices(db_str)
        scan_schema = {
            "template": system_email.get("template_id"),
            "email": system_email.get("email")
        }
        contents = await mail_service.scan_email(scan_schema, db_str, system_email.get("admin_id"))
        return contents

    tasks = [process_email(email) for email in system_emails]
    results = await asyncio.gather(*tasks)
    
    return results

# DONE
@clr.task(name = "send_email")
def activate_send(db: str, action: dict, record_id: str) -> str:
    object_id = action.get("object_id")
    obj_repo = ObjectRepository(db)
    obj = asyncio.get_event_loop().run_until_complete(obj_repo.find_one_by_id(object_id))
    obj_id = obj.get("obj_id")

    record_repo = RecordObjectRepository(db, obj_id)
    record = asyncio.get_event_loop().run_until_complete(record_repo.get_one_by_id_with_parsing_ref_detail(record_id, object_id))[0]
    mail_service = MailServices(db, obj_id)
    mail = {
        "email": action.get("from"),
        "send_to": action.get("to"),
        "template": action.get("template_id"),
        "object": action.get("object_id")
    }
    result = asyncio.get_event_loop().run_until_complete(mail_service.send_one(mail, db, record))
    return result

# DONE
@clr.task(name = "create_record")
def activate_create(
    db: str, action: dict, user_id: str, contents: List[str]
) -> Tuple[List[RecordObjectModel], str]:
    object_id = action.get("object_id")
    obj_repo = ObjectRepository(db)
    obj = asyncio.get_event_loop().run_until_complete(obj_repo.find_one_by_id(object_id))
    obj_id = obj.get("obj_id")
    record = {
        "object_id": object_id
    }
    if action.get("field_configs"):
        for field_config in action.get("field_configs"):
            record.update(field_config)

    record_service = RecordObjectService(db, obj_id, object_id)

    results = []
    if action.get("option") == "no":
        results.append(asyncio.get_event_loop().run_until_complete(record_service.create_record(record, user_id)))
    else:
        parent_info = contents.pop()
        field_repo = FieldObjectRepository(db)
        ref_parent_field = asyncio.get_event_loop().run_until_complete(field_repo.find_one(
            {"field_name": parent_info.get("ref_obj_name"), "object_id": object_id, "field_type": "ref_obj"}
        ))
        if not ref_parent_field:
            field_service = FieldObjectService(db)
            field_schema = {
                "field_type": "ref_obj",
                "field_name": parent_info.get("ref_obj_name"),
                "object_id": object_id,
                "sorting_id": len(asyncio.get_event_loop().run_until_complete(field_service.get_all_fields_by_obj_id(object_id))),
                "src": parent_info.get("ref_obj_id"),
                "cascade_option": "delete"
            }
            ref_parent_field_id = asyncio.get_event_loop().run_until_complete(
                field_service.create_one_field(FieldObjectSchema.model_validate(field_schema).model_dump())
            )
        else:
            ref_parent_field_id = ref_parent_field.get("_id")

        
        ref_parent_field = asyncio.get_event_loop().run_until_complete(
                field_repo.find_one_by_id(ref_parent_field_id)
            )
        parent_field_id = asyncio.get_event_loop().run_until_complete(
            field_repo.find_one_by_field_type(parent_info.get("ref_obj_id"), "id")
        ).get("field_id")
        parent_record_repo = RecordObjectRepository(db, parent_info.get("ref_obj_id_str"))
        
        for content in contents:
            if action.get("field_contents"):
                for field in action.get("field_contents"):
                    record[field] = content.get("body")

            print("PARENT_FIELD_IDDDDD :" , parent_field_id, content.get("record_prefix"))
            parent_record = asyncio.get_event_loop().run_until_complete(
                parent_record_repo.find_one({parent_field_id: content.get("record_prefix")})
            )
            if parent_record:
                record[ref_parent_field.get("field_id")] = parent_record.get("_id")
            record["object_id"] = object_id
            result = asyncio.get_event_loop().run_until_complete(record_service.create_record(record, user_id))
            if result:
                results.append(result)
    
    field_repo = FieldObjectRepository(db)
    fd_id = (asyncio.get_event_loop().run_until_complete(field_repo.find_one_by_field_type(object_id, "id"))).get("field_id")
    record_repo = RecordObjectRepository(db, obj_id)
    results = asyncio.get_event_loop().run_until_complete(record_repo.find_all({"_id": {"$in": results}}, {"object_id": 1, fd_id: 1}))
    return results, fd_id


# DONE
@clr.task(name = "update_record")
def activate_update(
    db: str, action: dict, user_id: str, record_id: str, contents: List[str]
) -> Tuple[List[RecordObjectModel], str]:
    object_id = action.get("object_id")
    obj_repo = ObjectRepository(db)
    obj = asyncio.get_event_loop().run_until_complete(obj_repo.find_one_by_id(object_id))
    obj_id = obj.get("obj_id")
    field_repo = FieldObjectRepository(db)
    fd_id = (asyncio.get_event_loop().run_until_complete(field_repo.find_one_by_field_type(object_id, "id"))).get("field_id")
    result = []
    record_service = RecordObjectService(db, obj_id, object_id)

    if len(contents) != 0:
        contents.pop() #{"ref_obj_name": obj_name, "ref_obj_id": object_id}
        record_repo = RecordObjectRepository(db, obj_id)
        for content in contents:
            record_prefix = content.get("record_prefix")
            record = {}
            for field_config in action.get("field_configs"):
                record.update(field_config)

            #switch to record_service.update_one_record to trigger worfkflow
            result += asyncio.get_event_loop().run_until_complete(record_repo.update_and_get_one({fd_id: record_prefix}, record))
            # result += asyncio.get_event_loop().run_until_complete(record_service.update_one_record({fd_id: record_prefix}, record))

    else:
        record = {
            "record_id": record_id,
            "object_id": object_id
        }
        for field_config in action.get("field_configs"):
            record.update(field_config)

        result += asyncio.get_event_loop().run_until_complete(record_service.update_one_record(record, user_id))

    return result, fd_id

@clr.task(name = "inbound_file")
def activate_inbound(db, file_inbound: dict, obj_id: str, user_id: str) -> Tuple[str, int, int]:
    config = file_inbound.get("config")
    inbound_service = InboundRule(db, config.get("object"), obj_id)
    result = asyncio.get_event_loop().run_until_complete(inbound_service.inbound_file(file_inbound, user_id))
    return result

@clr.task(name = "inbound_file_with_obj")
def activate_inbound_with_new_obj(db, config: dict, user_id: str, df: str) -> Tuple[str, int, int]:
    inbound_service = InboundRule(db)
    result = asyncio.get_event_loop().run_until_complete(inbound_service.inbound_file_with_new_obj(user_id, config, df))
    return result

@clr.task(name = "preprocess_dataset")
def activate_preprocess_dataset(db_str: str, config: dict, cur_user_id: str, access_token: str):
    dataset_service = DatasetAIServices(db_str)
    result = asyncio.get_event_loop().run_until_complete(dataset_service.config_preprocess_dataset(config, cur_user_id, access_token))
    return result

@clr.task(name = "activate_score_sentiment")
def activate_score_sentiment(db_str, config: dict, record_id: str, cur_user_id: str, access_token: str):
    dataset_service = DatasetAIServices(db_str)
    result = asyncio.get_event_loop().run_until_complete(dataset_service.infer_sentiment_score(db_str, config, record_id, cur_user_id, access_token))
    return result

def trigger_task(task_name):
    periodic_task_id = f'{task_name}_periodic_task'
    clr.conf.beat_schedule = {'print_num_periodic_task': {
            'task': 'app.tasks.print_num',
            'schedule': 5.0,  # Run every 5 seconds
            },
        }


@clr.task()
def test_asyncio_run(t):
    result = asyncio.run(test(t))
    print("RESULT: ", result)
    return result

async def test(t):
    print("hello")
    await asyncio.sleep(t)
    print(f"AFTER {t} seconds")
    return True