from abc import ABC, abstractmethod
from datetime import datetime
import logging
from typing import List
import asyncio
import re

from bson import ObjectId
import pymongo

from FieldObject.repository import FieldObjectRepository
from Object.repository import ObjectRepository
from RecordObject.models import RecordObjectModel
from RecordObject.repository import RecordObjectRepository
from RecordObject.schemas import RecordObjectSchema, UpdateRecordSchema
from RecordObject.search import ElasticsearchRecord
from RecordObject.utils import use_operator
from Workflow.repository import WorkflowRepository
from app.common.enums import ActionWorkflowStatus, FieldObjectType
from app.common.errors import HTTPBadRequest
from app.common.utils import generate_next_record_id, get_current_hcm_datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RecordException(Exception):
    pass

class RecordObjectService:
    def __init__(self, db_str: str, obj_id_str: str, obj_id: str):
        """
        :Parameters:
        obj_id_str: obj_<name>_<id> for selecting corresponding object's mongo collection
        """
        self.db_str = db_str
        self.obj_id_str = obj_id_str
        self.record_repo = RecordObjectRepository(db_str, coll=obj_id_str)
        self.field_obj_repo = FieldObjectRepository(db_str)
        self.object_repo = ObjectRepository(db_str) 
        self.workflow_repo = WorkflowRepository(db_str)

        # service
        self.elastic_service = ElasticsearchRecord(db_str, obj_id_str, obj_id)
        # self.workflow_service = WorkflowService(db_str)

    async def process_fields(
        self, fields: dict, record: dict, obj_id: str
    ) -> dict:
        for field_id, field_value in fields.items():
            field_detail = await self.field_obj_repo.find_one_by_field_id_str(
                obj_id, field_id
            )
            try:
                field_type = field_detail.get("field_type")
            except Exception as e:
                raise HTTPBadRequest(f"field {field_id} {field_value}")
            
            if field_type == FieldObjectType.TEXT:
                length = field_detail.get("length")
                if not isinstance(field_value, str):
                    raise RecordException(
                        f"field_value '{field_value}' of type {field_type} must be str."
                    )
                if len(field_value) > length:
                    raise RecordException(f"len(field_value) must be < {length}")
                
            elif field_type == FieldObjectType.FLOAT:
                if not isinstance(field_value, float):
                    raise RecordException(f"field_value '{field_value}' of type {field_type} must be float.")
                
            elif field_type == FieldObjectType.INTEGER:
                if not isinstance(field_value, int):
                    raise RecordException(f"field_value '{field_value}' of type {field_type} must be int.")

            elif field_type == FieldObjectType.EMAIL:
                email_regex = (
                    r"^[a-zA-Z0-9]+(?:\.[a-zA-Z0-9]+)*@[a-zA-Z0-9]+(?:\.[a-zA-Z0-9]+)*$"
                )
                match = re.search(email_regex, field_value)
                if not match:
                    raise RecordException(
                        f"field_value '{field_value}' of type {field_type} must match email_regex {email_regex}"
                    )

            elif field_type == FieldObjectType.PHONE_NUMBER:
                country_code = field_detail.get("country_code")
                if country_code == "+84":
                    vn_phone_regex = "^(0|84)(2(0[3-9]|1[0-6|8|9]|2[0-2|5-9]|3[2-9]|4[0-9]|5[1|2|4-9]|6[0-3|9]|7[0-7]|8[0-9]|9[0-4|6|7|9])|3[2-9]|5[5|6|8|9]|7[0|6-9]|8[0-6|8|9]|9[0-4|6-9])([0-9]{7})$"
                    match = re.search(vn_phone_regex, field_value)
                    if not match:
                        raise RecordException(
                            f"field_value '{field_value}' of type {field_type} must be match vn_phone_regex {vn_phone_regex}"
                        )

            elif field_type == FieldObjectType.SELECT:
                options = field_detail.get("options")
                if field_value not in options:
                    raise RecordException(
                        f"field_value '{field_value}' of type {field_type} must exist in options {options}"
                    )
                
            elif field_type == FieldObjectType.DATE:
                format = field_detail.get("format")
                separator = field_detail.get("separator")
                if separator not in field_value:
                    raise RecordException(
                        f"separator of date {field_value} is not valid."
                    )

                date_regex = {
                    "DD MM YYYY": r"^\d{2} \d{2} \d{4}$",
                    "MM DD YYYY": r"^\d{2} \d{2} \d{4}$",
                    "YYYY MM DD": r"^\d{4} \d{2} \d{2}$"
                }
                if not re.match(date_regex.get(format), field_value.replace(separator, " ")):
                    raise RecordException(
                        f"date {field_value} format is not valid."
                    )

                try:
                    if format == "DD MM YYYY":
                        bool(datetime.strptime(field_value, f"%d{separator}%m{separator}%Y"))
                    elif format == "MM DD YYYY":
                        bool(datetime.strptime(field_value, f"%m{separator}%d{separator}%Y"))
                    else:
                        bool(datetime.strptime(field_value, f"%Y{separator}%m{separator}%d"))
                except ValueError:
                    raise RecordException(
                        f"date {field_value} is not valid with format {format}."
                    )

            elif field_type == FieldObjectType.REFERENCE_OBJECT:
                ref_obj_id = field_detail.get("ref_obj_id")  # obj_<name>_<id>
                # obj_id's record repo
                ref_record_repo = RecordObjectRepository(self.db_str, ref_obj_id)
                ref_record = await ref_record_repo.find_one_by_id(field_value)
                if not ref_record:
                    raise RecordException(
                        f"Not found ref record '{field_value}' in {ref_obj_id}"
                    )

                obj_detail = await self.object_repo.find_one_by_object_id(ref_obj_id)
                field_ids = await self.field_obj_repo.get_all_by_field_types(obj_detail.get("_id"), [FieldObjectType.ID.value])
                
                if field_ids and len(field_ids) == 1:
                    field_value = {"ref_to": ref_record.get("_id"), "field_value": field_ids[0].get("field_id")}

            elif field_type == FieldObjectType.REFERENCE_FIELD_OBJECT:
                ref_field_obj_id = field_detail.get(
                    "ref_field_obj_id"
                )  # obj_<name>_<id>.fd_<name>_<id>
                splitted = ref_field_obj_id.split(".")
                ref_obj_id, ref_fld_id = splitted[0], splitted[1]
                # obj_id's record repo
                ref_record_repo = RecordObjectRepository(self.db_str, ref_obj_id)
                ref_record = await ref_record_repo.find_one_by_id(field_value)
                if not ref_record:
                    raise RecordException(
                        f"Not found ref record '{field_value} in {ref_obj_id}"
                    )

                field_value = {
                    "ref_to": ref_record.get("_id"),
                    "field_value": ref_fld_id,
                }

            record.update({field_id: field_value})

        return record
    
    async def check_conditions(self, record: dict, trigger: str, current_user_id: str, access_token: str):
        obj_id = record.get("object_id")
        record_id = record.get("_id")
        workflows = await self.workflow_repo.find_many({"object_id": obj_id}, {"_id": 1, "trigger": 1, "conditions": 1, "status": ActionWorkflowStatus.ACTIVE})
        logger.info("WORKFLOWS: ", workflows)
        task_ids = []
        for workflow in workflows:
            if workflow.get("trigger") != trigger:
                continue

            conditions = workflow.get("conditions")
            for index, condition in enumerate(conditions):
                field_name, field_value, field_op = condition.get("field_name"), condition.get("field_value"), condition.get("field_op")
                if index == 0 or len(conditions) == 1:
                    base = use_operator(record.get(field_name), field_value, field_op)
                else:
                    base = use_operator(use_operator(record.get(field_name), field_value, field_op), base, conditions[index-1].get("op"))
                
            if base:
                from Workflow.services import WorkflowService
                workflow_service = WorkflowService(self.db_str)
                # activate current workflow
                task_id = await workflow_service.activate_workflow(workflow.get("_id"), current_user_id, access_token, record_id)
                task_ids.append(task_id)

        return task_ids

    async def create_record(
        self, record: RecordObjectSchema, current_user_id: str, access_token: str = "" 
    ) -> str:
        obj_id = record.pop("object_id")
        inserted_record = {"object_id": obj_id}
        
        inserted_record = await self.process_fields(record, inserted_record, obj_id)

        list_field_details = await self.field_obj_repo.get_all_by_field_types(obj_id, [FieldObjectType.ID])
        field_id_detail = list_field_details[0]
        field_id, prefix = field_id_detail.get("field_id"), field_id_detail.get("prefix")
        seq = await generate_next_record_id(self.db_str, obj_id)
        id = seq.get("seq")
        concat_prefix_id = f"{prefix}{id}"
        
        await self.record_repo.create_indexing([(field_id_detail.get("field_id"), pymongo.ASCENDING, True)])
        
        inserted_record.update(
            {
                "_id": str(ObjectId()),
                field_id: concat_prefix_id,
                "created_at": get_current_hcm_datetime(),
                "modified_at": get_current_hcm_datetime(),
                "created_by": current_user_id,
                "modified_by": current_user_id,
            }
        )
        
        cpy_record = inserted_record.copy()
        await self.elastic_service.index_doc(record_id=cpy_record.pop("_id"), doc=cpy_record)
        
        result = await self.record_repo.insert_one(
            RecordObjectModel.model_validate(inserted_record).model_dump(by_alias=True)
        )

        # await self.check_conditions(inserted_record, "create", current_user_id, access_token)
        asyncio.create_task(self.check_conditions(inserted_record, "create", current_user_id, access_token))
        
        return result

    async def get_all_records_with_detail(
        self, object_id: str, page: int = 1, page_size: int = 100
    ) -> List[RecordObjectModel]:
        skip = (page - 1) * page_size
        records = await self.record_repo.get_all_with_parsing_ref_detail(
            object_id, skip, page_size
        )

        if records and isinstance(records, list) and len(records) == 1:
            records = records[0]
            if isinstance(records, dict):
                total = records.get("total_records")
                records.update({"total_records": total[0].get("total") if total else 0})
                return records

        return []

    async def get_one_record_by_id_with_detail(
        self, record_id: str, object_id: str
    ) -> RecordObjectModel:
        """
        :Params:
        - record_id: Record's _id
        - object_id: Object's _id
        """
        return await self.record_repo.get_one_by_id_with_parsing_ref_detail(record_id, object_id)
    
    async def get_all_records_ref_to(
        self, record_id: str, ref_obj_id: str
    ) -> List[RecordObjectModel]:
        if not (await self.object_repo.find_one_by_id(ref_obj_id)):
            raise HTTPBadRequest(f"Can not find Ref Object by id {ref_obj_id}")
        
        return await self.record_repo.get_all_records_ref_to(record_id, ref_obj_id)

    async def update_one_record(self, record: dict, current_user_id: str, access_token: str = "") -> bool:
        record_id = record.pop("record_id")
        current_record = await self.record_repo.find_one_by_id(record_id)
        if not current_record:
            raise HTTPBadRequest(f"Can not find record {record_id}")

        obj_id = record.pop("object_id")
        updated_record = {}

        updated_record = await self.process_fields(record, updated_record, obj_id)

        updated_record.update(
        {
            "modified_at": get_current_hcm_datetime(),
            "modified_by": current_user_id
        })

        result = await self.record_repo.update_and_get_one({"_id": record_id}, updated_record)
        # await self.check_conditions(result, "update", current_user_id, access_token)
        asyncio.create_task(self.check_conditions(result, "update", current_user_id, access_token))

        return result

    async def delete_one_record(self, id: str):
        if not await self.record_repo.find_one_by_id(id):
            raise HTTPBadRequest(f"Can not find Record by id {id}")

        return await self.record_repo.delete_one_by_id(id)