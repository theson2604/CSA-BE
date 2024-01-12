from abc import ABC, abstractmethod

from pydantic import EmailStr
from RootAdministrator.constants import HIDDEN_SYSTEM_USER_INFO
from RootAdministrator.models import AdministratorModel, RootModel, UserModel
from app.common.db_connector import client, RootCollections
from app.common.constants import ROOT_CSA_DB
from typing import List, Union

class IRootAdministratorRepository(ABC):
    @abstractmethod
    async def insert_admin(self, admin: AdministratorModel):
        raise NotImplementedError
    
    @abstractmethod
    async def find_one_by_email(self, email: EmailStr, db_str: str = "", projection: dict = None) -> Union[AdministratorModel, UserModel]:
        raise NotImplementedError
    
    @abstractmethod
    async def find_one_by_id(self, id: str, db_str: str) -> Union[AdministratorModel, UserModel]:
        raise NotImplementedError
    
    @abstractmethod
    async def find_all(self, query: dict, skip: int = 0, page_size: int = 100) -> List[Union[AdministratorModel, UserModel]]:
        raise NotImplementedError
    
    @abstractmethod
    async def find_all_by_email_fullname(self, query: str, db_str: str = "", projection: dict = HIDDEN_SYSTEM_USER_INFO) -> List[dict]:
        raise NotImplementedError
    
    @abstractmethod
    async def update_one_by_id(self, id: str, record: dict) -> bool:
        raise NotImplementedError
    
    @abstractmethod
    async def count_all(self, query: dict = {}) -> int:
        raise NotImplementedError
    
    @abstractmethod
    async def insert_user(self, user: UserModel) -> str:
        raise NotImplementedError

class RootAdministratorRepository(IRootAdministratorRepository):
    def __init__(self, db_str: str = ROOT_CSA_DB, coll: str = RootCollections.USERS.value):
        global client
        self.db_str = db_str
        self.db =  client.get_database(db_str)
        self.users_coll = self.db.get_collection(coll)
            
    async def insert_admin(self, admin: AdministratorModel):
        await self.users_coll.insert_one(admin)
        
    async def insert_user(self, user: UserModel) -> str:
        result = await self.users_coll.insert_one(user)
        return result.inserted_id
            
    async def find_one_by_email(self, email: EmailStr, db_str: str = "", projection: dict = None) -> Union[AdministratorModel, UserModel]:
        if db_str:
            return await self.users_coll.find_one({"email": email, "db": db_str}, projection)
        
        return await self.users_coll.find_one({"email": email}, projection)
    
    async def find_one_by_id(self, id: str, db_str: str, projection: dict = None) -> Union[AdministratorModel, UserModel]:
        return await self.users_coll.find_one({"_id": id, "db": db_str}, projection)
            
    async def find_all(self, query: dict, projection: dict = None, skip: int = 1, page_size: int = 100) -> List[Union[UserModel, AdministratorModel]]:
        return await self.users_coll.find(query, projection).skip(skip).limit(page_size).to_list(length=None)
    
    async def find_all_by_email_fullname(self, query: str, db_str: str = "", projection: dict = HIDDEN_SYSTEM_USER_INFO) -> List[dict]:
        query = {
            "$and": [
                {"$or": [{"email": {"$regex": query}}, {"full_name": {"$regex": query}}]},
                {"db": db_str}
            ]
        } if db_str else {"$or": [{"email": {"$regex": query}}, {"full_name": {"$regex": query}}]}
        
        return await self.users_coll.find(query, projection).to_list(length=None)
        
    async def update_one_by_id(self, id: str, record: dict) -> bool:
        result = await self.users_coll.update_one({"_id": id}, {"$set": record})
        return result.modified_count > 0

    async def count_all(self, query: dict = {}) -> int:
        return await self.users_coll.count_documents(query)
    