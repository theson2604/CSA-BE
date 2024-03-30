from abc import ABC, abstractmethod
from typing import List, Optional

from Object.models import ObjectModel
from RootAdministrator.constants import HIDDEN_METADATA_INFO

from app.common.db_connector import DBCollections, client
from app.common.enums import FieldObjectType


class IObjectRepository(ABC):
    @abstractmethod
    async def create_indexing(self, objects: List[tuple]):
        raise NotImplementedError
        
    @abstractmethod
    async def insert_one(self, obj: ObjectModel) -> str:
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
    async def get_all_objects_with_field_details(self, obj_id: str) -> dict:
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
        
    async def create_indexing(self, objects: List[tuple]):
        """
        :Params:
            - [(object_id: obj_<name>_<id>, direction: pymongo.ASCENDING, unique: bool)]
        """
        existing_indexes = await self.obj_coll.index_information()
        for object in objects:
            if object[0] in existing_indexes:
                return
            index_key, direction = object[0], object[1]
            index_options = {"name": index_key, "unique": object[2], "sparse": False}
            await self.obj_coll.create_index(
                [(index_key, direction)], **index_options
            )

    async def insert_one(self, obj: ObjectModel) -> str:
        result = await self.obj_coll.insert_one(obj)
        return result.inserted_id

    async def find_one_by_id(self, id: str, projection: dict = None) -> ObjectModel:
        return await self.obj_coll.find_one({"_id": id}, projection)

    async def find_one_by_object_id(
        self, obj_id: str, projection: dict = None
    ) -> ObjectModel:
        """
        Find Object by obj_<name>_<id>
        """
        return await self.obj_coll.find_one({"obj_id": obj_id}, projection)

    async def get_all_objects_with_field_details(self) -> Optional[list]:
        pipeline = [
            {
                "$lookup": {
                    "from": DBCollections.FIELD_OBJECT.value,
                    "localField": "_id",
                    "foreignField": "object_id",
                    "as": "fields",
                }
            },
            {
                "$set": {
                    "fields": {
                        "$sortArray": {"input": "$fields", "sortBy": {"sorting_id": 1}}
                    }
                }
            },
        ]
        
        return await self.obj_coll.aggregate(pipeline).to_list(length=None)

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
            {
                "$set": {
                    "fields": {
                        "$sortArray": {"input": "$fields", "sortBy": {"sorting_id": 1}}
                    }
                }
            },
        ]
        async for doc in self.obj_coll.aggregate(pipeline):
            return doc

    async def count_all(self, query: dict = {}) -> int:
        return await self.obj_coll.count_documents(query)

    async def delete_one_by_id(self, id: str) -> bool:
        return await self.obj_coll.delete_one({"_id": id})
