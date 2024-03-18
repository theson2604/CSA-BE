from abc import ABC, abstractmethod
from typing import List, Union
from bson import ObjectId
import re
from FieldObject.models import FieldEmail, FieldPhoneNumber, FieldReferenceObject, FieldSelect, FieldText, FieldReferenceFieldObject, FieldObjectBase

from FieldObject.repository import FieldObjectRepository
from FieldObject.schemas import FieldObjectSchema, UpdateFieldObjectSchema
from Object.repository import ObjectRepository
from app.common.enums import FieldObjectType
from app.common.errors import HTTPBadRequest
from app.common.utils import generate_field_id

class FieldObjectServiceException(Exception):
    pass

class IFieldObjectService(ABC):
    @abstractmethod
    async def create_many_field_object(self, object_id: str, fields: List[FieldObjectSchema]) -> List[str]:
        raise NotImplementedError
    
    @abstractmethod
    async def update_many_field_object(self, object_id: str, fields: List[UpdateFieldObjectSchema]) -> List[str]:
        raise NotImplementedError
    
    @abstractmethod
    async def get_all_fields_by_obj_id(self, object_id: str) -> List[Union[FieldObjectBase]]:
        raise NotImplementedError
    
class FieldObjectService(IFieldObjectService):
    def __init__(self, db_str: str):
        self.repo = FieldObjectRepository(db_str)
        self.object_repo = ObjectRepository(db_str)
        
    async def create_many_field_object(self, object_id: str, fields: List[FieldObjectSchema]) -> List[str]:
        try:
            list_fields = []
            for index, field in enumerate(fields):
                field = field.model_dump()
                field_base = {
                    "_id": str(ObjectId()),
                    "field_name": field.get("field_name"),
                    "field_type": field.get("field_type"),
                    "field_id": generate_field_id(field.get("field_name")),
                    "sorting_id": index,
                    "object_id": object_id
                }
                if field.get("field_type") is FieldObjectType.TEXT:
                    field_base.update({
                        "length": field.get("length")
                    })
                    list_fields.append(FieldText.model_validate(field_base).model_dump(by_alias=True))
                    
                elif field.get("field_type") is FieldObjectType.EMAIL:
                    list_fields.append(FieldEmail.model_validate(field_base).model_dump(by_alias=True))
                    
                elif field.get("field_type") is FieldObjectType.SELECT:
                    field_base.update({
                        "options": field.get("options", [])
                    })
                    list_fields.append(FieldSelect.model_validate(field_base).model_dump(by_alias=True))
                    
                elif field.get("field_type") is FieldObjectType.PHONE_NUMBER:
                    field_base.update({
                        "country_code": field.get("country_code"),
                        "number": field.get("number")
                    })
                    list_fields.append(FieldPhoneNumber.model_validate(field_base).model_dump(by_alias=True))
                    
                elif field.get("field_type") is FieldObjectType.REFERENCE_OBJECT:
                    # obj_contact_431
                    obj_id = field.get("src")
                    regex_str = "^obj_\w+_\d{3}"
                    match = re.search(regex_str, source_id)
                    if not match:
                        raise HTTPBadRequest(f"Invalid src {FieldObjectType.REFERENCE_OBJECT}. It must match {regex_str}")
                    
                    ref_obj = await self.object_repo.find_one_by_object_id(obj_id)
                    if not ref_obj:
                        raise HTTPBadRequest(f"Not found ref_obj {obj_id}")

                    field_base.update({
                        "ref_obj": ref_obj.get("_id"),
                    })
                    list_fields.append(FieldReferenceFieldObject.model_validate(field_base).model_dump(by_alias=True))
                    
                elif field.get("field_type") is FieldObjectType.REFERENCE_FIELD_OBJECT:
                    # obj_contact_431.fd_email_286
                    source_id = field.get("src")
                    regex_str = "^obj_\w+_\d{3}.fd_\w+_\d{3}$"
                    match = re.search(regex_str, source_id)
                    if not match:
                        raise HTTPBadRequest(f"Invalid src {FieldObjectType.REFERENCE_FIELD_OBJECT}. It must match {regex_str}")
                    
                    split_source_id = source_id.split(".")
                    obj_id, fld_id = split_source_id[0], split_source_id[1]
                    ref_obj = await self.object_repo.find_one_by_object_id(obj_id)
                    ref_obj_id = ref_obj.get("_id")
                    ref_field = await self.repo.find_one_by_field_id(ref_obj_id, fld_id)
                    if not ref_obj:
                        raise HTTPBadRequest(f"Not found ref_obj {obj_id}")

                    display_value = f'{ref_obj.get("obj_name")}.{ref_field.get("field_name")}'
                    field_base.update({
                        "field_value": source_id,
                        "display_value": display_value,
                        "ref_obj": ref_obj_id,
                        "ref_field_obj": ref_field.get("_id")
                    })
                    
                    list_fields.append(FieldReferenceFieldObject.model_validate(field_base).model_dump(by_alias=True))
                    
            return await self.repo.insert_many(list_fields)
        
        except Exception as e:
            raise FieldObjectServiceException(e)
    
    async def update_many_field_object(self, object_id: str, fields: List[UpdateFieldObjectSchema]) -> List[str]:
        list_fields = []
        for field in fields:
            pass
    
    async def get_all_fields_by_obj_id(self, object_id: str) -> List[Union[FieldObjectBase]]:
        return await self.repo.find_all({"object_id": object_id})