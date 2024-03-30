from abc import ABC, abstractmethod
from typing import List
import asyncio
import re

from bson import ObjectId
import pymongo

from FieldObject.repository import FieldObjectRepository
from Object.repository import ObjectRepository
from RecordObject.models import RecordObjectModel
from RecordObject.repository import RecordObjectRepository
from RecordObject.schemas import RecordObjectSchema
from app.common.enums import FieldObjectType
from app.common.errors import HTTPBadRequest
from app.common.utils import generate_next_record_id, get_current_hcm_datetime


class RecordException(Exception):
    pass


class IRecordObjectService(ABC):
    @abstractmethod
    async def create_record(
        self, record: RecordObjectSchema, current_user_id: str
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    async def get_all_records_with_detail(
        self, object_id: str, page: int = 1, page_size: int = 100
    ) -> List[RecordObjectModel]:
        raise NotImplementedError
    
    @abstractmethod
    async def get_one_record_by_id_with_detail(
        self, record_id: str, object_id: str
    ) -> RecordObjectModel:
        raise NotImplementedError


class RecordObjectService(IRecordObjectService):
    def __init__(self, db_str: str, obj_id: str):
        """
        :Parameters:
        obj_id: obj_<name>_<id> for selecting corresponding object's mongo collection
        """
        self.db_str = db_str
        self.record_repo = RecordObjectRepository(db_str, coll=obj_id)
        self.field_obj_repo = FieldObjectRepository(db_str)
        self.object_repo = ObjectRepository(db_str) 

    async def create_record(
        self, record: RecordObjectSchema, current_user_id: str
    ) -> str:
        obj_id = record.pop("object_id")
        inserted_record = {"object_id": obj_id}
        
        for field_id, field_value in record.items():
            field_detail = await self.field_obj_repo.find_one_by_field_id(
                obj_id, field_id
            )
            field_type = field_detail.get("field_type")
            
            if field_type == FieldObjectType.TEXT:
                length = field_detail.get("length")
                if not isinstance(field_value, str):
                    raise RecordException(
                        f"field_value '{field_value}' of type {field_type} must be str."
                    )
                if len(field_value) > length:
                    raise RecordException(f"len(field_value) must be < {length}")

            elif field_type == FieldObjectType.EMAIL:
                email_regex = (
                    "^[a-zA-Z0-9]+(?:\.[a-zA-Z0-9]+)*@[a-zA-Z0-9]+(?:\.[a-zA-Z0-9]+)*$"
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

            inserted_record.update({field_id: field_value})

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
        return await self.record_repo.insert_one(
            RecordObjectModel.model_validate(inserted_record).model_dump(by_alias=True)
        )

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
                total = records.get("total_records", [{"total": 0}])
                records.update({"total_records": total[0].get("total")})
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