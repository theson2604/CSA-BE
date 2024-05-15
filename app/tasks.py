import asyncio
from MailService.schemas import MailSchema
from MailService.services import MailServices
from Object.repository import ObjectRepository
from app.common.db_connector import DBCollections, client
from celery import chain, shared_task, Celery
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

@clr.task(bind=True, max_retries=1, retry_backoff=5)
def division(self, a, b):
    try:
        time.sleep(3)
        return a/b
    except ZeroDivisionError as e:
        raise self.retry(exc=e)
    

async def test_queyr():
    # db = client.get_database(db_str)
    # record_coll = db.get_collection(coll)

    # return await record_coll.find_one({"_id": "6621547dd478411eb0ad46a6"})

    await asyncio.sleep(1)
    return 'hello'
