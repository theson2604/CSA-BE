from typing import List
from GroupObjects.models import GroupObjectModel
from GroupObjects.schemas import GroupObjectSchema, UpdateGroupObjectSchema
from GroupObjects.repository import GroupObjectRepository, IGroupObjectRepository
from bson import ObjectId
from abc import ABC, abstractmethod

from app.common.utils import get_current_hcm_datetime

class IGroupObjectServices(ABC):
    @abstractmethod
    async def create_group(self, group: GroupObjectSchema) -> str:
        raise NotImplementedError
    
    @abstractmethod
    async def update_group(self, group: UpdateGroupObjectSchema) -> bool:
        raise NotImplementedError
    
    @abstractmethod
    async def get_detail_group_by_id(self, id: str) -> GroupObjectModel:
        raise NotImplementedError
    
    @abstractmethod
    async def get_all_groups(self) -> List[GroupObjectModel]:
        raise NotImplementedError
    

class GroupObjectServices(IGroupObjectServices):
    def __init__(self, db_str: str):
        self.repo = GroupObjectRepository(db_str)
    
    async def create_group(self, group: GroupObjectSchema) -> str:
        try:
            group = group.model_dump()
            group_model = GroupObjectModel(
                id = str(ObjectId()),
                name = group.get("group_name"),
                manager_id = group.get("manager_id"),
                sorting_id = group.get("sorting_id")
            )
            return await self.repo.insert_one(group_model.model_dump(by_alias=True))
        except Exception as e:
            print(e)
            return None
        
    async def update_group(self, group: UpdateGroupObjectSchema) -> bool:
        try:
            group = group.model_dump()
            group.update({"modified_at": get_current_hcm_datetime()})
            return await self.repo.update_one_by_id(group.pop("id"), group)
        except Exception as e:
            print(e)
            return False
    
    async def get_detail_group_by_id(self, id: str) -> GroupObjectModel:
        try:
            return await self.repo.find_one_by_id(id)
        except Exception as e:
            print(e)
            return None
    
    async def get_all_groups(self) -> List[GroupObjectModel]:
        try:
            return await self.repo.find_all()
        except Exception as e:
            print(e)
            return []