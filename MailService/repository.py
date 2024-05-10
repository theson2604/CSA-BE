from abc import ABC, abstractmethod
from typing import List
from RootAdministrator.constants import HIDDEN_METADATA_INFO
from app.common.constants import ROOT_CSA_DB
from app.common.db_connector import client, RootCollections
from MailService.models import EmailModel, TemplateModel
# from app.common.db_connector import DBCollections

    
class MailServiceRepository:
    def __init__(self, db_str: str = ROOT_CSA_DB, coll: str = RootCollections.EMAILS.value):
        global client
        try:
            self.db_str = db_str
            self.db =  client.get_database(db_str)
            self.coll = self.db.get_collection(coll)
        except Exception as e:
            print("ERORR IN MONGODb: ", e)
        
    async def insert_email(self, email: EmailModel):
        result = await self.coll.insert_one(email)
        return result.inserted_id
    
    async def find_email(self, query: dict, projection: dict = None):
        return await self.coll.find_one(query, projection)
    
    async def find_email_by_name(self, name: str, projection: dict = None):
        return await self.coll.find_one({"email": name}, projection)
    
    async def insert_template(self, template: TemplateModel, projection: dict = None):
        result = await self.coll.insert_one(template, projection)
        return result.inserted_id
    
    async def find_template_by_id(self, id: str, projection: dict = None):
        return await self.coll.find_one({"_id": id}, projection)
    
    async def get_all_templates(self) -> list:
        pipeline = []
        return await self.coll.aggregate(pipeline).to_list(length=None)
    
    async def get_templates_by_object_id(self, object_id) -> list:
        
        pipeline = [
            {
                "$match": {
                    "object_id": f"{object_id}"
                }
            },
            {
                "$sort": {
                    "modified_at": -1
                }
            }
        ]

        return await self.coll.aggregate(pipeline).to_list(length=None)