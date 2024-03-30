from abc import ABC, abstractmethod
import asyncio
from typing import List
from bson import ObjectId

from fastapi import HTTPException
import pymongo
from FieldObject.repository import FieldObjectRepository
from FieldObject.services import FieldObjectServiceException, FieldObjectService
from GroupObjects.repository import GroupObjectRepository
from Object.models import ObjectModel

from Object.repository import ObjectRepository
from Object.schemas import ObjectSchema, ObjectWithFieldSchema
from app.common.enums import StatusCodeException
from app.common.errors import HTTPBadRequest
from app.common.utils import generate_object_id

class IObjectService(ABC):
    @abstractmethod
    async def create_object_only(self, obj: ObjectSchema, current_user_id: str) -> str:
        raise NotImplementedError
    
    @abstractmethod
    async def create_object_with_fields(self, obj: ObjectWithFieldSchema, current_user_id: str) -> str:
        raise NotImplementedError
    
    @abstractmethod
    async def get_all_objects_with_field_details(self) -> List[dict]:
        raise NotImplementedError
    
    @abstractmethod
    async def get_object_detail_by_id(self, id: str) -> dict:
        raise NotImplementedError
    
    
class ObjectService(IObjectService):
    def __init__(self, db_str: str):
        # Repo
        self.repo = ObjectRepository(db_str)
        self.group_obj_repo = GroupObjectRepository(db_str)
        # Services
        self.field_obj_service = FieldObjectService(db_str)
        
    async def create_object_only(self, obj: ObjectSchema, current_user_id: str) -> str:
        obj = obj.model_dump()
        group_obj_id = obj.get("group_obj_id")
        group = await self.group_obj_repo.find_one_by_id(group_obj_id)
        if not group:
            raise HTTPBadRequest(f"Cannot found Group Object by {group_obj_id}")
        
        obj_name = obj.get("obj_name")
        group_obj_id = group.get("_id") if group.get("_id") else group.get("id")
        last_index_in_group = await self.repo.count_all({"group_obj_id": group_obj_id})
        
        obj_id = generate_object_id(obj_name)
        
        obj_model = ObjectModel(
            id = str(ObjectId()),
            obj_name = obj_name,
            obj_id = obj_id,
            group_obj_id = group_obj_id,
            sorting_id = last_index_in_group,
            modified_by = current_user_id,
            created_by = current_user_id
        )
        
        asyncio.create_task(self.repo.create_indexing([(obj_id, pymongo.ASCENDING, True)]))
        
        return await self.repo.insert_one(obj_model.model_dump(by_alias=True))

    async def get_all_objects_with_field_details(self) -> List[dict]:
        """
            Include parsing Fields
        """
        return await self.repo.get_all_objects_with_field_details()
    
    async def create_object_with_fields(self, obj_with_fields: ObjectWithFieldSchema, current_user_id: str) -> str:
        try:
            # Create Object first
            obj_with_fields_schema = obj_with_fields
            obj_with_fields = obj_with_fields.model_dump()
            obj_only = {"obj_name": obj_with_fields.get("obj_name"), "group_obj_id": obj_with_fields.get("group_obj_id")}
            new_obj_id = await self.create_object_only(ObjectSchema(**obj_only), current_user_id)
            # Create Field Object
            await self.field_obj_service.create_many_fields_object(new_obj_id, obj_with_fields_schema.fields)
            return new_obj_id
        except FieldObjectServiceException as e:
            if new_obj_id:
                await self.repo.delete_one_by_id(new_obj_id)
            return HTTPBadRequest(str(e))
            
    
    async def get_object_detail_by_id(self, id: str) -> dict:
        return await self.repo.get_object_with_all_fields(id)