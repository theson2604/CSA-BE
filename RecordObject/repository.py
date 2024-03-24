from abc import ABC, abstractmethod
from typing import List

from FieldObject.models import FieldObjectBase
from FieldObject.repository import FieldObjectRepository
from RecordObject.models import RecordObjectModel
from RootAdministrator.constants import HIDDEN_METADATA_INFO

from app.common.db_connector import DBCollections, client


class IRecordObjectRepository(ABC):
    @abstractmethod
    async def insert_one(self, record: RecordObjectModel) -> str:
        raise NotImplementedError

    @abstractmethod
    async def get_all_with_parsing_ref_detail(
        self, field_details: List[dict], page: int = 1, page_size: int = 100
    ) -> list:
        raise NotImplementedError

    @abstractmethod
    async def find_one_by_id(
        self, id: str, projection: dict = None
    ) -> RecordObjectModel:
        raise NotImplementedError

    # @abstractmethod
    # async def count_all(self, query: dict = {}) -> int:
    #     raise NotImplementedError

    # @abstractmethod
    # async def delete_one_by_id(self, id: str) -> bool:
    #     raise NotImplementedError


class RecordObjectRepository(IRecordObjectRepository):
    def __init__(self, db_str: str, coll: str):
        global client
        self.db = client.get_database(db_str)
        self.record_coll = self.db.get_collection(coll)
        self.field_obj_repo = FieldObjectRepository(db_str)

    async def insert_one(self, record: RecordObjectModel) -> str:
        result = await self.record_coll.insert_one(record)
        return result.inserted_id

    async def get_all_with_parsing_ref_detail(
        self, object_id: str, page: int = 1, page_size: int = 100
    ) -> list:
        """
        Get all Record Object with ref detail parsing \n
        :Params:
        - object_id: _id
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
        parsed_ref_fields = await self.field_obj_repo.get_all_field_refs_deeply(
            object_id
        )
        parsing_ref_pipeline = []
        for field_detail in parsed_ref_fields:
            full_ref_field_obj_id = field_detail.get(
                "ref_field_obj_id"
            )  # obj_<name>_<id>.fd_<name>_<id>
            ref_obj_id = full_ref_field_obj_id.split(".")[0]
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
            # Pasrse Linking Fields
            linking_fields = field_detail.get("linking_fields", [])
            for linking_field in linking_fields[:-1]:
                local_field_id = linking_field.get("field_id")
                full_ref_field_obj_id = linking_field.get(
                    "ref_field_obj_id"
                )  # obj_<name>_<id>.fd_<name>_<id>
                ref_obj_id = full_ref_field_obj_id.split(".")[0]
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
                        f"{base_local_field_id}.ref_to.created_at": 0,
                        f"{base_local_field_id}.ref_to.modified_at": 0,
                        f"{base_local_field_id}.ref_to.created_by": 0,
                        f"{base_local_field_id}.ref_to.modified_by": 0,
                        "ref": 0,
                    },
                }
            ]

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

    async def find_one_by_id(
        self, id: str, projection: dict = None
    ) -> RecordObjectModel:
        return await self.record_coll.find_one({"_id": id}, projection)

    # async def count_all(self, query: dict = {}) -> int:
    #     return await self.record_coll.count_documents(query)

    # async def delete_one_by_id(self, id: str) -> bool:
    #     return await self.record_coll.delete_one({"_id": id})
