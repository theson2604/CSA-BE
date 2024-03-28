from abc import ABC, abstractmethod
from typing import List
from RootAdministrator.constants import HIDDEN_METADATA_INFO
from app.common.db_connector import client
from GroupObjects.models import GroupObjectModel
from app.common.db_connector import DBCollections


class IGroupObjectRepository(ABC):
    @abstractmethod
    async def insert_one(self, group: GroupObjectModel) -> str:
        raise NotImplementedError

    @abstractmethod
    async def update_one_by_id(self, id: str, group: dict):
        raise NotImplementedError

    @abstractmethod
    async def update_many(self, groups: List[dict]) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def find_one_by_id(
        self, id: str, projection: dict = None
    ) -> GroupObjectModel:
        raise NotImplementedError

    @abstractmethod
    async def get_all_groups_with_details(self) -> List[dict]:
        raise NotImplementedError

    @abstractmethod
    async def count_all(self, query: dict = {}) -> int:
        raise NotImplementedError


class GroupObjectRepository(IGroupObjectRepository):
    def __init__(self, db_str: str, coll: str = DBCollections.GROUP_OBJECTS.value):
        global client
        self.db_str = db_str
        self.db = client.get_database(db_str)
        self.group_obj_coll = self.db.get_collection(coll)

    async def insert_one(self, group: GroupObjectModel) -> str:
        result = await self.group_obj_coll.insert_one(group)
        return result.inserted_id

    async def update_one_by_id(self, id: str, group: dict):
        await self.group_obj_coll.update_one({"_id": id}, {"$set": group})

    async def update_many(self, groups: List[dict]):
        for group in groups:
            await self.update_one_by_id(group.pop("id"), group)

    async def find_one_by_id(
        self, id: str, projection: dict = None
    ) -> GroupObjectModel:
        return await self.group_obj_coll.find_one({"_id": id}, projection)

    async def get_all_groups_with_details(self) -> List[dict]:
        pipeline = [
            {
                "$lookup": {
                    "from": DBCollections.OBJECT.value,
                    "localField": "_id",
                    "foreignField": "group_obj_id",
                    "pipeline": [
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
                                    "$sortArray": {
                                        "input": "$fields",
                                        "sortBy": {"sorting_id": 1},
                                    }
                                }
                            }
                        },
                    ],
                    "as": "objects",
                }
            },
            {
                "$set": {
                    "objects": {
                        "$sortArray": {"input": "$objects", "sortBy": {"sorting_id": 1}}
                    }
                }
            },
        ]
        
        return await self.group_obj_coll.aggregate(pipeline).to_list(length=None)

    async def count_all(self, query: dict = {}) -> int:
        return await self.group_obj_coll.count_documents(query)
