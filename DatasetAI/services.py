from fastapi import HTTPException
from DatasetAI.repository import DatasetAIRepository
from DatasetAI.schemas import DatasetConfigSchema
from FieldObject.repository import FieldObjectRepository
from FieldObject.schemas import FieldObjectSchema
from GroupObjects.repository import GroupObjectRepository
from Object.schemas import ObjectWithFieldSchema
from Object.services import ObjectService
from app.common.enums import FieldObjectType, GroupObjectType
from app.common.errors import HTTPBadRequest
import httpx
from dotenv import load_dotenv
import os

from app.common.utils import generate_model_id

load_dotenv()

class DatasetAIServices:
    def __init__(self, db_str: str):
        self.repo = DatasetAIRepository(db_str)
        self.obj_service = ObjectService(db_str)
        self.field_obj_repo = FieldObjectRepository(db_str)
        self.group_obj_repo = GroupObjectRepository(db_str)
        self.db_str = db_str

    async def config_preprocess_dataset(self, config: DatasetConfigSchema, cur_user_id: str, access_token: str) -> str:
        config = config.model_dump()
        obj_id = config.get("obj_id")
        obj_id_str = config.get("obj_id_str")
        features_id_str = config.get("features")
        label_id_str = config.get("label")
        train_model_name = config.get("train_model_name")
        train_model_description = config.get("train_model_description")
        dataset_name = config.get("dataset_name")
        dataset_description = config.get("dataset_description")
        
        list_ids = features_id_str + [label_id_str]

        list_fields_detail = (
            await self.field_obj_repo.get_all_fields_detail_by_list_field_ids_str(
                list_ids,
                obj_id,
                {"_id": 0, "field_id": 0, "object_id": 0, "sorting_id": 0},
            )
        )

        features = list_fields_detail[:-1]
        for feature in features:
            if feature.get("field_type") not in [FieldObjectType.TEXT.value, FieldObjectType.TEXTAREA.value]:
                return HTTPBadRequest(f"feature {feature.get("field_name")} field_type must be 'text' or 'textarea'")
        
        for feature in features:
            feature["is_label"] = False
            
        label = list_fields_detail[-1]
        if label.get("field_type") not in [FieldObjectType.FLOAT.value]:
            return HTTPBadRequest(f"label {label.get("field_name")} field_type must be 'float'")
        
        label.update({"is_label": True})
        
        dataset_fields_schema = [FieldObjectSchema(**label)] + [FieldObjectSchema(**x) for x in features]
        # Find AI Datasets Group by default
        group_ai_datasets = await self.group_obj_repo.get_group_by_type(GroupObjectType.AI_DATASETS)
        object_with_fields_schema = ObjectWithFieldSchema(obj_name=dataset_name, group_obj_id=group_ai_datasets.get("_id"), fields=dataset_fields_schema)
        dataset_obj_id = await self.obj_service.create_object_with_fields(obj_with_fields=object_with_fields_schema, current_user_id=cur_user_id)
        # Get dataset obj_id_str
        dataset_obj_detail = await self.obj_service.get_object_detail_by_id(dataset_obj_id)
        dataset_obj_id_str = dataset_obj_detail.get("obj_id")
        
        body = {
            "dest_obj_id_str": dataset_obj_id_str,
            "src_obj_id_str": obj_id_str,
            "features": features_id_str,
            "label": label_id_str,
            "model_id": generate_model_id(train_model_name)
        }
        
        headers = {'Authorization': f'Bearer {access_token}'}
        async with httpx.AsyncClient() as client:
            response = await client.post(f'{os.environ.get("AI_SERVER_URL")}/preprocess', json=body, headers=headers)
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            
            histogram_labels = response.json().get("histogram_labels", {"labels": [], "counts": []})
            
        return histogram_labels
