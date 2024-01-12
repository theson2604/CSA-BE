from abc import ABC, abstractmethod
from typing import List
from bson import ObjectId
from FieldObject.models import FieldEmail, FieldPhoneNumber, FieldReferenceObject, FieldSelect, FieldText

from FieldObject.repository import FieldObjectRepository
from FieldObject.schemas import FieldObjectSchema
from app.common.enums import FieldObjectType
from app.common.utils import generate_field_id

class IFieldObjectService(ABC):
    @abstractmethod
    async def create_many_field_object(self, object_id: str, fields: List[FieldObjectSchema]) -> List[str]:
        raise NotImplementedError
    
class FieldObjectService(IFieldObjectService):
    def __init__(self, db_str: str):
        self.repo = FieldObjectRepository(db_str)
    
    async def create_many_field_object(self, object_id: str, fields: List[FieldObjectSchema]) -> List[str]:
        list_fields = []
        for index, field in enumerate(fields):
            field = field.model_dump()
            field_base = {
                "id": str(ObjectId()),
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
                list_fields.append(FieldText(field_base.model_dump(by_alias=True)))
                
            elif field.get("field_type") is FieldObjectType.EMAIL:
                list_fields.append(FieldEmail(field_base.model_dump(by_alias=True)))
                
            elif field.get("field_type") is FieldObjectType.SELECT:
                field_base.update({
                    "options": field.get("options", [])
                })
                list_fields.append(FieldSelect(field_base.model_dump(by_alias=True)))
                
            elif field.get("field_type") is FieldObjectType.PHONE_NUMBER:
                field_base.update({
                    "country_code": field.get("country_code"),
                    "number": field.get("number")
                })
                list_fields.append(FieldPhoneNumber(field_base.model_dump(by_alias=True)))
                
            elif field.get("field_type") is FieldObjectType.REFERENCE_OBJECT:
                field_base.update({
                    "source": field.get("source")
                })
                list_fields.append(FieldReferenceObject(field_base.model_dump(by_alias=True)))
                
        return await self.repo.insert_many(list_fields)