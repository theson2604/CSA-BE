from datetime import datetime
import re
from bson import ObjectId
from fastapi import File, UploadFile
import pandas as pd
from FieldObject.repository import FieldObjectRepository
from FieldObject.schemas import FieldObjectSchema
from FieldObject.services import FieldObjectService
from InboundRule.schemas import *
from abc import ABC, abstractmethod
from Object.repository import ObjectRepository
from Object.schemas import ObjectSchema, ObjectWithFieldSchema
from Object.services import ObjectService
from RecordObject.models import RecordObjectModel
from app.common.db_connector import DBCollections
from app.common.enums import FieldObjectType
from app.common.errors import HTTPBadRequest
from app.common.utils import generate_next_record_id, get_current_hcm_datetime, get_current_record_id, update_record_id
from RecordObject.services import RecordException, RecordObjectService
from RecordObject.repository import RecordObjectRepository
import json
import time


class InboundRule:
    def __init__(self, db, obj_id: str = None, obj_id_str: str = None):
        self.field_obj_repo = FieldObjectRepository(db)
        self.obj_repo = ObjectRepository(db)

        if obj_id_str != None:
            self.record_repo = RecordObjectRepository(db, obj_id_str)
            self.record_services = RecordObjectService(db, obj_id_str, obj_id)

        self.obj_services = ObjectService(db)
        self.field_obj_services = FieldObjectService(db)
        self.db_str = db

    def process_data(df, config: dict):
        mapping = json.loads(config.get("map"))
        cols = []

        for key in mapping:
            if key not in df.columns:
                raise HTTPBadRequest(f"Can not find column ${key} in file")
            cols.append(key)
            
        df = df[cols]
        df = df.rename(columns=mapping)
        # json_str = df.to_json(orient="records")
        # return json.loads(json_str)
        return df
    
    async def inbound_file(self, file_inbound: dict, user_id: str) -> Tuple[str, int, int]:
        start_time = time.time()
        json_df = file_inbound.get("file")
        df = pd.read_json(json_df, orient="records")
        
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
        list_details = await self.field_obj_repo.find_many_by_field_ids_str(object_id, list(mapping.values()))

        for index, key in enumerate(mapping):
            if key not in df.columns:
                raise HTTPBadRequest(f"Can not find column ${key} in file")
            cols.append(key)
            field_id = mapping[key]
            field_ids.append(field_id)

            # store all field_details to avoid redundant query
            field_detail = list_details[index]
            field_details[field_id] = field_detail
            field_type = field_detail.get("field_type")
            if field_type == FieldObjectType.REFERENCE_OBJECT:
                ref_obj_id = field_detail.get("ref_obj_id")  # obj_<name>_<id>
                if not ref_obj_records.get(ref_obj_id):
                    ref_record_repo = RecordObjectRepository(self.db_str, ref_obj_id)
                    ref_record_ids = await ref_record_repo.find_all(projection={"_id": 1})
                    ref_obj_records[ref_obj_id] = [id.get("_id") for id in ref_record_ids]
                obj_detail = await self.obj_repo.find_one_by_object_id(ref_obj_id)
                self.ref_record_repo = ref_record_repo
                field_details[field_id]["field_ids"] = await self.field_obj_repo.get_all_by_field_types(obj_detail.get("_id"), [FieldObjectType.ID.value])
            elif field_type == FieldObjectType.REFERENCE_FIELD_OBJECT:
                ref_field_obj_id = field_detail.get(
                    "ref_field_obj_id"
                )
                splitted = ref_field_obj_id.split(".")
                ref_obj_id = splitted[0]
                if not ref_obj_records.get(ref_obj_id):
                    ref_record_repo = RecordObjectRepository(self.db_str, ref_obj_id)
                    ref_record_ids = await ref_record_repo.find_all(projection={"_id": 1})
                    ref_obj_records[ref_obj_id] = [id.get("_id") for id in ref_record_ids]
                
                    
        cols.append("idx")
        df.insert(len(df.axes[1]), "idx", range(0, len(df)))
        init_df = df
        df = df.dropna()
        df = df[cols]
        df = df.rename(columns=mapping)

        records = []
        field_id_details = await self.field_obj_repo.get_all_by_field_types(object_id, [FieldObjectType.ID])
        field_id_detail = field_id_details[0]
        counter = await get_current_record_id(self.db_str, object_id)

        for fd_id in field_ids:
            new_field_value = {}
            field_detail = field_details.get(fd_id)
            fd_type = field_detail.get("field_type") 
            if fd_type == FieldObjectType.TEXT:
                df = df.loc[lambda df_: (df_[fd_id].apply(lambda x: InboundRule.check_text(x, field_detail)))]
            elif fd_type == FieldObjectType.FLOAT:
                df = df.loc[lambda df_: (df_[fd_id].apply(lambda x: InboundRule.check_float(x, field_detail)))]
            elif fd_type == FieldObjectType.INTEGER:
                df = df.loc[lambda df_: (df_[fd_id].apply(lambda x: InboundRule.check_integer(x, field_detail)))]
            elif fd_type == FieldObjectType.EMAIL:
                df = df.loc[lambda df_: (df_[fd_id].apply(lambda x: InboundRule.check_email(x)))]
            elif fd_type == FieldObjectType.PHONE_NUMBER:
                df = df.loc[lambda df_: (df_[fd_id].apply(lambda x: InboundRule.check_phone(x, field_detail)))]
            elif fd_type == FieldObjectType.SELECT:
                df = df.loc[lambda df_: (df_[fd_id].apply(lambda x: InboundRule.check_select(x, field_detail)))]
            elif fd_type == FieldObjectType.DATE:
                df = df.loc[lambda df_: (df_[fd_id].apply(lambda x: InboundRule.check_date(x, field_detail)))]
            elif fd_type == FieldObjectType.REFERENCE_OBJECT:
                ref_obj_id = field_detail.get("ref_obj_id")
                df = df.loc[lambda df_: (df_[fd_id].apply(lambda x: InboundRule.check_ref_obj(x, field_detail, ref_obj_records.get(ref_obj_id), new_field_value)))]
                df.replace({fd_id: new_field_value}, inplace=True)
            elif fd_type == FieldObjectType.REFERENCE_FIELD_OBJECT:
                df = df.loc[lambda df_: (df_[fd_id].apply(lambda x: InboundRule.check_ref_field(x, field_detail, ref_obj_records, new_field_value)))]
                df.replace({fd_id: new_field_value}, inplace=True)
        
        # avoid inserting empty record to db
        if len(df) == 0:
            return object_id, 0, len(init_df)
        
        inserted_idx = df["idx"]
        removed_df = init_df.loc[lambda df_: (~df_["idx"].isin(inserted_idx))]
        # removed_idx = list(removed_df["idx"]) ##### to get the idx of the removed records
        df.drop(["idx"], axis=1, inplace=True)

        field_id, prefix = field_id_detail.get("field_id"), field_id_detail.get("prefix")
        seq = counter.get("seq") + 1
        prefix_ids = [f"{prefix}{i}" for i in range(seq, seq+len(df))]
        _ids = [str(ObjectId()) for _ in range(len(df))]
        current_time = get_current_hcm_datetime()
        df.insert(0, "object_id", object_id)
        df.insert(0, "_id", _ids)
        df.insert(len(df.axes[1]), field_id, prefix_ids)
        df.insert(len(df.axes[1]), "created_at", current_time)
        df.insert(len(df.axes[1]), "modified_at", current_time)
        df.insert(len(df.axes[1]), "created_by", user_id)
        df.insert(len(df.axes[1]), "modified_by", user_id)

        dict_records = df.to_dict(orient="records")
        records = [RecordObjectModel.model_validate(record).model_dump(by_alias=True) for record in dict_records]

        results = []
        batch_size = 10000
        if len(records) > batch_size:
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                results = results + (await self.record_repo.insert_many(batch) if len(batch) > 1 else [await self.record_repo.insert_one(batch[0])])
        else:
            results = await self.record_repo.insert_many(records) if len(records) > 1 else await self.record_repo.insert_one(records[0])
        await update_record_id(self.db_str, object_id, seq+len(results)-1)
        end_time = time.time()
        execution_time = end_time - start_time
        # print(f"Execution time: {execution_time} seconds")
        return config.get("object"), len(results), len(removed_df)
    
    def check_text(field_value, field_detail):
        length = field_detail.get("length")
        if not isinstance(field_value, str):
            return False
        if len(field_value) > length:
            return False
        return True
    
    def check_float(field_value, field_detail):
        if not isinstance(field_value, int) and not isinstance(field_value, float):
            return False
        return True
    
    def check_integer(field_value, field_detail):
        if not isinstance(field_value, int):
            return False
        return True
    
    def check_email(field_value):
        email_regex = (
            r"^[a-zA-Z0-9]+(?:\.[a-zA-Z0-9]+)*@[a-zA-Z0-9]+(?:\.[a-zA-Z0-9]+)*$"
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
    
    def check_date(field_value, field_detail):
        format = field_detail.get("format")
        separator = field_detail.get("separator")
        # print(field_value)
        if separator not in field_value:
            return False

        date_regex = {
            "DD MM YYYY": r"^\d{2} \d{2} \d{4}$",
            "MM DD YYYY": r"^\d{2} \d{2} \d{4}$",
            "YYYY MM DD": r"^\d{4} \d{2} \d{2}$"
        }
        if not re.match(date_regex.get(format).replace(" ", separator), field_value):
            raise RecordException(
                f"date {field_value} format is not valid."
            )

        try:
            if format == "DD MM YYYY":
                bool(datetime.strptime(field_value, f"%d{separator}%m{separator}%Y"))
            elif format == "MM DD YYYY":
                bool(datetime.strptime(field_value, f"%m{separator}%d{separator}%Y"))
            else:
                bool(datetime.strptime(field_value, f"%Y{separator}%m{separator}%d"))
        except ValueError:
            return False
        return True
    
    def check_ref_obj(field_value, field_detail, ref_obj_records, new_field_value):
        if field_value not in ref_obj_records:
            return False

        field_ids = field_detail.get("field_ids")
        if field_ids and len(field_ids) == 1:
            new_field_value[field_value] = {"ref_to": field_value, "field_value": field_ids[0].get("field_id")}
        return True
    
    def check_ref_field(field_value, field_detail, ref_obj_records, new_field_value):
        ref_field_obj_id = field_detail.get("ref_field_obj_id")  # obj_<name>_<id>.fd_<name>_<id>
        splitted = ref_field_obj_id.split(".")
        ref_obj_id, ref_fld_id = splitted[0], splitted[1]
        if field_value not in ref_obj_records.get(ref_obj_id):
            return False

        new_field_value[field_value] = {"ref_to": field_value, "field_value": ref_fld_id}
        return True
    
    async def inbound_file_with_new_obj(self, current_user_id: str, config: FileObjectSchema, df: str):
        mapping = json.loads(config.pop("map"))
        # mapping = json.loads(mapping)
        fields_mapping = json.loads(config.get("fields"))
        config["fields"] = json.loads(json.dumps(fields_mapping))
        obj_only = {"obj_name": config.get("obj_name"), "group_obj_id": config.get("group_obj_id")}
        new_obj_id = await self.obj_services.create_object_only(ObjectSchema(**obj_only), current_user_id)
        # obj_with_fields = ObjectWithFieldSchema(**config)
        # obj_id = await self.obj_services.create_object_with_fields(obj_with_fields, user_id)
        await self.field_obj_services.create_many_fields_object(new_obj_id, [FieldObjectSchema(**field) for field in config.get("fields")])
        obj_with_details = await self.obj_services.get_object_detail_by_id(new_obj_id)
        fields_obj = obj_with_details.get("fields")
        for key in mapping:
            for field_obj in fields_obj:
                if field_obj["field_name"] == mapping.get(key):
                    mapping.update({key: field_obj.get("field_id")})
        
        obj_repo = ObjectRepository(self.db_str)
        obj = await obj_repo.find_one_by_id(new_obj_id)
        if not obj:
            raise HTTPBadRequest(f"Not found {new_obj_id} object by _id")
        
        self.record_repo = RecordObjectRepository(self.db_str, obj.get("obj_id"))
        self.record_services = RecordObjectService(self.db_str, obj.get("obj_id"), new_obj_id)
        return await self.inbound_file({"file": df, "config": {"map": mapping, "object": new_obj_id}}, current_user_id)