from abc import ABC, abstractmethod
from typing import List

from FieldObject.models import FieldObjectBase
from FieldObject.repository import FieldObjectRepository
from RecordObject.models import RecordObjectModel
from RootAdministrator.constants import HIDDEN_METADATA_INFO

from app.common.db_connector import DBCollections, client
from app.common.enums import FieldObjectType

class RecordObjectRepository:
    def __init__(self, db_str: str, coll: str):
        global client
        self.db = client.get_database(db_str)
        self.record_coll = self.db.get_collection(coll)
        self.field_obj_repo = FieldObjectRepository(db_str)

    async def create_indexing(self, fields: List[tuple]):
        """
        :Params:
            - [(field_id: fd_<name>_<id>, direction: pymongo.ASCENDING, unique: bool)]
        """
        existing_indexes = await self.record_coll.index_information()
        for field in fields:
            if field[0] in existing_indexes:
                return
            index_key, direction = field[0], field[1]
            index_options = {"name": index_key, "unique": field[2], "sparse": False}
            await self.record_coll.create_index(
                [(index_key, direction)], **index_options
            )

    async def insert_one(self, record: RecordObjectModel) -> str:
        result = await self.record_coll.insert_one(record)
        return result.inserted_id
    
    async def insert_many(self, records: List[RecordObjectModel]) -> str:
        result = await self.record_coll.insert_many(records)
        return [inserted_id for inserted_id in result.inserted_ids]

    async def get_parsing_ref_detail_pipeline(self, object_id: str) -> List[dict]:
        """
        Get parsing ref detail pipeline \n
        :Params:
        - object_id: Object's _id
        """
        deep_ref_fields = await self.field_obj_repo.get_all_field_refs_deeply(object_id)
        parsing_ref_pipeline = []
        for field_detail in deep_ref_fields:
            full_ref_field_obj_id = (
                field_detail.get("ref_obj_id")
                if field_detail.get("field_type") == FieldObjectType.REFERENCE_OBJECT
                else field_detail.get("ref_field_obj_id")
            )

            ref_obj_id = (
                full_ref_field_obj_id
                if field_detail.get("field_type") == FieldObjectType.REFERENCE_OBJECT
                else full_ref_field_obj_id.split(".")[0]
            )

            base_local_field_id = field_detail.get("field_id")
            local_field_accumulator = f"{base_local_field_id}"

            stages = [
                {
                    "$lookup": {
                        "from": f"{ref_obj_id}",
                        "localField": f"{base_local_field_id}.ref_to",
                        "foreignField": "_id",
                        "as": "ref",
                    }
                },
                {"$set": {f"{base_local_field_id}.ref_to": {"$first": "$ref"}}},
            ]
            parsing_ref_pipeline = parsing_ref_pipeline + stages
            # Parse Linking Fields
            linking_fields = field_detail.get("linking_fields", [])
            for linking_field in linking_fields:
                local_field_id = linking_field.get("field_id")

                full_ref_field_obj_id = (
                    linking_field.get("ref_obj_id")
                    if linking_field.get("field_type")
                    == FieldObjectType.REFERENCE_OBJECT
                    else linking_field.get("ref_field_obj_id")
                )

                ref_obj_id = (
                    full_ref_field_obj_id
                    if linking_field.get("field_type")
                    == FieldObjectType.REFERENCE_OBJECT
                    else full_ref_field_obj_id.split(".")[0]
                )

                local_field_accumulator = (
                    f"{local_field_accumulator}.ref_to.{local_field_id}"
                )

                stages = [
                    {
                        "$lookup": {
                            "from": ref_obj_id,
                            "localField": f"{local_field_accumulator}.ref_to",
                            "foreignField": "_id",
                            "as": "ref",
                        },
                    },
                    {
                        "$set": {
                            f"{base_local_field_id}.ref_to": {
                                "$first": "$ref",
                            },
                            f"{base_local_field_id}.field_value": f"${local_field_accumulator}.field_value",
                        },
                    },
                ]

                parsing_ref_pipeline = parsing_ref_pipeline + stages

            parsing_ref_pipeline += [
                {
                    "$project": {
                        "created_at": 0,
                        "modified_at": 0,
                        "created_by": 0,
                        "modified_by": 0,
                        "object_id": 0,
                        f"{base_local_field_id}.ref_to.created_at": 0,
                        f"{base_local_field_id}.ref_to.modified_at": 0,
                        f"{base_local_field_id}.ref_to.created_by": 0,
                        f"{base_local_field_id}.ref_to.modified_by": 0,
                        "ref": 0,
                    },
                }
            ]

        return parsing_ref_pipeline

    async def get_all_with_parsing_ref_detail(
        self, object_id: str, page: int = 1, page_size: int = 100
    ) -> list:
        """
        Get all Record Object with ref detail parsing \n
        :Params:
        - object_id: Object's _id
        - page: Starting from 1
        - page_size: int = 100 \n
        :Return:
        [
            {
                "total_records": [{"total": int}],
                "record_details": List[RecordObjectModel]
            }
        ]
        """
        parsing_ref_pipeline = await self.get_parsing_ref_detail_pipeline(object_id)

        parsing_ref_pipeline += [
            {"$sort": {"created_at": -1}},
            {"$skip": page},
            {"$limit": page_size},
        ]

        # total_records count + parsing record_details
        pipeline = [
            {
                "$facet": {
                    "total_records": [{"$count": "total"}],
                    "record_details": parsing_ref_pipeline,
                }
            }
        ]

        return await self.record_coll.aggregate(pipeline).to_list(length=None)

    async def get_one_by_id_with_parsing_ref_detail(
        self, record_id: str, object_id: str
    ) -> list:
        one_record_pipeline = [{"$match": {"_id": record_id}}]
        parsing_ref_pipeline = await self.get_parsing_ref_detail_pipeline(object_id)

        pipeline = one_record_pipeline + parsing_ref_pipeline
        return await self.record_coll.aggregate(pipeline).to_list(length=None)

    async def get_many_by_ids_with_parsing_ref_detail(
        self, list_ids: List[str], object_id: str
    ) -> list:
        one_record_pipeline = [{"$match": {"_id": {"$in": list_ids}}}]
        parsing_ref_pipeline = await self.get_parsing_ref_detail_pipeline(object_id)
        # Scoring order
        scoring_order_pipeline = [
            {"$addFields": {"orderIndex": {"$indexOfArray": [list_ids, "$_id"]}}},
            {"$sort": {"orderIndex": 1}},
            {"$unset": "orderIndex"},
        ]
        pipeline = one_record_pipeline + parsing_ref_pipeline + scoring_order_pipeline
        return await self.record_coll.aggregate(pipeline).to_list(length=None)

    async def find_one_by_id(
        self, id: str, projection: dict = None
    ) -> RecordObjectModel:
        return await self.record_coll.find_one({"_id": id}, projection)

    async def find_all(
        self, query: dict = {}, projection: dict = None
    ) -> List[RecordObjectModel]:
        return await self.record_coll.find(query, projection).to_list(length=None)

    async def count_all(self, query: dict = {}) -> int:
        return await self.record_coll.count_documents(query)

    # async def delete_one_by_id(self, id: str) -> bool:
    #     return await self.record_coll.delete_one({"_id": id})

    async def update_one_by_id(self, id: str, record: dict) -> int:
        result = await self.record_coll.update_one({"_id": id}, {"$set": record})
        return result.modified_count