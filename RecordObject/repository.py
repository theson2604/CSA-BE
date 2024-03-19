from abc import ABC, abstractmethod
from typing import List

from RecordObject.models import RecordObjectModel
from RootAdministrator.constants import HIDDEN_METADATA_INFO

from app.common.db_connector import DBCollections, client

class IRecordObjectRepository(ABC):
    @abstractmethod
    async def insert_one(self, record: RecordObjectModel) -> str:
        raise NotImplementedError
    
    @abstractmethod
    async def find_all(self, query: dict = {}) -> List[RecordObjectModel]:
        raise NotImplementedError
    
    @abstractmethod
    async def find_one_by_id(self, id: str, projection: dict = None) -> RecordObjectModel:
        raise NotImplementedError
    
    @abstractmethod
    async def count_all(self, query: dict = {}) -> int:
        raise NotImplementedError
    
    @abstractmethod
    async def delete_one_by_id(self, id: str) -> bool:
        raise NotImplementedError
    
class RecordObjectRepository(IRecordObjectRepository):
    def __init__(self, db_str: str, coll: str):
        global client
        self.db_str = db_str
        self.repo = client.get_database(db_str)
        self.record_coll = self.repo.get_collection(coll)
    
    async def insert_one(self, record: RecordObjectModel) -> str:
        result = await self.record_coll.insert_one(record)
        return result.inserted_id
    
    async def find_all(self, query: dict = {}, projection: dict = HIDDEN_METADATA_INFO) -> List[RecordObjectModel]:
        return await self.record_coll.find(query, projection).to_list(length=None)
    
    async def find_one_by_id(self, id: str, projection: dict = None) -> RecordObjectModel:
        return await self.record_coll.find_one({"_id": id}, projection)
    
    async def count_all(self, query: dict = {}) -> int:
        return await self.record_coll.count_documents(query)
    
    async def delete_one_by_id(self, id: str) -> bool:
        return await self.record_coll.delete_one({"_id": id})
    