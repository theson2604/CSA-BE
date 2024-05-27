import asyncio
from typing import List
from Action.repository import ActionRepository
from MailService.schemas import MailSchema
from MailService.services import MailServices
from Object.repository import ObjectRepository
from app.common.db_connector import DBCollections, client
from celery import chain, group, shared_task, Celery
from RecordObject.repository import RecordObjectRepository
from RecordObject.services import RecordObjectService
from app.celery import celery as clr
import time


def print_info(self):
    print(f"{self.name} has parent with task id {self.request.parent_id}")
    print(f"chain of {self.name}: {self.request.chain}")
    print(f"self.request.id: {self.request.id}")

@clr.task(bind=True)
def create_task(self, value, t):
    # raise HTTPBadRequest("STOP !")
    print_info(self)

    time.sleep(t)
    return value

@clr.task(bind=True)
def add(self, a, t):
    print_info(self)

    time.sleep(t)
    return a+1

@clr.task()
def test_scan_mail(db: str, mail: dict, obj_id: str, admin_id: str):
    mail_service = MailServices(db, obj_id)
    # result = async_to_sync(record_repo.find_one_by_id)(id = "6621547dd478411eb0ad46a6")
    result = asyncio.get_event_loop().run_until_complete(mail_service.scan_email(mail, admin_id))

    return result


@clr.task()
def test_query(db: str, obj_id: str):
    time.sleep(5)
    record_repo = RecordObjectRepository(db, obj_id)
    # result = async_to_sync(record_repo.find_one_by_id)(id = "6621547dd478411eb0ad46a6")
    result = asyncio.get_event_loop().run_until_complete(record_repo.find_one_by_id(id="6621547dd478411eb0ad46a6"))
    # result = async_find_one_by_id(id="6621547dd478411eb0ad46a6")

    return result

@clr.task(bind=True, max_retries=1, retry_backoff=5)
def division(self, a, b):
    try:
        time.sleep(3)
        return a/b
    except ZeroDivisionError as e:
        raise self.retry(exc=e)
    
@clr.task(bind=True)
def activate_workflow(self, a, t):
    print_info(self)

    time.sleep(t)
    return a+1


# DONE
@clr.task()
def activate_send(db: str, action: dict, admin_id: str):
    # action_repo = ActionRepository(db)
    # action = asyncio.get_event_loop().run_until_complete(action_repo.find_one_by_id(action_id))
    object_id = action.get("object_id")
    obj_repo = ObjectRepository(db)
    obj = asyncio.get_event_loop().run_until_complete(obj_repo.find_one_by_id(object_id))
    obj_id = obj.get("obj_id")

    record_repo = RecordObjectRepository(db, obj_id)
    records = asyncio.get_event_loop().run_until_complete(record_repo.get_all_records())
    mail_service = MailServices(db, obj_id)
    field_email = action.get("to")
    mail = {
        "email": action.get("from"),
        "template": action.get("template_id"),
        "object": action.get("object_id")
    }
    results = []

    for record in records:
        mail["send_to"] = record.get(field_email)

        # result = async_to_sync(record_repo.find_one_by_id)(id = "6621547dd478411eb0ad46a6")
        result = asyncio.get_event_loop().run_until_complete(mail_service.send_one(mail, admin_id, record))
        results.append(result)

    return len(results)

# DONE
@clr.task()
def activate_create(db: str, action: dict, user_id: str, contents: List[str]):
    object_id = action.get("object_id")
    obj_repo = ObjectRepository(db)
    obj = asyncio.get_event_loop().run_until_complete(obj_repo.find_one_by_id(object_id))
    obj_id = obj.get("obj_id")
    record = {
        "object_id": object_id
    }
    for field_config in action.get("field_configs"):
        record.update(field_config)

    record_service = RecordObjectService(db, obj_id, object_id)

    results = []
    if action.get("option") == "no":
        results = asyncio.get_event_loop().run_until_complete(record_service.create_record(record, user_id))
    else:
        for content in contents:
            if action.get("field_contents"):      
                for field in action.get("field_contents"):
                    record[field] = content

            result = asyncio.get_event_loop().run_until_complete(record_service.create_record(record, user_id))
            results.append(result)

    return len(results)


# DONE
@clr.task()
def activate_update(db: str, action: dict, user_id: str, contents: List[str], record_id: str):
    object_id = action.get("object_id")
    obj_repo = ObjectRepository(db)
    obj = asyncio.get_event_loop().run_until_complete(obj_repo.find_one_by_id(object_id))
    obj_id = obj.get("obj_id")

    record = {
        "record_id": record_id,
        "object_id": object_id
    }
    for field_config in action.get("field_configs"):
        record.update(field_config)

    record_service = RecordObjectService(db, obj_id, object_id)

    if action.get("option") == "yes":
        if action.get("field_contents"):      
            for field in action.get("field_contents"):
                record[field] = contents[0]

    result = asyncio.get_event_loop().run_until_complete(record_service.update_one_record(record, user_id))
    return result

@clr.task()
def activate_inbound():
    pass


def test_call(num: int):
    task = group(create_task.s(7, 27), add.s(num, 11), create_task.s(3, 17), division.s(9, 0)).apply_async()

    return task.id