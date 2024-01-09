from abc import ABC, abstractmethod
from RootAdministrator.models import AdministratorModel, RootModel
from app.common.db_connector import client, RootCollections
from app.common.constants import ROOT_CSA_DB
from typing import Union

class IRootAdministratorRepository(ABC):
    """
        Interface RootAdministratorRepository
    """
    @abstractmethod
    async def insert_root(self):
        raise NotImplementedError
    
    @abstractmethod
    async def insert_admin(self):
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