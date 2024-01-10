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

class RootAdministratorRepository(IRootAdministratorRepository):
    def __init__(self, db: Union[str, None] = ROOT_CSA_DB, coll: Union[str, None] = RootCollections.USERS.value):
        global client
        self.db = db
        self.root_db =  client.get_database(db)
        self.users_coll = self.root_db.get_collection(coll)
    
    # Run Only Once
    async def insert_root(self, root: RootModel):
        try:
            await self.users_coll.insert_one(root)
        except Exception as e:
            print(e)
            
    async def insert_admin(self, admin: AdministratorModel):
        try:
            await self.users_coll.insert_one(admin)
        except Exception as e:
            print(e)
    
    async def find_one_by_email(self, email: EmailStr) -> Union[RootModel, AdministratorModel, None]:
        try:
            user = await self.users_coll.find_one({"email": email})
            return user
        except Exception as e:
            print(e)
    
    async def find_one_by_id(self, id: str) -> Union[RootModel, AdministratorModel, None]:
        try:
            user = await self.users_coll.find_one({"_id": id})
            return user
        except Exception as e:
            print(e)
            
    async def find_all(self, query: dict, projection: dict, skip: int = 0, page_size: int = 100) -> List[Union[RootModel, AdministratorModel]]:
        try:
            user = await self.users_coll.find(query, projection).skip(skip).limit(page_size).to_list(length=None)
            return user
        except Exception as e:
            print(e)