import asyncio
from MailService.schemas import MailSchema
from MailService.services import MailServices
from Object.repository import ObjectRepository
from app.common.db_connector import DBCollections, client
from celery import chain, group, shared_task, Celery
from RecordObject.repository import RecordObjectRepository
from asgiref.sync import async_to_sync
from app.celery import celery as clr
import time
import celery

from app.decorator import async_task

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
    result = async_to_sync(mail_service.scan_email)(mail, admin_id)

    return result


@clr.task()
def test_query(db: str, obj_id: str):
    record_repo = RecordObjectRepository(db, obj_id)
    # result = async_to_sync(record_repo.find_one_by_id)(id = "6621547dd478411eb0ad46a6")
    async_find_one_by_id = async_to_sync(record_repo.find_one_by_id)
    result = async_find_one_by_id(id="6621547dd478411eb0ad46a6")

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

@clr.task()
def activate_send(db: str, mail: dict, obj_id: str, admin_id: str):
    mail_service = MailServices(db, obj_id)
    # result = async_to_sync(record_repo.find_one_by_id)(id = "6621547dd478411eb0ad46a6")
    result = async_to_sync(mail_service.scan_email)(mail, admin_id)

@clr.task()
def activate_scan(db: str, mail: dict, obj_id: str, admin_id: str):
    mail_service = MailServices(db, obj_id)
    # result = async_to_sync(record_repo.find_one_by_id)(id = "6621547dd478411eb0ad46a6")
    result = async_to_sync(mail_service.scan_email)(mail, admin_id)

@clr.task()
def activate_create(db: str, mail: dict, obj_id: str, admin_id: str):
    mail_service = MailServices(db, obj_id)
    # result = async_to_sync(record_repo.find_one_by_id)(id = "6621547dd478411eb0ad46a6")
    result = async_to_sync(mail_service.scan_email)(mail, admin_id)

@clr.task()
def activate_update(db: str, mail: dict, obj_id: str, admin_id: str):
    mail_service = MailServices(db, obj_id)
    # result = async_to_sync(record_repo.find_one_by_id)(id = "6621547dd478411eb0ad46a6")
    result = async_to_sync(mail_service.scan_email)(mail, admin_id)

async def test_queyr():
    # db = client.get_database(db_str)
    # record_coll = db.get_collection(coll)

    # return await record_coll.find_one({"_id": "6621547dd478411eb0ad46a6"})

    await asyncio.sleep(1)
    return 'hello'


def test_call(num: int):
    task = group(create_task.s(7, 27), add.s(num, 11), create_task.s(3, 17), division.s(9, 0)).apply_async()

    return task.id

def call_(num: int):
    task = group(create_task.s(7, 27), add.s(num, 11), create_task.s(3, 17), division.s(9, 0)).apply_async()

    return task.id