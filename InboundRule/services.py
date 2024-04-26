from fastapi import File, UploadFile
from FieldObject.repository import FieldObjectRepository
from FieldObject.services import FieldObjectService
from InboundRule.schemas import *
from abc import ABC, abstractmethod
from Object.repository import ObjectRepository
from Object.schemas import ObjectWithFieldSchema
from Object.services import ObjectService
from app.common.db_connector import DBCollections
from app.common.enums import FieldObjectType
from app.common.errors import HTTPBadRequest
from app.common.utils import get_current_record_id, update_record_id
from RecordObject.services import RecordObjectService
from RecordObject.repository import RecordObjectRepository
import asyncio
import json
import pandas as pd 
import time

class IInboundRule(ABC):
    @abstractmethod
    def process_data(data, mapping):
        raise NotImplementedError

    @abstractmethod
    async def inbound_file(self, file_inbound: dict, user_id: str):
        raise NotImplementedError
    
    @abstractmethod
    async def inbound_file_with_new_obj(self, config: FileObjectSchema, file: UploadFile = File(...)):
        raise NotImplementedError

class InboundRule(IInboundRule):
    def __init__(self, db, obj_id: str = None, obj_id_str: str = None):
        self.field_obj_repo = FieldObjectRepository(db)
        self.obj_repo = ObjectRepository(db)

        if obj_id_str != None:
            self.record_repo = RecordObjectRepository(db, obj_id_str)
            self.record_services = RecordObjectService(db, obj_id_str, obj_id)

        self.obj_services = ObjectService(db)
        self.db_str = db

    @staticmethod
    def process_data(df, config: dict):
        mapping = json.loads(config.get("map"))
        object_id = config.get("object")
        cols = []

        for key in mapping:
            if key not in df.columns:
                raise HTTPBadRequest(f"Can not find column ${key} in file")
            cols.append(key)
            
        df = df[cols]
        df = df.rename(columns=mapping)
        df.insert(0, "object_id", [object_id for _ in range(0, len(df))])
        # json_str = df.to_json(orient="records")
        # return json.loads(json_str)
        return df
    
    async def inbound_file(self, file_inbound: dict, user_id: str):
        start_time = time.time()
        file = file_inbound.get("file")
        file_extension = file.filename.split(".")[-1]
        if file_extension.lower() == "csv":
            df = pd.read_csv(file.file)
        elif file_extension.lower() == "json":
            default = 'lines'
            file.file.seek(0)
            first_char = await file.read(1)
            file.file.seek(0)
            if first_char == b'[':
                default = 'array'

            if default == 'lines':
                df = pd.read_json(file.file, lines=True)
            else:
                data = json.load(file.file)
                df = pd.DataFrame(data)
        else:
            raise HTTPBadRequest(f"Invalid file type {file_extension}.")

        # map column names to field_ids
        config = file_inbound.get("config")
        print(config, type(config))
        mapping = config.get("map")
        if type(mapping) is str:
            mapping = json.loads(mapping)
        object_id = config.get("object")
        cols = []
        field_ids = []

        for key in mapping:
            if key not in df.columns:
                raise HTTPBadRequest(f"Can not find column ${key} in file")
            cols.append(key)
            field_ids.append(mapping[key])
            
        df = df[cols]
        df = df.rename(columns=mapping)
        df.insert(0, "object_id", [object_id for _ in range(0, len(df))])

        records = []
        field_details = {}
        field_id_details = await self.field_obj_repo.get_all_by_field_types(object_id, [FieldObjectType.ID])
        field_id_detail = field_id_details[0]
        counter = await get_current_record_id(self.db_str, object_id)
        field_id_detail["counter"] = counter
        # count = 0
        
        max_chunk_size = 1000
        chunk_size = min(max_chunk_size, max(1, len(df) // 10))
        df_chunks = [df[i:i+chunk_size] for i in range(0, len(df), chunk_size)]

        tasks = [
            InboundRule.process_file_rows(user_id, df_chunk, field_ids, field_details, field_id_detail, self.record_services)
            for df_chunk in df_chunks
        ]

        records_chunks = await asyncio.gather(*tasks)
        records = [record for records_chunk in records_chunks for record in records_chunk]

        results = await self.record_repo.insert_many(records)
        await update_record_id(self.db_str, object_id, field_id_detail.get("counter").get("seq"))
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Execution time: {execution_time} seconds")
        return results
    
    async def process_file_rows(current_user_id, df, field_ids, field_details, field_id_detail, record_services):
        records = []
        for _, row in df.iterrows():
            # print(f"{field_ids, field_details, field_id_detail}")
            record = await record_services.create_record_from_file(current_user_id, row, field_ids, field_details, field_id_detail)
            if record is not None:
                records.append(record)
        return records
    
    async def inbound_file_with_new_obj(self, user_id: str, config: FileObjectSchema, file: UploadFile = File(...)):
        config_obj = config.model_dump()
        mapping = json.loads(config_obj.pop("map"))
        fields_mapping = json.loads(config_obj.get("fields"))
        config_obj["fields"] = json.loads(fields_mapping)
        obj_with_fields = ObjectWithFieldSchema(**config_obj)
        obj_id = await self.obj_services.create_object_with_fields(obj_with_fields, user_id)
        obj_with_details = await self.obj_services.get_object_detail_by_id(obj_id)
        fields_obj = obj_with_details.get("fields")
        for key in mapping:
            for field_obj in fields_obj:
                if field_obj["field_name"] == mapping.get(key):
                    mapping.update({key: field_obj.get("field_id")})
        obj_repo = ObjectRepository(self.db_str)
        obj = await obj_repo.find_one_by_id(obj_id)
        if not obj:
            raise HTTPBadRequest(f"Not found {obj_id} object by _id")
        
        self.record_repo = RecordObjectRepository(self.db_str, obj.get("obj_id"))
        self.record_services = RecordObjectService(self.db_str, obj.get("obj_id"), obj_id)
        asyncio.create_task(self.inbound_file({"file": file, "config": {"map": mapping, "object": obj_id}}, user_id))