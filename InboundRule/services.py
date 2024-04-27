import re
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
from RecordObject.services import RecordException, RecordObjectService
from RecordObject.repository import RecordObjectRepository
from functools import reduce
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
        mapping = config.get("map")
        if type(mapping) is str:
            mapping = json.loads(mapping)
        object_id = config.get("object")
        cols = []
        field_ids = []
        field_details = {}
        ref_obj_records = {}

        for key in mapping:
            if key not in df.columns:
                raise HTTPBadRequest(f"Can not find column ${key} in file")
            cols.append(key)
            field_id = mapping[key]
            field_ids.append(field_id)
            # store all field_details to avoid redundant query
            if not field_details.get(field_id):
                field_detail = await self.field_obj_repo.find_one_by_field_id(
                                    object_id, field_id
                                )
                field_details[field_id] = field_detail
                field_type = field_detail.get("field_type")
                if field_type == FieldObjectType.REFERENCE_OBJECT:
                    ref_obj_id = field_detail.get("ref_obj_id")  # obj_<name>_<id>
                    if not ref_obj_records.get(ref_obj_id):
                        ref_record_repo = RecordObjectRepository(self.db_str, ref_obj_id)
                        ref_record_ids = await ref_record_repo.find_all(projection={"_id": 1})
                        ref_obj_records[ref_obj_id] = [id.get("_id") for id in ref_record_ids]
                        print(ref_obj_records[ref_obj_id][:5])
                    obj_detail = await self.obj_repo.find_one_by_object_id(ref_obj_id)
                    self.ref_record_repo = ref_record_repo
                    field_details[field_id]["field_ids"] = await self.field_obj_repo.get_all_by_field_types(obj_detail.get("_id"), [FieldObjectType.ID.value])
                    

        df = df[cols]
        df = df.rename(columns=mapping)
        df.insert(0, "object_id", [object_id for _ in range(0, len(df))])

        records = []
        field_id_details = await self.field_obj_repo.get_all_by_field_types(object_id, [FieldObjectType.ID])
        field_id_detail = field_id_details[0]
        # counter = await get_current_record_id(self.db_str, object_id)
        # field_id_detail["counter"] = counter
        # count = 0
        
        # max_chunk_size = 1000
        # chunk_size = min(max_chunk_size, max(1, len(df) // 10))
        # df_chunks = [df[i:i+chunk_size] for i in range(0, len(df), chunk_size)]

        # tasks = [
        #     self.process_file_rows(user_id, df_chunk, field_ids, field_details, field_id_detail)
        #     for df_chunk in df_chunks
        # ]

        # records_chunks = await asyncio.gather(*tasks)
        # records = [record for records_chunk in records_chunks for record in records_chunk]

        new_field_value = {}
        for fd_id in field_ids:
            field_detail = field_details.get(fd_id)
            fd_type = field_detail.get("field_type") 
            if fd_type in [FieldObjectType.TEXT]:
                df = df.loc[lambda df_: (df_[fd_id].apply(lambda x: InboundRule.check_text(x, field_detail)))]
            elif fd_type == FieldObjectType.EMAIL:
                df = df.loc[lambda df_: (df_[fd_id].apply(lambda x: InboundRule.check_email(x)))]
            elif fd_type == FieldObjectType.PHONE_NUMBER:
                df = df.loc[lambda df_: (df_[fd_id].apply(lambda x: InboundRule.check_phone(x, field_detail)))]
            elif fd_type == FieldObjectType.SELECT:
                df = df.loc[lambda df_: (df_[fd_id].apply(lambda x: InboundRule.check_select(x, field_detail)))]
            elif fd_type == FieldObjectType.REFERENCE_OBJECT:
                ref_obj_id = field_detail.get("ref_obj_id")
                df = df.loc[lambda df_: (df_[fd_id].apply(lambda x: InboundRule.check_ref_obj(x, field_detail, ref_obj_records.get(ref_obj_id), new_field_value)))]
                # elif fd_type == FieldObjectType.REFERENCE_FIELD_OBJECT:
                
                
            # df_records = df.loc[lambda df_: reduce(lambda x,y: (nest_asyncio.apply((self.process_field(df_[y], field_details, y, object_id))) & x), 
            #                                        field_ids, True)]
        print(len(df))
        # raise HTTPBadRequest("STOP")

        # results = await self.record_repo.insert_many(records)
        # await update_record_id(self.db_str, object_id, field_id_detail.get("counter").get("seq"))
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Execution time: {execution_time} seconds")
        return len(records)
    
    def check_text(field_value, field_detail):
        length = field_detail.get("length")
        if not isinstance(field_value, str):
            return False
        if len(field_value) > length:
            return False
        return True
    
    def check_email(field_value):
        email_regex = (
            "^[a-zA-Z0-9]+(?:\.[a-zA-Z0-9]+)*@[a-zA-Z0-9]+(?:\.[a-zA-Z0-9]+)*$"
        )
        match = re.search(email_regex, field_value)
        if not match:
            return False
        return True
    
    def check_phone(field_value, field_detail):
        country_code = field_detail.get("country_code")
        if country_code == "+84":
            vn_phone_regex = "^(0|84)(2(0[3-9]|1[0-6|8|9]|2[0-2|5-9]|3[2-9]|4[0-9]|5[1|2|4-9]|6[0-3|9]|7[0-7]|8[0-9]|9[0-4|6|7|9])|3[2-9]|5[5|6|8|9]|7[0|6-9]|8[0-6|8|9]|9[0-4|6-9])([0-9]{7})$"
            match = re.search(vn_phone_regex, field_value)
            if not match:
                return False
        return True
    
    def check_select(field_value, field_detail):
        options = field_detail.get("options")
        if field_value not in options:
            return False
        return True
    
    def check_ref_obj(field_value, field_detail, ref_obj_records, new_field_value):
        if field_value not in ref_obj_records:
            return False

        field_ids = field_detail.get("field_ids")
        print("FIELD_IDS: ", field_ids)
        print(field_value)
        
        if field_ids and len(field_ids) == 1:
            new_field_value[field_value] = {"ref_to": field_value, "field_value": field_ids[0].get("field_id")}
            print("AAAA", new_field_value[field_value])

        return True
    
    # def check_ref_field(field_value, field_detail):
    #     ref_field_obj_id = field_detail.get("ref_field_obj_id")  # obj_<name>_<id>.fd_<name>_<id>
    #     splitted = ref_field_obj_id.split(".")
    #     ref_obj_id, ref_fld_id = splitted[0], splitted[1]
    #     # obj_id's record repo
    #     ref_record_repo = RecordObjectRepository(self.db_str, ref_obj_id)
    #     ref_record = await ref_record_repo.find_one_by_id(field_value)
    #     if not ref_record:
    #         raise RecordException(
    #             f"Not found ref record '{field_value} in {ref_obj_id}"
    #         )

    #     field_value = {
    #         "ref_to": ref_record.get("_id"),
    #         "field_value": ref_fld_id,
    #     }
    
    # async def process_file_rows(self, current_user_id, df, field_ids, field_details, field_id_detail):
    #     records = []
    #     # for _, row in df.iterrows():
    #     #     record = await record_services.create_record_from_file(current_user_id, row, field_ids, field_details, field_id_detail)
    #     #     if record is not None:
    #     #         records.append(record)
    #     object_id =""
        
    #     # df_records = df.loc[lambda df_: reduce(lambda x,y: (await self.record_services.check_field_value(df_[x], field_details, x, object_id, self.ref_record_repo)) & y, field_details, True)]
    #     try:
    #         df_records = df.loc[lambda df_: reduce(lambda x,y: (asyncio.run(self.process_field(df_[y], field_details, y, object_id)) & x), 
    #                                                list(field_details.keys()), True)]
    #     except Exception as e:
    #         raise HTTPBadRequest(f"NOT TRUE {e}")
    #     print(len(df_records))
    #     raise HTTPBadRequest("STOP")
    
    # async def process_field(self, df_column, field_details, field_id, object_id):
    #     return await self.record_services.check_field_value(df_column, field_details, field_id, "123")
    
    async def inbound_file_with_new_obj(self, user_id: str, config: FileObjectSchema, file: UploadFile = File(...)):
        config_obj = config.model_dump()
        mapping = json.loads(config_obj.pop("map"))
        parse_dict_mapping = json.loads(mapping)
        fields_mapping = json.loads(config_obj.get("fields"))
        config_obj["fields"] = json.loads(fields_mapping)
        obj_with_fields = ObjectWithFieldSchema(**config_obj)
        obj_id = await self.obj_services.create_object_with_fields(obj_with_fields, user_id)
        obj_with_details = await self.obj_services.get_object_detail_by_id(obj_id)
        fields_obj = obj_with_details.get("fields")
        for key in parse_dict_mapping:
            for field_obj in fields_obj:
                if field_obj["field_name"] == parse_dict_mapping.get(key):
                    parse_dict_mapping.update({key: field_obj.get("field_id")})
        
        obj_repo = ObjectRepository(self.db_str)
        obj = await obj_repo.find_one_by_id(obj_id)
        if not obj:
            raise HTTPBadRequest(f"Not found {obj_id} object by _id")
        
        self.record_repo = RecordObjectRepository(self.db_str, obj.get("obj_id"))
        self.record_services = RecordObjectService(self.db_str, obj.get("obj_id"), obj_id)
        return await self.inbound_file({"file": file, "config": {"map": parse_dict_mapping, "object": obj_id}}, user_id)
        # asyncio.create_task(self.inbound_file({"file": file, "config": {"map": parse_dict_mapping, "object": obj_id}}, user_id))