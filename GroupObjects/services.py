from typing import List
from GroupObjects.models import GroupObjectModel
from GroupObjects.schemas import GroupObjectSchema, UpdateGroupObjectSchema
from GroupObjects.repository import GroupObjectRepository
from Object.repository import ObjectRepository
from Object.services import ObjectService
from bson import ObjectId
from abc import ABC, abstractmethod
from RootAdministrator.constants import HIDDEN_SYSTEM_USER_INFO
from RootAdministrator.repository import RootAdministratorRepository
from app.common.errors import HTTPBadRequest
from app.common.utils import get_current_hcm_datetime

class GroupObjectServices:
    def __init__(self, db_str: str):
        self.repo = GroupObjectRepository(db_str)
        self.users_repo = RootAdministratorRepository()
        self.obj_service = ObjectService(db_str)
        self.db_str = db_str
    
    async def create_group(self, group: GroupObjectSchema) -> str:
        group = group.model_dump()
        manager_id = group.get("manager_id")
        system_user = await self.users_repo.find_one_by_id(manager_id, self.db_str)
        if not system_user:
            raise HTTPBadRequest("Cannot found system user by manager_id")
        
        new_index = await self.repo.count_all()
        group_model = GroupObjectModel(
            id = str(ObjectId()),
            name = group.get("name"),
            manager_id = system_user.get("_id"),
            sorting_id = new_index
        )
        await self.users_repo.update_one_by_id(system_user.get("_id"), {"is_manager": True})
        
        return await self.repo.insert_one(group_model.model_dump(by_alias=True))
        
    async def update_many_groups(self, groups: List[UpdateGroupObjectSchema]):
        list_groups = []
        for index, group in enumerate(groups):
            group = group.model_dump()
            manager_id = group.get("manager_id")
            system_user = await self.users_repo.find_one_by_id(manager_id, self.db_str)
            if not system_user:
                raise HTTPBadRequest("Cannot found system user by manager_id")
            
            updated_group = {
                "id":  group.get("id"),
                "name": group.get("name"),
                "manager_id": group.get("manager_id"),
                "sorting_id": index,
                "modified_at": get_current_hcm_datetime()
            }
            list_groups.append(updated_group)
        
        await self.repo.update_many(list_groups)
    
    async def update_one_group(self, group: UpdateGroupObjectSchema):
        group = group.model_dump()
        manager_id = group.get("manager_id")
        system_user = await self.users_repo.find_one_by_id(manager_id, self.db_str)
        if not system_user:
            raise HTTPBadRequest("Cannot found system user by manager_id")
        
        group.update({"modified_at": get_current_hcm_datetime()})
        await self.repo.update_one_by_id(group.pop("id"), group)

    async def get_detail_group_by_id(self, id: str) -> dict:
        group = await self.repo.find_one_by_id(id)
        manager_id = group.pop("manager_id")
        if manager_id:
            manager = await self.users_repo.find_one_by_id(manager_id, self.db_str, HIDDEN_SYSTEM_USER_INFO)
            group.update({"manager": manager})
        
        return group
 
    async def get_all_groups_with_details(self) -> List[dict]:
        """
        Get all GroupObject with parsing Object details, nested parsing FieldObject details
        """
        return await self.repo.get_all_groups_with_details()
        
    async def get_all_user_groups(self, user_id: str) -> List[GroupObjectModel]:
        return await self.get_all_groups({"manager_id": user_id})
    
    async def delete_one_group_obj_by_id(self, id: str) -> bool:
        await self.obj_service.delete_all_objects_by_group_id(id)

        return await self.repo.delete_one_by_id(id)