from app.common.db_connector import DBCollections
from app.common.db_connector import client


class SentimentModelRepository:
    def __init__(self, db_str: str, coll: str = DBCollections.SENTIMENT_MODEL.value):
        global client
        self.db_str = db_str
        self.db = client.get_database(db_str)
        self.sentiment_model_coll = self.db.get_collection(coll)

    async def get_all_models_with_details(self):
        pipeline = [
            {
                "$lookup": {
                    "from": DBCollections.DATASET_AI.value,
                    "localField": "dataset_obj_id",
                    "foreignField": "_id",
                    "as": "ref",
                }
            },
            {"$set": {"dataset_name": {"$first": "$ref.name"}}},
            {"$project": {"ref": 0}},
            {
                "$lookup": {
                    "from": DBCollections.TRAINING_EPOCH.value,
                    "localField": "model_id",
                    "foreignField": "model_id_str",
                    "as": "epochs",
                }
            },
        ]

        return await self.sentiment_model_coll.aggregate(pipeline).to_list(length=None)
    
    async def get_all_models_prototype(self):
        return await self.sentiment_model_coll.find({}, {"name": 1, "model_id": 1}).to_list(length=None)
