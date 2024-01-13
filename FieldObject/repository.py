from typing import List, Union
from abc import ABC, abstractmethod

from FieldObject.models import FieldEmail, FieldPhoneNumber, FieldReferenceObject, FieldSelect, FieldText

from app.common.db_connector import client, DBCollections


class IFieldObjectRepository(ABC):
    @abstractmethod
    async def insert_many(self, fields: List[Union[FieldText, FieldEmail, FieldSelect, FieldPhoneNumber, FieldReferenceObject, None]]) -> List[str]:
        raise NotImplementedError
    
    @abstractmethod
    async def update_one_by_id(self, id: str, field: dict) -> bool:
        raise NotImplementedError
    
    @abstractmethod
    async def update_many(self, fields: List[dict]) -> bool:
        raise NotImplementedError
    
    @abstractmethod
    async def find_all(self) -> List[Union[FieldText, FieldEmail, FieldSelect, FieldPhoneNumber, FieldReferenceObject]]:
        raise NotImplementedError
    
class FieldObjectRepository(IFieldObjectRepository):
    def __init__(self, db_str: str, coll: str = DBCollections.FIELD_OBJECT.value):
        global client
        self.db_str = db_str
        self.db = client.get_database(db_str)
        self.field_object_coll = self.db.get_collection(coll)
        
    async def insert_many(self, fields: List[Union[FieldText, FieldEmail, FieldSelect, FieldPhoneNumber, FieldReferenceObject, None]]) -> List[str]:
        result = await self.field_object_coll.insert_many(fields)
        ids = result.inserted_ids
        return ids if ids else []
    
    async def update_one_by_id(self, id: str, field: dict) -> bool:
        result = await self.field_object_coll.update_one({"_id": id}, {"$set": field})
        return result.modified_count > 0
    
    async def update_many(self, fields: List[dict]) -> bool:
        for field in fields:
            result = await self.update_one_by_id(field.pop("id"), field) # Have to check more
            if not result: return False
            
        return True
    
    async def find_all(self) -> List[Union[FieldText, FieldEmail, FieldSelect, FieldPhoneNumber, FieldReferenceObject]]:
        raise NotImplementedError
        