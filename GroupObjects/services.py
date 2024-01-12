from typing import List

from fastapi import Depends
from GroupObjects.models import GroupObjectModel
from GroupObjects.schemas import GroupObjectSchema, UpdateGroupObjectSchema
from GroupObjects.repository import GroupObjectRepository, IGroupObjectRepository
from bson import ObjectId
from abc import ABC, abstractmethod
from RootAdministrator.repository import IRootAdministratorRepository, RootAdministratorRepository

from app.common.utils import get_current_hcm_datetime

class IGroupObjectServices(ABC):
    @abstractmethod
    async def create_group(self, group: GroupObjectSchema) -> str:
        raise NotImplementedError
    
    @abstractmethod
    async def update_many_groups(self, groups: List[UpdateGroupObjectSchema]) -> bool:
        raise NotImplementedError
    
    @abstractmethod
    async def get_detail_group_by_id(self, id: str) -> GroupObjectModel:
        raise NotImplementedError
    
    @abstractmethod
    async def get_all_groups(self) -> List[GroupObjectModel]:
        raise NotImplementedError
    

class GroupObjectServices(IGroupObjectServices):
    def __init__(self, db_str: str, users_repo: IRootAdministratorRepository = Depends(RootAdministratorRepository)):
        self.repo = GroupObjectRepository(db_str)
        self.users_repo = users_repo
        self.db_str = db_str
    
    async def create_group(self, group: GroupObjectSchema) -> str:
        try:
            group = group.model_dump()
            manager_id = group.get("manager_id")
            system_user = await self.users_repo.find_one_by_id(manager_id, self.db_str)
            if system_user:
                system_user = system_user.model_dump()
                new_index = await self.repo.count_all()
                group_model = GroupObjectModel(
                    id = str(ObjectId()),
                    name = group.get("group_name"),
                    manager_id = system_user.get("_id"),
                    sorting_id = new_index
                )
                update_success = await self.users_repo.update_one_by_id(system_user.get("_id"), {"is_manager": True})
                if update_success:
                    return await self.repo.insert_one(group_model.model_dump(by_alias=True))

                raise Exception("Fail to update is_manager")
            
            raise Exception("Not found system user")
        
        except Exception as e:
            print(e)
            return None
        
    async def update_many_groups(self, groups: List[UpdateGroupObjectSchema]) -> bool:
        try:
            groups = groups.model_dump()
            # group.update({"modified_at": get_current_hcm_datetime()})
            # return await self.repo.update_one_by_id(group.pop("id"), group)
            return True
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