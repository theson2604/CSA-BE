from typing import List, Union
from abc import ABC, abstractmethod

from FieldObject.models import (
    FieldObjectBase,
    FieldEmail,
    FieldPhoneNumber,
    FieldReferenceObject,
    FieldReferenceFieldObject,
    FieldSelect,
    FieldText,
)

from app.common.db_connector import client, DBCollections
from app.common.enums import FieldObjectType


class IFieldObjectRepository(ABC):
    @abstractmethod
    async def insert_many(self, fields: List[Union[FieldObjectBase]]) -> List[str]:
        raise NotImplementedError

    @abstractmethod
    async def update_one_by_id(self, id: str, field: dict):
        raise NotImplementedError

    @abstractmethod
    async def update_many(self, fields: List[dict]):
        raise NotImplementedError

    @abstractmethod
    async def find_one_by_id(self, id: str) -> Union[FieldObjectBase]:
        raise NotImplementedError

    @abstractmethod
    async def find_one_by_field_id(
        self, obj_id: str, fld_id: str
    ) -> Union[FieldObjectBase]:
        raise NotImplementedError

    @abstractmethod
    async def find_all(self) -> List[Union[FieldObjectBase]]:
        raise NotImplementedError

    @abstractmethod
    async def get_all_by_field_types(
        self, obj_id: str, field_types: List[FieldObjectType]
    ) -> List[Union[FieldObjectBase]]:
        raise NotImplementedError


class FieldObjectRepository(IFieldObjectRepository):
    def __init__(self, db_str: str, coll: str = DBCollections.FIELD_OBJECT.value):
        global client
        self.db_str = db_str
        self.db = client.get_database(db_str)
        self.field_object_coll = self.db.get_collection(coll)

    async def insert_many(self, fields: List[Union[FieldObjectBase]]) -> List[str]:
        result = await self.field_object_coll.insert_many(fields)
        return result.inserted_ids

    async def update_one_by_id(self, id: str, field: dict):
        await self.field_object_coll.update_one({"_id": id}, {"$set": field})

    async def update_many(self, fields: List[dict]):
        for field in fields:
            await self.update_one_by_id(field.pop("id"), field)  # Have to check more

    async def find_one_by_id(self, id: str) -> Union[FieldObjectBase]:
        return await self.field_object_coll.find_one({"_id": id})

    async def find_one_by_field_id(
        self, obj_id: str, fld_id: str
    ) -> Union[FieldObjectBase]:
        """
        Find Field Object by field_id fd_<name>_id \n
        :Params:
            - obj_id: _id
            - fld_id: fd_<name>_<id>
        """
        return await self.field_object_coll.find_one(
            {"object_id": obj_id, "field_id": fld_id}
        )

    async def find_all(self, query: dict = {}) -> List[Union[FieldObjectBase]]:
        return await self.field_object_coll.find(query).to_list(length=None)
    async def get_all_by_field_types(
        self, obj_id: str, field_types: List[FieldObjectType]
    ) -> List[Union[FieldObjectBase]]:
        """
        Get all Fields Object by a list of field_type \n
        :Params:
            - obj_id: _id
            - field_types: List[FieldObjectType]
        """
        pipeline = [
            {
                "$match": {
                    "$and": [
                        {"object_id": obj_id},
                        {"field_type": {"$in": field_types}},
                    ]
                }
            }
        ]
        
        return await self.field_object_coll.aggregate(pipeline).to_list(length=None)
