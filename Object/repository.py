from abc import ABC, abstractmethod
from typing import List, Optional

from Object.models import ObjectModel
from RootAdministrator.constants import HIDDEN_METADATA_INFO

from app.common.db_connector import DBCollections, client
from app.common.enums import FieldObjectType


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
    async def find_one_by_object_id(
        self, obj_id: str, projection: dict = None
    ) -> ObjectModel:
        raise NotImplementedError

    @abstractmethod
    async def get_object_with_all_fields(self, obj_id: str) -> dict:
        raise NotImplementedError

    @abstractmethod
    async def count_all(self, query: dict = {}) -> int:
        raise NotImplementedError

    @abstractmethod
    async def delete_one_by_id(self, id: str) -> bool:
        raise NotImplementedError


class ObjectRepository(IObjectRepository):
    def __init__(self, db_str: str, coll: str = DBCollections.OBJECT):
        global client
        self.db_str = db_str
        self.db = client.get_database(db_str)
        self.obj_coll = self.db.get_collection(coll)

    async def insert_one(self, obj: ObjectModel) -> str:
        result = await self.obj_coll.insert_one(obj)
        return result.inserted_id

    async def find_all(
        self, query: dict = {}, projection: dict = HIDDEN_METADATA_INFO
    ) -> List[ObjectModel]:
        return await self.obj_coll.find(query, projection).to_list(length=None)

    async def find_one_by_id(self, id: str, projection: dict = None) -> ObjectModel:
        return await self.obj_coll.find_one({"_id": id}, projection)

    async def find_one_by_object_id(
        self, obj_id: str, projection: dict = None
    ) -> ObjectModel:
        return await self.obj_coll.find_one({"obj_id": obj_id}, projection)

    async def get_object_with_all_fields(self, obj_id: str) -> Optional[dict]:
        """
            :Params:
            - obj_id: _id
        """
        pipeline = [
            {"$match": {"_id": obj_id}},
            {
                "$lookup": {
                    "from": DBCollections.FIELD_OBJECT.value,
                    "localField": "_id",
                    "foreignField": "object_id",
                    "as": "fields",
                }
            },
            {"$project": {"fields.object_id": 0}},
        ]
        async for doc in self.obj_coll.aggregate(pipeline):
            return doc

    async def count_all(self, query: dict = {}) -> int:
        return await self.obj_coll.count_documents(query)

    async def delete_one_by_id(self, id: str) -> bool:
        return await self.obj_coll.delete_one({"_id": id})
