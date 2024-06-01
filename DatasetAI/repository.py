from DatasetAI.models import DatasetAIModel
from app.common.db_connector import DBCollections
from app.common.db_connector import client


class DatasetAIRepository:
    def __init__(self, db_str: str, coll: str = DBCollections.DATASET_AI.value):
        global client
        self.db_str = db_str
        self.db = client.get_database(db_str)
        self.dataset_ai_coll = self.db.get_collection(coll)

    async def insert_one(self, dataset: DatasetAIModel) -> str:
        result = await self.dataset_ai_coll.insert_one(dataset)
        return result.inserted_id

    async def find_one_by_id(self, id: str, projection: dict = {}):
        return await self.dataset_ai_coll.find_one({"_id": id}, projection)
    
    async def find_one_by_dataset_obj_id_str(self, dataset_obj_id_str: str, projection: dict = {}):
        return await self.dataset_ai_coll.find_one({"dataset_obj_id_str": dataset_obj_id_str}, projection)

    async def get_historgram_labels(self, field_id: str):
        pipeline = [
            {"$group": {"_id": f"${field_id}", "count": {"$sum": 1}}},
            {"$sort": {"_id": 1}}
        ]
        return await self.dataset_ai_coll.aggregate(pipeline).to_list(length=None)