from typing import List, Union
from bson import ObjectId
from FieldObject.models import FieldEmail, FieldFloat, FieldId, FieldInteger, FieldPhoneNumber, FieldReferenceObject, FieldSelect, FieldText, FieldReferenceFieldObject, FieldObjectBase, FieldTextArea, FieldDate

from FieldObject.repository import FieldObjectRepository
from FieldObject.schemas import FieldObjectSchema, UpdateFieldObjectSchema
from FieldObject.utils import check_loop
from Object.repository import ObjectRepository
from app.common.enums import FIELD_ID, FieldObjectType
from app.common.errors import HTTPBadRequest
from app.common.utils import generate_field_id

class FieldObjectServiceException(Exception):
    pass

    
class FieldObjectService:
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
                        "prefix": field.get("prefix").upper()
                    })
                    list_fields.append(FieldId.model_validate(field_base).model_dump(by_alias=True))
                
                elif field.get("field_type") is FieldObjectType.TEXT:
                    field_base.update({
                        "length": field.get("length")
                    })
                    list_fields.append(FieldText.model_validate(field_base).model_dump(by_alias=True))
                    
                elif field.get("field_type") is FieldObjectType.FLOAT:
                    list_fields.append(FieldFloat.model_validate(field_base).model_dump(by_alias=True))
                    
                elif field.get("field_type") is FieldObjectType.INTEGER:
                    list_fields.append(FieldInteger.model_validate(field_base).model_dump(by_alias=True))
                
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

                elif field.get("field_type") is FieldObjectType.DATE:
                    field_base.update({
                        "format": field.get("format"),
                        "separator": field.get("separator")
                    })
                    list_fields.append(FieldDate.model_validate(field_base).model_dump(by_alias=True))
                
                elif field.get("field_type") is FieldObjectType.REFERENCE_OBJECT:
                    # obj_contact_431
                    source_id = field.get("src")
                    ref_obj = await self.object_repo.find_one_by_object_id(source_id)
                    if not ref_obj:
                        raise HTTPBadRequest(f"Not found ref_obj {source_id}.")
                    
                    ref_obj_id_value = ref_obj.get("_id")
                    display_value = ref_obj.get("obj_name")
                    cascade_option = field.get("cascade_option")
                    
                    field_base.update({
                        "display_value": display_value,
                        "ref_obj_id": source_id,
                        "ref_obj_id_value": ref_obj_id_value,
                        "cascade_option": cascade_option
                    })
                    
                    list_fields.append(FieldReferenceObject.model_validate(field_base).model_dump(by_alias=True))
                    
                elif field.get("field_type") is FieldObjectType.REFERENCE_FIELD_OBJECT:
                    # obj_contact_431.fd_email_286
                    source_id = field.get("src")
                    split_source_id = source_id.split(".")
                    obj_id_str, fld_id_str = split_source_id[0], split_source_id[1]
                    ref_obj = await self.object_repo.find_one_by_object_id(obj_id_str)
                    if not ref_obj:
                        raise HTTPBadRequest(f"Not found ref_obj {obj_id_str}.")
                    
                    ref_obj_id_value = ref_obj.get("_id")
                    ref_field = await self.repo.find_one_by_field_id_str(ref_obj_id_value, fld_id_str)
                    if not ref_field:
                        raise HTTPBadRequest(f"Not found ref_field '{fld_id_str}' in ref_obj '{obj_id_str}'")
                    
                    # Infinite field loop checking
                    new_path = [object_id, ref_obj_id_value]  # [from, to]
                    if (await self.infinite_loop_checking(new_path, target_ref_field_id=ref_field.get("_id"), target_obj_id=ref_obj_id_value)):
                        raise FieldObjectServiceException("Infinite field loop")
                    
                    display_value = f'{ref_obj.get("obj_name")}.{ref_field.get("field_name")}'
                    cascade_option = field.get("cascade_option")

                    field_base.update({
                        "display_value": display_value,
                        "ref_field_obj_id": source_id,
                        "ref_obj_id_value": ref_obj_id_value,
                        "cascade_option": cascade_option
                    })
                    
                    list_fields.append(FieldReferenceFieldObject.model_validate(field_base).model_dump(by_alias=True))
            
            return list_fields
        
        except Exception as e:
            raise FieldObjectServiceException(e)
        
        
    async def get_field_ref_path_deeply(self, target_ref_field_id, target_obj_id):
        """ Get the ref path deeply of the target ref field"""
        # Get all field refs with parsing deeply from reference obj
        all_field_refs_source_obj = await self.repo.get_all_field_refs_deeply(target_obj_id)
        # {C, linking_fields: {B * ref_obj_id_value(C), A, D}} C -> B -> A -> D
        path = []
        for field_ref_detail in all_field_refs_source_obj:
            if field_ref_detail.get("_id") == target_ref_field_id:
                # print(field_ref_detail)
                path.append(field_ref_detail.get("object_id"))
                for linking_field in field_ref_detail.get("linking_fields", []):
                    path.append(linking_field.get("object_id"))
        
        return path
    
    
    async def infinite_loop_checking(self, new_path: List[str], target_ref_field_id: str, target_obj_id: str) -> bool:
        ref_path_seq = await self.get_field_ref_path_deeply(target_ref_field_id, target_obj_id)
        return check_loop(ref_path_seq, new_path)
        
        
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
    
    
    async def delete_one_field_by_id(self, field_id: str) -> bool:
        return await self.repo.delete_one_by_id(field_id)


    async def delete_all_fields_by_obj_id(self, object_id: str) -> bool:
        object = await self.obj_repo.find_one_by_id(object_id)
        if not object:
            raise HTTPBadRequest("Cannot find Object by object_id")
        
        return await self.repo.delete_many({"object_id": object_id})