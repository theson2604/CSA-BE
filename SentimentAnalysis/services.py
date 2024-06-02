import os
import aiohttp
from fastapi import HTTPException
from FieldObject.repository import FieldObjectRepository
from Object.repository import ObjectRepository
from RecordObject.repository import RecordObjectRepository
from SentimentAnalysis.repository import SentimentModelRepository
from app.common.utils import get_current_hcm_datetime
import re


class SentimentAnalysisServices:
    def __init__(self, db_str: str):
        self.db_str = db_str
        self.sentiment_model_repo = SentimentModelRepository(db_str)
        self.obj_repo = ObjectRepository(db_str)
        self.field_obj_repo = FieldObjectRepository(db_str)
        
    async def get_all_models_with_details(self):
        return await self.sentiment_model_repo.get_all_models_with_details()
    
    async def get_all_models_prototype(self):
        return await self.sentiment_model_repo.get_all_models_prototype()
        
    async def infer_sentiment_score(self, db_str: str, config: dict, record_id: str, cur_user_id: str, access_token: str) -> dict:
        object_id = config.get("object_id")
        obj = await self.obj_repo.find_one_by_id(object_id)
        obj_id = obj.get("obj_id")
        record_repo = RecordObjectRepository(db_str, obj_id)
        
        record = await record_repo.find_one_by_id(record_id)
        # Field to score sentiment
        text = record.get(config.get("field_score"), "")
        model_id = config.get("model_id_str", "") # SentimentModel model_<name>_<id>
        field_update_score = config.get("field_update_score", "fd_dummy")
        
        if not text: 
            return -1
        body = {
            "text": text,
            "model_id": model_id
        }
        
        headers = {'Authorization': f'Bearer {access_token}'}
        async with aiohttp.ClientSession() as session:
            async with session.post(f'{os.environ.get("AI_SERVER_URL")}/predict', json=body, headers=headers) as response:
                if response.status != 200:
                    error_message = await response.text()
                    raise HTTPException(status_code=response.status, detail=error_message)
                
                score = await response.json()
                
        record.update({
            field_update_score: score.get("score"),
            "modified_by": cur_user_id,
            "modified_at": get_current_hcm_datetime()
        })
        
        await record_repo.update_one_by_id(record.pop('_id'), record)
        
        # Get field_type id of record
        pattern = r'^fd_id_\d{6}$'
        matching_keys = [key for key in record.keys() if re.match(pattern, key)]
        if matching_keys:
            record_prefix_id = record.get(matching_keys[0], "")
    
            return {"record_prefix": record_prefix_id, "score": score.get("score"), "object_id": record.get("object_id")}
        
    