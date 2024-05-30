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

class FieldObjectRepository:
    def __init__(self, db_str: str, coll: str = DBCollections.FIELD_OBJECT.value):
        global client
        self.db_str = db_str
        self.db = client.get_database(db_str)
        self.field_object_coll = self.db.get_collection(coll)

    async def create_indexing(self, field_id: str, index_name: str):
        existing_indexes = await self.field_object_coll.index_information()
        if index_name in existing_indexes:
            return
        index_key = field_id
        index_options = {"name": index_name, "unique": False, "sparse": False}
        await self.field_object_coll.create_index(index_key, **index_options)

    async def insert_many(self, fields: List[Union[FieldObjectBase]]) -> List[str]:
        # await self.create_indexing(field_id="field_id", index_name="field_id")
        result = await self.field_object_coll.insert_many(fields)
        return result.inserted_ids
    
    async def insert_one(self, field: FieldObjectBase) -> str:
        result = await self.field_object_coll.insert_one(field)
        return result.inserted_id

    async def update_one_by_id(self, id: str, field: dict) -> int:
        result = await self.field_object_coll.update_one({"_id": id}, {"$set": field})
        return result.modified_count

    async def update_many(self, fields: List[dict]):
        for field in fields:
            await self.update_one_by_id(field.pop("_id"), field)  # Have to check more

    async def find_one_by_id(self, id: str) -> Union[FieldObjectBase]:
        # self.field_object_coll.
        return await self.field_object_coll.find_one({"_id": id})

    async def find_one_by_field_id_str(
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
    
    async def find_many_by_field_ids_str(
        self, obj_id: str, fld_ids: List[str], projection: dict = None
    ) -> Union[FieldObjectBase]:
        """
        Find Field Object by field_id fd_<name>_id \n
        :Params:
            - obj_id: _id
            - fld_id: fd_<name>_<id>
        """
        cursor = self.field_object_coll.find(
            {"object_id": obj_id, "field_id": {"$in": fld_ids}}, projection
        )

        return await cursor.to_list(length=None)
    
    async def find_one_by_field_type(
        self, obj_id: str, field_type: str
    ) -> Union[FieldObjectBase]:
        return await self.field_object_coll.find_one({"object_id": obj_id, "field_type": field_type})
    
    async def find_one(self, query: dict, projection: dict = None):
        return await self.field_object_coll.find_one(query, projection)

    async def find_all(self, query: dict = {}) -> List[Union[FieldObjectBase]]:
        return await self.field_object_coll.find(query).to_list(length=None)
    
    async def find_all_by_obj_id(self, obj_id: str, projection: dict = {}) -> List[Union[FieldObjectBase]]:
        return await self.field_object_coll.find({"object_id": obj_id}, projection).to_list(length=None)
    
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

    async def get_all_field_refs_deeply(self, obj_id: str) -> list:
        """
        Get all Ref Fields with parsing detail deeply \n
        :Params:
        - obj_id: _id
        """
        pipeline = [
            {
                "$match": {
                    "$and": [
                        {"object_id": obj_id},
                        {
                            "field_type": {
                                "$in": [
                                    FieldObjectType.REFERENCE_OBJECT.value,
                                    FieldObjectType.REFERENCE_FIELD_OBJECT.value,
                                ]
                            }
                        },
                    ]
                }
            },
        ]
        
        field_refs = await self.field_object_coll.aggregate(pipeline).to_list(length=None)
        
        for field_ref in field_refs:
            if field_ref.get("field_type") == FieldObjectType.REFERENCE_FIELD_OBJECT.value:
                ref_obj_id_value = field_ref.get("ref_obj_id_value") # _id
                ref_field_obj_id = field_ref.get("ref_field_obj_id") # obj_objectb_386.fd_fieldb_149
                ref_field_id_str = ref_field_obj_id.split(".")[1]
                visited = [field_ref.get("_id")]
                
                linking_fields = await self.traverse_ref_fields(ref_obj_id_value, ref_field_id_str, visited)
                
                field_ref.update({"linking_fields": linking_fields})
                
        return field_refs
                
    async def traverse_ref_fields(self, obj_id, field_id_str, visited):
        field = await self.find_one_by_field_id_str(obj_id, field_id_str)
        
        if field and field.get("_id") in visited: raise Exception("Infinite ref field loop")
        
        if field and field.get("field_type") == FieldObjectType.REFERENCE_FIELD_OBJECT.value:    
            ref_obj_id_value = field.get("ref_obj_id_value") # _id
            ref_field_obj_id = field.get("ref_field_obj_id") # obj_objectb_386.fd_fieldb_149
            ref_field_id_str = ref_field_obj_id.split(".")[1]
            
            visited += [field.get("_id")]
            
            return [field] + await self.traverse_ref_fields(ref_obj_id_value, ref_field_id_str, visited)
        
        # elif field and field.get("field_type") is FieldObjectType.REFERENCE_OBJECT.value:
            
        return []
    