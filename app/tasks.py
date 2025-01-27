import asyncio
import json
from celery.result import AsyncResult
from typing import List, Tuple

from fastapi import WebSocket
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
from SentimentAnalysis.services import SentimentAnalysisServices
from app.celery import celery as clr, redis_client
import logging
from app.common.db_connector import DBCollections

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def monitor_tasks(clients: List[WebSocket]):
    while True:
        # old_ids = []
        tasks_info = clr.control.inspect().active() # {worker_name : [{task_info}]}
        await asyncio.sleep(0.1)
        try:
            task_ids = tasks_info[list(tasks_info.keys())[0]]
        except:
            task_ids = []
        # old_ids.extend(task_ids)
        for task_id in task_ids:
            # if task_id in old_ids:
            #     continue
            result = AsyncResult(task_id["id"])
            if result.ready():
                await NotificationService.send_one(task_id["id"], result, clients)
            # else:
                # old_ids.append(task_id)
            #     print("NOT READY")

def set_task_metadata(task_id: str, metadata: dict):
    return redis_client.set(task_id, json.dumps(metadata))

def get_task_metadata(task_id: str):
    return redis_client.get(task_id)

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
    db: str, action: dict, user_id: str, contents: List[str], access_token: str
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
        results.append(asyncio.get_event_loop().run_until_complete(record_service.create_record(record, user_id, access_token))) #inserted_id
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

            parent_record = asyncio.get_event_loop().run_until_complete(
                parent_record_repo.find_one({parent_field_id: content.get("record_prefix")})
            )
            if parent_record:
                record[ref_parent_field.get("field_id")] = parent_record.get("_id")
            record["object_id"] = object_id
            result = asyncio.get_event_loop().run_until_complete(record_service.create_record(record, user_id, access_token)) #inserted_id
            if result:
                results.append(result)
    
    field_repo = FieldObjectRepository(db)
    fd_id = (asyncio.get_event_loop().run_until_complete(field_repo.find_one_by_field_type(object_id, "id"))).get("field_id")
    record_repo = RecordObjectRepository(db, obj_id)
    if len(results) > 1:
        results = asyncio.get_event_loop().run_until_complete(record_repo.find_all({"_id": {"$in": results}}, {"_id": 1, "object_id": 1, fd_id: 1}))
    else:
        results = [asyncio.get_event_loop().run_until_complete(record_repo.find_one_by_id(results[0], {"_id": 1, "object_id": 1, fd_id: 1}))]
    return results, fd_id


# DONE
@clr.task(name = "update_record")
def activate_update(
    db: str, action: dict, user_id: str, record_id: str, contents: List[str], access_token: str
) -> Tuple[List[RecordObjectModel], str]:
    object_id = action.get("object_id")
    obj_repo = ObjectRepository(db)
    obj = asyncio.get_event_loop().run_until_complete(obj_repo.find_one_by_id(object_id))
    obj_id = obj.get("obj_id")
    field_repo = FieldObjectRepository(db)
    fd_id = (asyncio.get_event_loop().run_until_complete(field_repo.find_one_by_field_type(object_id, "id"))).get("field_id")
    results = []
    record_service = RecordObjectService(db, obj_id, object_id)

    if len(contents) != 0:
        contents.pop() #{"ref_obj_name": obj_name, "ref_obj_id": object_id}
        record_repo = RecordObjectRepository(db, obj_id)
        for content in contents:
            record_prefix = content.get("record_prefix")
            record = asyncio.get_event_loop().run_until_complete(record_repo.find_one({fd_id: record_prefix}))
            new_record = {
                "record_id": record.get("_id"),
                "object_id": record.get("object_id")
            }
            for field_config in action.get("field_configs"):
                new_record.update(field_config)

            #switch to record_service.update_one_record to trigger worfkflow
            # result += asyncio.get_event_loop().run_until_complete(record_repo.update_and_get_one({fd_id: record_prefix}, new_record))
            results.append(asyncio.get_event_loop().run_until_complete(record_service.update_one_record(new_record, user_id, access_token)))

    else:
        record = {
            "record_id": record_id,
            "object_id": object_id
        }
        for field_config in action.get("field_configs"):
            record.update(field_config)

        results.append(asyncio.get_event_loop().run_until_complete(record_service.update_one_record(record, user_id, access_token)))

    return results, fd_id

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
    sentiment_service = SentimentAnalysisServices(db_str)
    result = asyncio.get_event_loop().run_until_complete(sentiment_service.infer_sentiment_score(db_str, config, record_id, cur_user_id, access_token))
    return result


