from abc import ABC, abstractmethod
from typing import List, Union
from bson import ObjectId
from FieldObject.models import FieldEmail, FieldPhoneNumber, FieldReferenceObject, FieldSelect, FieldText

from FieldObject.repository import FieldObjectRepository
from FieldObject.schemas import FieldObjectSchema
from app.common.enums import FieldObjectType
from app.common.errors import HTTPBadRequest
from app.common.utils import generate_field_id

class IFieldObjectService(ABC):
    @abstractmethod
    async def create_many_field_object(self, object_id: str, fields: List[FieldObjectSchema]) -> List[str]:
        raise NotImplementedError
    
    @abstractmethod
    async def get_all_fields_by_obj_id(self, object_id: str) -> List[Union[FieldText, FieldEmail, FieldSelect, FieldPhoneNumber, FieldReferenceObject]]:
        raise NotImplementedError
    
class FieldObjectService(IFieldObjectService):
    def __init__(self, db_str: str):
        self.repo = FieldObjectRepository(db_str)
        
    async def create_many_field_object(self, object_id: str, fields: List[FieldObjectSchema]) -> List[str]:
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
                # Check whether is a valid source
                source_id = field.get("source")
                source_obj = await self.repo.find_one_by_id(source_id)
                if not source_obj:
                    raise HTTPBadRequest("Invalid source Object")
                
                field_base.update({
                    "source": source_id
                })
                list_fields.append(FieldReferenceObject.model_validate(field_base).model_dump(by_alias=True))
                
        return await self.repo.insert_many(list_fields)
    
    async def get_all_fields_by_obj_id(self, object_id: str) -> List[Union[FieldText, FieldEmail, FieldSelect, FieldPhoneNumber, FieldReferenceObject]]:
        return await self.repo.find_all({"object_id": object_id})