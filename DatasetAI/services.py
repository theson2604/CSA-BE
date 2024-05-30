import asyncio
import re
import aiohttp
from bson import ObjectId
from fastapi import HTTPException
from DatasetAI.models import DatasetAIModel
from DatasetAI.repository import DatasetAIRepository
from DatasetAI.schemas import DatasetConfigSchema
from FieldObject.repository import FieldObjectRepository
from FieldObject.schemas import FieldObjectSchema
from GroupObjects.repository import GroupObjectRepository
from Object.repository import ObjectRepository
from Object.schemas import ObjectWithFieldSchema
from Object.services import ObjectService
from RecordObject.repository import RecordObjectRepository
from RecordObject.services import RecordObjectService
from app.common.enums import FieldObjectType, GroupObjectType
from app.common.errors import HTTPBadRequest
import httpx
from dotenv import load_dotenv
import os
import copy
from app.common.utils import generate_model_id, get_current_hcm_datetime
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatasetAIServices:
    def __init__(self, db_str: str):
        self.repo = DatasetAIRepository(db_str)
        self.obj_service = ObjectService(db_str)
        self.field_obj_repo = FieldObjectRepository(db_str)
        self.group_obj_repo = GroupObjectRepository(db_str)
        self.db_str = db_str

    async def config_preprocess_dataset(self, config: DatasetConfigSchema, cur_user_id: str, access_token: str) -> dict:
        config = config.model_dump()
        
        obj_id = config.get("obj_id")
        obj_id_str = config.get("obj_id_str")
        features_id_str = config.get("features")
        label_id_str = config.get("label")
        dataset_name = config.get("dataset_name")
        dataset_description = config.get("dataset_description")
        
        list_ids = features_id_str + [label_id_str]

        list_fields_detail = (
            await self.field_obj_repo.find_many_by_field_ids_str(
                obj_id,
                list_ids,
                {"_id": 0, "object_id": 0, "sorting_id": 0},
            )
        )
        features = []
        cpy_list_fields_detail = copy.deepcopy(list_fields_detail)
        for feature in features_id_str:
            for field in cpy_list_fields_detail:
                if field.get("field_id") == feature:
                    if field.get("field_type") not in [FieldObjectType.TEXT.value, FieldObjectType.TEXTAREA.value]:
                        return HTTPBadRequest(f"feature {field.get("field_name")} field_type must be 'text' or 'textarea'")
                    
                    field.pop("field_id")
                    field.update({"is_label": False})
                    features += [field]
                    break
        
        label = {}
        for field in cpy_list_fields_detail:
            if field.get("field_id") == label_id_str:
                if field.get("field_type") not in [FieldObjectType.INTEGER.value]:
                    return HTTPBadRequest(f"label {field.get("field_name")} field_type must be 'integer'")

                field.pop("field_id")
                field.update({"is_label": True})
                label = field
                break
                
        dataset_fields_schema = [FieldObjectSchema(**x) for x in features] + [FieldObjectSchema(**label)]
        # Create new AI Dataset Object in group "AI Datasets" by default
        group_ai_datasets = await self.group_obj_repo.get_group_by_type(GroupObjectType.AI_DATASETS)
        object_with_fields_schema = ObjectWithFieldSchema(obj_name=dataset_name, group_obj_id=group_ai_datasets.get("_id"), fields=dataset_fields_schema)
        dataset_obj_id = await self.obj_service.create_object_with_fields(obj_with_fields=object_with_fields_schema, current_user_id=cur_user_id)
        
        dataset_obj_detail = await self.obj_service.get_object_detail_by_id(dataset_obj_id)
        dataset_obj_id_str = dataset_obj_detail.get("obj_id")
        
        # Map src record's field_id_str to new ones [new_feature_ids, new_label_id]
        field_mapping = {}
        dataset_fields_detail= await self.field_obj_repo.find_all_by_obj_id(dataset_obj_id, {"_id": 0, "field_id": 1, "field_name": 1})
        for src_field in list_fields_detail:
            for dataset_field in dataset_fields_detail:
                if src_field.get("field_name") == dataset_field.get("field_name"):
                    field_mapping.update({src_field.get("field_id"): dataset_field.get("field_id")})
                    continue
                
        body = {
            "dest_obj_id": dataset_obj_id,
            "dest_obj_id_str": dataset_obj_id_str,
            "src_obj_id_str": obj_id_str,
            "features": features_id_str,
            "label": label_id_str,
            "field_mapping": field_mapping
        }
        
        headers = {'Authorization': f'Bearer {access_token}'}
        async with aiohttp.ClientSession() as session:
            async with session.post(f'{os.environ.get("AI_SERVER_URL")}/preprocess', json=body, headers=headers) as response:
                if response.status != 200:
                    error_message = await response.text()
                    raise HTTPException(status_code=response.status, detail=error_message)
                
                histogram_labels = await response.json()
                
        record_service = RecordObjectService(self.db_str, dataset_obj_id_str, dataset_obj_id)
        preprocessed_records = await record_service.get_all_records_with_detail(dataset_obj_id, page=1, page_size=10)
        
        dataset_model = DatasetAIModel(
            id=str(ObjectId()),
            name=dataset_name,
            features=[field_mapping[feature] for feature in features_id_str],
            label=field_mapping[label_id_str],
            dataset_obj_id_str=dataset_obj_id_str,
            description=dataset_description,
            **histogram_labels
        )
        
        inserted_config_id = await self.repo.insert_one(dataset_model.model_dump(by_alias=True))
            
        return {"config_id": inserted_config_id, "records": preprocessed_records, **histogram_labels}
    
    async def infer_sentiment_score(self, db_str: str, config: dict, record_id: str, cur_user_id: str, access_token: str):
        object_id = config.get("object_id")
        obj_repo = ObjectRepository(db_str)
        obj = await obj_repo.find_one_by_id(object_id)
        obj_id = obj.get("obj_id")
        record_repo = RecordObjectRepository(db_str, obj_id)
        
        record = await record_repo.get_one_by_id_with_parsing_ref_detail(record_id, object_id)[0]
        # Field to score sentiment
        text = record.get(config.get("field_to_score"), "")
        model_id = config.get("sentiment_model", "") # SentimentModel model_<name>_<id>
        
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
                
        # Auto create, update SENTIMENT_SCORE field for record
        field_score_id_str = await self.field_obj_repo.find_and_create_field_sentiment_score(obj_id)
        record.update({
            field_score_id_str: score.get("score"),
            "modified_by": cur_user_id,
            "modified_at": get_current_hcm_datetime()
        })
        record_repo.insert_one(record)
        
        # Get field_type id of record
        pattern = r'^fd_id_\d{6}$'
        matching_keys = [key for key in record.keys() if re.match(pattern, key)]
        if matching_keys:
            record_prefix_id = record.get(matching_keys[0], "")
    
            return {"record_prefix": record_prefix_id, "score": score}
