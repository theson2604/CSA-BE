from abc import ABC, abstractmethod
from typing import List, Union
from bson import ObjectId
import re
from FieldObject.models import FieldEmail, FieldId, FieldPhoneNumber, FieldReferenceObject, FieldSelect, FieldText, FieldReferenceFieldObject, FieldObjectBase, FieldTextArea

from FieldObject.repository import FieldObjectRepository
from FieldObject.schemas import FieldObjectSchema, UpdateFieldObjectSchema
from Object.repository import ObjectRepository
from app.common.enums import FIELD_ID, FieldObjectType
from app.common.errors import HTTPBadRequest
from app.common.utils import generate_field_id

class FieldObjectServiceException(Exception):
    pass

class IFieldObjectService(ABC):
    @abstractmethod
    async def validate_and_get_all_field_models(self, object_id: str, fields: List[FieldObjectSchema]) -> List[FieldObjectBase]:
        raise NotImplementedError
    
    @abstractmethod
    async def create_many_fields_object(self, object_id: str, fields: List[FieldObjectSchema]) -> List[str]:
        raise NotImplementedError
    
    @abstractmethod
    async def update_one_field(self, field: UpdateFieldObjectSchema) -> int:
        raise NotImplementedError
    
    @abstractmethod
    async def update_sorting(self, fields: List[str]):
        raise NotImplementedError
    
    @abstractmethod
    async def create_one_field(self, field: FieldObjectSchema) -> str:
        raise NotImplementedError
    
    @abstractmethod
    async def get_all_fields_by_obj_id(self, object_id: str) -> List[Union[FieldObjectBase]]:
        raise NotImplementedError
    
class FieldObjectService(IFieldObjectService):
    def __init__(self, db_str: str):
        self.repo = FieldObjectRepository(db_str)
        self.object_repo = ObjectRepository(db_str)
        
    async def validate_and_get_all_field_models(self, object_id: str, fields: List[FieldObjectSchema]) -> List[FieldObjectBase]:
        try:
            list_fields = []
            obj = await self.object_repo.find_one_by_id(object_id)
            if not obj:
                raise FieldObjectServiceException(f"Not found object by _id {object_id}")
            
            for index, field in enumerate(fields):
                field = field.model_dump()
                field_base = {
                    "_id": str(ObjectId()) if not field.get("id") else field.get("id"),
                    "field_name": field.get("field_name"),
                    "field_type": field.get("field_type"),
                    "field_id": generate_field_id(field.get("field_name")) if not field.get("field_id") else field.get("field_id"),
                    "sorting_id": index,
                    "object_id": object_id
                }
                if field.get("field_type") is FieldObjectType.ID:
                    field_base.update({
                        "field_name": FIELD_ID,
                        "prefix": field.get("prefix")
                    })
                    list_fields.append(FieldId.model_validate(field_base).model_dump(by_alias=True))
                
                elif field.get("field_type") is FieldObjectType.TEXT:
                    field_base.update({
                        "length": field.get("length")
                    })
                    list_fields.append(FieldText.model_validate(field_base).model_dump(by_alias=True))
                
                elif field.get("field_type") is FieldObjectType.TEXTAREA:
                    list_fields.append(FieldTextArea.model_validate(field_base).model_dump(by_alias=True))
                    
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
                    source_id = field.get("src")
                    ref_obj = await self.object_repo.find_one_by_object_id(source_id)
                    if not ref_obj:
                        raise HTTPBadRequest(f"Not found ref_obj {source_id}.")
                    
                    ref_obj_id_value = ref_obj.get("_id")
                    display_value = ref_obj.get("obj_name")
                    
                    field_base.update({
                        "display_value": display_value,
                        "ref_obj_id": source_id,
                        "ref_obj_id_value": ref_obj_id_value
                    })
                    
                    list_fields.append(FieldReferenceObject.model_validate(field_base).model_dump(by_alias=True))
                    
                elif field.get("field_type") is FieldObjectType.REFERENCE_FIELD_OBJECT:
                    # obj_contact_431.fd_email_286
                    source_id = field.get("src")
                    split_source_id = source_id.split(".")
                    obj_id, fld_id = split_source_id[0], split_source_id[1]
                    ref_obj = await self.object_repo.find_one_by_object_id(obj_id)
                    if not ref_obj:
                        raise HTTPBadRequest(f"Not found ref_obj {obj_id}.")
                    
                    ref_obj_id_value = ref_obj.get("_id")
                    ref_field = await self.repo.find_one_by_field_id(ref_obj_id_value, fld_id)
                    if not ref_field:
                        raise HTTPBadRequest(f"Not found ref_field '{fld_id}' in ref_obj '{obj_id}'")

                    display_value = f'{ref_obj.get("obj_name")}.{ref_field.get("field_name")}'
                    field_base.update({
                        "display_value": display_value,
                        "ref_field_obj_id": source_id,
                        "ref_obj_id_value": ref_obj_id_value
                    })
                    
                    list_fields.append(FieldReferenceFieldObject.model_validate(field_base).model_dump(by_alias=True))
            
            return list_fields
        
        except Exception as e:
            raise FieldObjectServiceException(e)
        
    async def create_many_fields_object(self, object_id: str, fields: List[FieldObjectSchema]) -> List[str]:
        field_models = await self.validate_and_get_all_field_models(object_id, fields)
        return await self.repo.insert_many(field_models)
    
    async def update_one_field(self, field: UpdateFieldObjectSchema) -> int:
        field_dump = field.model_dump()
        field_models = await self.validate_and_get_all_field_models(field_dump.get("object_id"), [field])
        if isinstance(field_models, list) and len(field_models) == 1:
            field_model = field_models[0]
            field_model.update({"sorting_id": field_dump.get("sorting_id")})
            return await self.repo.update_one_by_id(field_model.pop("_id"), field_model)
        
    async def update_sorting(self, fields: List[str]):
        sorted_list = []
        for index, field_id in enumerate(fields):
            sorted_list += [{"_id": field_id, "sorting_id": index}]
        
        await self.repo.update_many(sorted_list)
        
    async def create_one_field(self, field: FieldObjectSchema) -> str:
        field_dump = field.model_dump()
        field_models = await self.validate_and_get_all_field_models(field_dump.get("object_id"), [field])
        if isinstance(field_models, list) and len(field_models) == 1:
            field_model = field_models[0]
            field_model.update({"sorting_id": field_dump.get("sorting_id")})
            return await self.repo.insert_one(field_model)
    
    async def get_all_fields_by_obj_id(self, object_id: str) -> List[Union[FieldObjectBase]]:
        return await self.repo.find_all({"object_id": object_id})