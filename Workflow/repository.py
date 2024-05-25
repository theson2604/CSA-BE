from abc import ABC, abstractmethod
from typing import List, Optional

from Object.models import ObjectModel

from Workflow.models import WorkflowModel
from app.common.db_connector import DBCollections, client
from app.common.enums import FieldObjectType

class WorkflowRepository:
    def __init__(self, db_str: str, coll: str = DBCollections.WORKFLOW):
        global client
        self.db_str = db_str
        self.db = client.get_database(db_str)
        # self.obj_coll = self.db.get_collection(coll)
        self.workflow_coll = self.db.get_collection(coll)
        
    # async def create_indexing(self, objects: List[tuple]):
    #     """
    #     :Params:
    #         - [(object_id: obj_<name>_<id>, direction: pymongo.ASCENDING, unique: bool)]
    #     """
    #     existing_indexes = await self.obj_coll.index_information()
    #     for object in objects:
    #         if object[0] in existing_indexes:
    #             return
    #         index_key, direction = object[0], object[1]
    #         index_options = {"name": index_key, "unique": object[2], "sparse": False}
    #         await self.obj_coll.create_index(
    #             [(index_key, direction)], **index_options
    #         )

    async def insert_one(self, workflow: WorkflowModel) -> str:
        result = await self.workflow_coll.insert_one(workflow)
        return result.inserted_id

    async def find_one_by_id(self, id: str, projection: dict = None) -> ObjectModel:
        return await self.workflow_coll.find_one({"_id": id}, projection)
    
    async def find_one_by_name(self, name: str, projection: dict = None):
        return await self.find_one({"_id": id}, projection)
        
    async def find_many(self, query: dict, projection: dict = None):
        cursor = await self.workflow_coll.find(query, projection)
        workflows = []
        for workflow in cursor:
            workflows.append(workflow)

        return workflows

    # async def get_all_objects_with_field_details(self) -> Optional[list]:
    #     pipeline = [
    #         {
    #             "$lookup": {
    #                 "from": DBCollections.FIELD_OBJECT.value,
    #                 "localField": "_id",
    #                 "foreignField": "object_id",
    #                 "as": "fields",
    #             }
    #         },
    #         {
    #             "$set": {
    #                 "fields": {
    #                     "$sortArray": {"input": "$fields", "sortBy": {"sorting_id": 1}}
    #                 }
    #             }
    #         },
    #     ]
        
    #     return await self.obj_coll.aggregate(pipeline).to_list(length=None)

    async def get_workflow_with_all_actions(self, workflow_id: str) -> Optional[dict]:
        """
        :Params:
        - obj_id: _id
        """
        pipeline = [
            {"$match": {"_id": workflow_id}},
            {
                "$lookup": {
                    "from": DBCollections.ACTION.value,
                    "localField": "_id",
                    "foreignField": "workflow_id",
                    "as": "actions",
                }
            },
            {
                "$set": {
                    "actions": {
                        "$sortArray": {"input": "$actions", "sortBy": {"sorting_id": 1}}
                    }
                }
            },
            {
                "$project": {
                    "_id": 1,
                    "actions": 1
                }
            }
        ]
        async for doc in self.workflow_coll.aggregate(pipeline):
            return doc

    # async def count_all(self, query: dict = {}) -> int:
    #     return await self.obj_coll.count_documents(query)
    async def delete_one_by_id(self, id: str) -> bool:
        return await self.workflow_coll.delete_one({"_id": id})
