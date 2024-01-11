from abc import ABC, abstractmethod

from pydantic import EmailStr
from RootAdministrator.models import AdministratorModel, RootModel
from app.common.db_connector import client, RootCollections
from app.common.constants import ROOT_CSA_DB
from typing import List, Union

class IRootAdministratorRepository(ABC):
    """
        Interface RootAdministratorRepository
    """
    @abstractmethod
    async def insert_root(self, root: RootModel):
        raise NotImplementedError
    
    @abstractmethod
    async def insert_admin(self, admin: AdministratorModel):
        raise NotImplementedError
    
    @abstractmethod
    async def find_one_by_email(self, email: EmailStr) -> Union[RootModel, AdministratorModel, None]:
        raise NotImplementedError
    
    @abstractmethod
    async def find_one_by_id(self, id: str) -> Union[RootModel, AdministratorModel, None]:
        raise NotImplementedError
    
    @abstractmethod
    async def find_all(self, query: dict, skip: int = 0, page_size: int = 100) -> List[Union[RootModel, AdministratorModel]]:
        raise NotImplementedError
    
    @abstractmethod
    async def update_one_by_id(self, id: str, record: dict) -> bool:
        raise NotImplementedError
    
    @abstractmethod
    async def count_all(self, query: dict = {}) -> int:
        raise NotImplementedError

class RootAdministratorRepository(IRootAdministratorRepository):
    def __init__(self, db_str: str = ROOT_CSA_DB, coll: str = RootCollections.USERS.value):
        global client
        self.db_str = db_str
        self.db =  client.get_database(db_str)
        self.users_coll = self.db.get_collection(coll)
    
    # Run Only Once
    async def insert_root(self, root: RootModel):
        try:
            await self.users_coll.insert_one(root)
        except Exception as e:
            print(e)
            
    async def insert_admin(self, admin: AdministratorModel):
        await self.users_coll.insert_one(admin)
            
    async def find_one_by_email(self, email: EmailStr, projection: dict = None) -> Union[RootModel, AdministratorModel, None]:
        return await self.users_coll.find_one({"email": email}, projection)
    
    async def find_one_by_id(self, id: str, projection: dict = None) -> Union[RootModel, AdministratorModel, None]:
        return await self.users_coll.find_one({"_id": id}, projection)
            
    async def find_all(self, query: dict, projection: dict = None, skip: int = 1, page_size: int = 100) -> List[Union[RootModel, AdministratorModel]]:
        return await self.users_coll.find(query, projection).skip(skip).limit(page_size).to_list(length=None)
            
    async def update_one_by_id(self, id: str, record: dict) -> bool:
        result = await self.users_coll.update_one({"_id": id}, {"$set": record})
        return result.modified_count > 0

    async def count_all(self, query: dict = {}) -> int:
        return await self.users_coll.count_documents(query)