from GroupObjects.models import GroupObjectModel
from GroupObjects.schemas import GroupObjectSchema
from GroupObjects.repository import GroupObjectRepository
from bson import ObjectId
from abc import ABC, abstractmethod

class IGroupObjectServices(ABC):
    @abstractmethod
    async def create_group(self, group: GroupObjectSchema) -> bool:
        raise NotImplementedError
    

class GroupObjectServices(IGroupObjectServices):
    def __init__(self, db_str: str):
        self.repo = GroupObjectRepository(db_str)
    
    async def create_group(self, group: GroupObjectSchema) -> bool:
        try:
            group = group.model_dump()
            group_model = GroupObjectModel(
                id = str(ObjectId()),
                name = group.get("group_name"),
                manager_id = group.get("manager_id")
            )
            await self.repo.insert_group(group_model.model_dump(by_alias=True))
            return True
        except Exception as e:
            print(e)
            return False