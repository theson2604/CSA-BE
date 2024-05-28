from DatasetAI.models import DatasetAIModel
from app.common.db_connector import DBCollections
from app.common.db_connector import client

class DatasetAIRepository:
    def __init__(self, db_str: str, coll: str = DBCollections.AI_DATASET.value):
        global client
        self.db_str = db_str
        self.db = client.get_database(db_str)
        self.group_obj_coll = self.db.get_collection(coll)

    async def insert_one(self, group: DatasetAIModel) -> str:
        result = await self.group_obj_coll.insert_one(group)
        return result.inserted_id
    
    
    async def set_all_field_keys():
        return