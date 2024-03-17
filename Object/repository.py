from abc import ABC, abstractmethod
from typing import List

from Object.models import ObjectModel
from RootAdministrator.constants import HIDDEN_METADATA_INFO

from app.common.db_connector import DBCollections, client

class IObjectRepository(ABC):
    @abstractmethod
    async def insert_one(self, obj: ObjectModel) -> str:
        raise NotImplementedError
    
    @abstractmethod
    async def find_all(self, query: dict = {}) -> List[ObjectModel]:
        raise NotImplementedError
    
    @abstractmethod
    async def find_one_by_id(self, id: str, projection: dict = None) -> ObjectModel:
        raise NotImplementedError
    
    @abstractmethod
    async def find_one_by_object_id(self, obj_id: str, projection: dict = None) -> ObjectModel:
        raise NotImplementedError
    
    @abstractmethod
    async def count_all(self, query: dict = {}) -> int:
        raise NotImplementedError
    

class ObjectRepository(IObjectRepository):
    def __init__(self, db_str: str, coll: str = DBCollections.OBJECT):
        global client
        self.db_str = db_str
        self.repo = client.get_database(db_str)
        self.obj_coll = self.repo.get_collection(coll)
    
    async def insert_one(self, obj: ObjectModel) -> str:
        result = await self.obj_coll.insert_one(obj)
        return result.inserted_id
    
    async def find_all(self, query: dict = {}, projection: dict = HIDDEN_METADATA_INFO) -> List[ObjectModel]:
        return await self.obj_coll.find(query, projection).to_list(length=None)
    
    async def find_one_by_id(self, id: str, projection: dict = None) -> ObjectModel:
        return await self.obj_coll.find_one({"_id": id}, projection)
    
    async def find_one_by_object_id(self, obj_id: str, projection: dict = None) -> ObjectModel:
        return await self.obj_coll.find_one({"obj_id": obj_id}, projection)
    
    async def count_all(self, query: dict = {}) -> int:
        return await self.obj_coll.count_documents(query)
    