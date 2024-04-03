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

class IInboundRule(ABC):
    @abstractmethod
    async def process_file(self, file: UploadFile = File(...), data: FileSchema = None):
        raise NotImplementedError

class InboundRule(IInboundRule):
    def __init__(self, db):
        # self.repo = MailServiceRepository()
        # self.template_repo = MailServiceRepository(db, DBCollections.EMAIL_TEMPLATE)
        # self.root_repo = RootAdministratorRepository()
        # self.obj_repo = ObjectRepository(db)

        # self.db_str = db
        pass

    async def process_file(self, file_obj: dict):
        file = file_obj.get("file")
        # config
        file_extension = file.filename.split(".")[-1]
        if file_extension.lower() == "csv":
            csvReader = csv.DictReader(codecs.iterdecode(file.file, 'utf-8'))
            # background_tasks.add_task(file.file.close)
            data = list(csvReader)
        elif file_extension.lower() == "json":
            data = json.load(file.file)
        else:
            raise HTTPBadRequest(f"Invalid file type {file_extension}.")
        
        # for 
        print(type(data))
        return data