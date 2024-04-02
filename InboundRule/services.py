from InboundRule.models import EmailModel, TemplateModel
from InboundRule.repository import MailServiceRepository
from InboundRule.schemas import *
from abc import ABC, abstractmethod
from app.common.db_connector import DBCollections
from app.common.errors import HTTPBadRequest
from fastapi import FastAPI, File, UploadFile
from bson import ObjectId
from Object.repository import ObjectRepository
from RootAdministrator.repository import RootAdministratorRepository
import csv
import codecs

class IInboundRule(ABC):
    @abstractmethod
    async def process_file(self, file: UploadFile = File(...)):
        raise NotImplementedError

class InboundRule(IInboundRule):
    def __init__(self, db):
        # self.repo = MailServiceRepository()
        # self.template_repo = MailServiceRepository(db, DBCollections.EMAIL_TEMPLATE)
        # self.root_repo = RootAdministratorRepository()
        # self.obj_repo = ObjectRepository(db)

        # self.db_str = db
        pass

    async def process_file(self, file: UploadFile = File(...)):
        # filtered_data = (line.replace(b'\x00', b'\xff') for line in file.file)
        csvReader = csv.DictReader(codecs.iterdecode(file.file, 'latin-1'))
        # background_tasks.add_task(file.file.close)
        return list(csvReader)