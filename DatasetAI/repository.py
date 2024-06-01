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
    
    