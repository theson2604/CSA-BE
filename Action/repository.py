from typing import List, Union
from abc import ABC, abstractmethod

from Action.models import ActionBase
from app.common.db_connector import client, DBCollections
from app.common.enums import FieldObjectType

class ActionRepository:
    def __init__(self, db_str: str, coll: str = DBCollections.ACTION.value):
        global client
        self.db_str = db_str
        self.db = client.get_database(db_str)
        self.action_coll = self.db.get_collection(coll)

    async def insert_many(self, fields: List[Union[ActionBase]]) -> List[str]:
        result = await self.action_coll.insert_many(fields)
        return result.inserted_ids
    
    async def insert_one(self, action: ActionBase) -> str:
        result = await self.action_coll.insert_one(action)
        return result.inserted_id

    async def update_one_by_id(self, id: str, field: dict) -> int:
        result = await self.action_coll.update_one({"_id": id}, {"$set": field})
        return result.modified_count
    
    async def delete_one_by_id(self, id: str) -> bool:
        return await self.action_coll.delete_one({"_id": id})
    
    async def find_one_by_id(self, id: str) -> Union[ActionBase]:
        return await self.action_coll.find_one({"_id": id})
    
    async def delete_many_by_workflow_id(self, workflow_id: str):
        return await self.action_coll.delete_many({"workflow_id": workflow_id})
