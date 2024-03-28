from abc import ABC, abstractmethod
from typing import List
from RootAdministrator.constants import HIDDEN_METADATA_INFO
from app.common.constants import ROOT_CSA_DB
from app.common.db_connector import client, RootCollections
from MailService.models import EmailModel
from app.common.db_connector import DBCollections

class IMailServiceRepository(ABC):
    @abstractmethod
    async def insert_email(self, email: EmailModel):
        raise NotImplementedError
    
class MailServiceRepository(IMailServiceRepository):
    def __init__(self, db_str: str = ROOT_CSA_DB, coll: str = RootCollections.EMAILS.value):
        global client
        self.db_str = db_str
        self.db =  client.get_database(db_str)
        self.emails_coll = self.db.get_collection(coll)
        
    async def insert_email(self, email: EmailModel):
        return await self.emails_coll.insert_one(email)