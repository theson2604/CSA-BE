from abc import ABC, abstractmethod
from typing import List
from bson import ObjectId

from fastapi import HTTPException
from FieldObject.repository import FieldObjectRepository
from GroupObjects.repository import GroupObjectRepository
from Object.models import ObjectModel

from Object.repository import ObjectRepository
from Object.schemas import ObjectSchema
from app.common.enums import StatusCodeException
from app.common.errors import HTTPBadRequest
from app.common.utils import generate_object_id

class IObjectService(ABC):
    @abstractmethod
    async def create_object_only(self, obj: ObjectSchema, current_user_id: str) -> str:
        raise NotImplementedError
    
    @abstractmethod
    async def get_all_objects(self) -> List[dict]:
        raise NotImplementedError
    
    # @abstractmethod
    # async def get_object_detail(self) -> str:
    #     raise NotImplementedError
    
    
class ObjectService(IObjectService):
    def __init__(self, db_str: str):
        self.repo = ObjectRepository(db_str)
        self.field_obj_repo = FieldObjectRepository(db_str)
        self.group_obj_repo = GroupObjectRepository(db_str)
        
    async def create_object_only(self, obj: ObjectSchema, current_user_id: str) -> str:
        obj = obj.model_dump()
        group_obj_id = obj.get("group_obj_id")
        group = await self.group_obj_repo.find_one_by_id(group_obj_id)
        if not group:
            raise HTTPBadRequest("Cannot found Group Object by group_obj_id")
        
        obj_name = obj.get("obj_name")
        group_obj_id = group.get("_id") if group.get("_id") else group.get("id")
        last_index_in_group = await self.repo.count_all({"group_obj_id": group_obj_id})
        
        obj_model = ObjectModel(
            id = str(ObjectId()),
            obj_name = obj_name,
            obj_id = generate_object_id(obj_name),
            group_obj_id = group_obj_id,
            sorting_id = last_index_in_group,
            modified_by = current_user_id,
            created_by = current_user_id
        )
        
        return await self.repo.insert_one(obj_model.model_dump(by_alias=True))

    async def get_all_objects(self) -> dict:
        objects = await self.repo.find_all()
        ret_objects = {}
        for obj in objects:
            group_id = obj.pop("group_obj_id")
            if not ret_objects.get(group_id):
                ret_objects.update({group_id: []})
                ret_objects[group_id].append(obj)
            else:
                ret_objects[group_id].append(obj)

        return ret_objects