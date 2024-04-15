

# from InboundRule.models import EmailModel, TemplateModel
# from InboundRule.repository import MailServiceRepository
from InboundRule.schemas import *
from abc import ABC, abstractmethod
from app.common.db_connector import DBCollections
from app.common.errors import HTTPBadRequest
from fastapi import FastAPI, File, UploadFile
from bson import ObjectId
# from Object.repository import ObjectRepository
# from RootAdministrator.repository import RootAdministratorRepository
import csv
import codecs
import json
import pandas as pd 

class IInboundRule(ABC):
    @abstractmethod
    def process_data(data, mapping):
        raise NotImplementedError

    @abstractmethod
    async def inbound_file(self, file: UploadFile = File(...), data: FileSchema = None):
        raise NotImplementedError

class InboundRule(IInboundRule):
    def __init__(self, db):
        # self.repo = MailServiceRepository()
        # self.template_repo = MailServiceRepository(db, DBCollections.EMAIL_TEMPLATE)
        # self.root_repo = RootAdministratorRepository()
        # self.obj_repo = ObjectRepository(db)

        # self.db_str = db
        pass

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
        df.rename(columns=mapping, inplace=True)
        df.insert(0, "object_id", [object_id for _ in range(0, len(df))])
        json_str = df.to_json(orient="records")
        return json.loads(json_str)
    
    async def inbound_file(self, file_inbound: dict):
        file = file_inbound.get("file")
        config = file_inbound.get("config")
        file_extension = file.filename.split(".")[-1]
        if file_extension.lower() == "csv":
            df = pd.read_csv(file.file)
            # csvReader = csv.DictReader(codecs.iterdecode(file.file, 'utf-8'))
            # data = list(csvReader)
        elif file_extension.lower() == "json":
            df = pd.read_json(file.file, lines=True)
        else:
            raise HTTPBadRequest(f"Invalid file type {file_extension}.")
        
        data = InboundRule.process_data(df, config)

        return data[700:]