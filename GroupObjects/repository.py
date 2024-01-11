from abc import ABC, abstractmethod
from app.common.db_connector import client
from GroupObjects.models import GroupObjectModel
from app.common.db_connector import DBCollections

class IGroupObjectRepository(ABC):
    @abstractmethod
    async def insert_group(self, group: GroupObjectModel):
        raise NotImplementedError
    
    
class GroupObjectRepository(IGroupObjectRepository):
    def __init__(self, db_str: str, coll: str = DBCollections.GROUP_OBJECTS.value):
        global client
        self.db_str = db_str
        self.db = client.get_database(db_str)
        self.group_obj_coll = self.db.get_collection(coll)
        
    async def insert_group(self, group: GroupObjectModel):
        await self.group_obj_coll.insert_one(group)
        