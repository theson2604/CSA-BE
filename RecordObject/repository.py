from abc import ABC, abstractmethod
from typing import List

from FieldObject.models import FieldObjectBase
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
    async def find_one_by_id(self, id: str, projection: dict = None) -> RecordObjectModel:
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

    async def insert_one(self, record: RecordObjectModel) -> str:
        result = await self.record_coll.insert_one(record)
        return result.inserted_id

    async def get_all_with_parsing_ref_detail(
        self, field_details: List[dict], page: int = 1, page_size: int = 100
    ) -> list:
        """
        Get all Record Object with ref detail parsing \n
        :Params:
        - field_details: List[{"ref_obj_id": obj_<name>_<id>, "local_field_id": fd_<name>_<id>}]
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
        try:
            paring_pipeline = []
            for field_detail in field_details:
                ref_obj_id = field_detail.get("ref_obj_id")
                local_field_id = field_detail.get("local_field_id")
                stages = [
                    {
                        "$lookup": {
                            "from": f"{ref_obj_id}",
                            "localField": f"{local_field_id}.ref_to",
                            "foreignField": "_id",
                            "as": "ref",
                        }
                    },
                    {"$set": {f"{local_field_id}.ref_to": {"$first": "$ref"}}},
                    {
                        "$project": {
                            f"{local_field_id}.ref_to.created_at": 0,
                            f"{local_field_id}.ref_to.modified_at": 0,
                            f"{local_field_id}.ref_to.created_by": 0,
                            f"{local_field_id}.ref_to.modified_by": 0,
                            "ref": 0,
                        }
                    },
                ]
                paring_pipeline = paring_pipeline + stages
                
            paring_pipeline += [
                {"$sort": {"created_at": -1}},
                {"$skip": page},
                {"$limit": page_size}
            ]
            
            # total_records count + parsing record_details
            pipeline = [
                {
                    "$facet": {
                        "total_records": [{"$count": "total"}],
                        "record_details": paring_pipeline
                    }
                }
            ]
            
            return await self.record_coll.aggregate(pipeline).to_list(length=None)
        except Exception as e:
            print(e)
            return []

    async def find_one_by_id(self, id: str, projection: dict = None) -> RecordObjectModel:
        return await self.record_coll.find_one({"_id": id}, projection)

    # async def count_all(self, query: dict = {}) -> int:
    #     return await self.record_coll.count_documents(query)

    # async def delete_one_by_id(self, id: str) -> bool:
    #     return await self.record_coll.delete_one({"_id": id})
