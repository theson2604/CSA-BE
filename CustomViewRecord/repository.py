from typing import List, Union
from CustomViewRecord.models import CustomViewRecordModel
from app.common.db_connector import client, DBCollections


class CustomViewRecordRepository:
    def __init__(self, db_str: str, coll = DBCollections.CUSTOM_VIEW_RECORD.value):
        global client
        self.db = client.get_database(db_str)
        self.view_record_coll = self.db.get_collection(coll)
        pass

    async def insert_one(self, view_record: CustomViewRecordModel) -> str:
        result = await self.view_record_coll.insert_one(view_record)
        return result.inserted_id


    async def find_one_by_id(self, id: str) -> Union[CustomViewRecordModel]:
        return await self.view_record_coll.find_one({"_id": id})
    
    async def find_one(self, query: dict, projection: dict = None) -> Union[CustomViewRecordModel]:
        return await self.view_record_coll.find_one(query, projection)
    
    async def find_many(self,  query: dict, projection: dict = None) -> List[Union[CustomViewRecordModel]]:
        cursor = self.view_record_coll.find(query, projection)
        return await cursor.to_list(length=None)
    
    async def update_one_by_id(self, id: str, view_record: dict) -> str:
        result = await self.view_record_coll.update_one({"_id": id}, {"$set": view_record})
        return result.modified_count
    
    async def delete_one_by_id(self, id: str) -> int:
        return (await self.view_record_coll.delete_one({"_id": id})).deleted_count
    
    async def delete_many(self, query: dict) -> int:
        return (await self.view_record_coll.delete_many(query)).deleted_count