from typing import List, Union
from RootAdministrator.models import RootModel, AdministratorModel
from RootAdministrator.schemas import RootSchema, AdminSchema, UpdateAdminSchema
from app.common.enums import SystemUserRole
from app.common.utils import generate_db_company, get_current_hcm_datetime
from .repository import IRootAdministratorRepository, RootAdministratorRepository
from fastapi import Depends
import bcrypt
from app.common.constants import ROOT_CSA_DB
from bson import ObjectId
from abc import ABC, abstractmethod

class IRootAdministratorServices(ABC):
    @abstractmethod
    async def create_system_root(self, root: RootSchema):
        raise NotImplementedError
    
    @abstractmethod
    async def create_system_admin(self, admin: AdminSchema):
        raise NotImplementedError
    
    @abstractmethod
    async def find_system_user_by_id(self, id: str) -> Union[RootModel, AdministratorModel, None]:
        raise NotImplementedError
    
    @abstractmethod
    async def find_all_system_admins(self, page: int = 0, page_size: int = 0) -> List[Union[RootModel, AdministratorModel]]:
        raise NotImplementedError
    
    @abstractmethod
    async def update_admin(self, record: dict) -> bool:
        raise NotImplementedError
    

class RootAdministratorServices:
    def __init__(self, repo: IRootAdministratorRepository = Depends(RootAdministratorRepository)):
        self.repo = repo
    
    # Run Only Once
    async def create_system_root(self, root: RootSchema):
        try:
            root_obj = root.model_dump()
            raw_pwd = root_obj.get("pwd", "")
            # Hashing pwd
            salt = bcrypt.gensalt()
            hashed_pwd = bcrypt.hashpw(raw_pwd.encode('utf-8'), salt).decode("utf-8")
 
            record = RootModel(
                _id = str(ObjectId()),
                email = root_obj.get("email"),
                db = ROOT_CSA_DB,
                system_role = SystemUserRole.ROOT,
                pwd = hashed_pwd
            )
            await self.repo.insert_root(record.model_dump(by_alias=True))
            
        except Exception as e:
            print(e)
            
    async def create_system_admin(self, admin: AdminSchema):
        try:
            admin_obj = admin.model_dump()
            raw_pwd = admin_obj.get("pwd", "")
            company = admin_obj.get("company", "")
            # Hashing pwd
            salt = bcrypt.gensalt()
            hashed_pwd = bcrypt.hashpw(raw_pwd.encode('utf-8'), salt).decode("utf-8")
            db_company_id = generate_db_company(company)
            record = AdministratorModel(
                _id = str(ObjectId()),
                full_name = admin_obj.get("full_name"),
                email = admin_obj.get("email"),
                pwd = hashed_pwd,
                db = db_company_id,
                system_role = SystemUserRole.ADMINISTRATOR,
                company = admin_obj.get("company"),
                domain = admin_obj.get("domain")
            )
            await self.repo.insert_admin(record.model_dump(by_alias=True))
            
        except Exception as e:
            print(e)
            
    async def find_system_user_by_id(self, id: str) -> Union[RootModel, AdministratorModel, None]:
        try:
            return await self.repo.find_one_by_id(id)
        except Exception as e:
            print(e)
            
    async def find_all_system_admins(self, page: int = 1, page_size: int = 100) -> List[Union[RootModel, AdministratorModel]]:
        try:
            skip = (page - 1) * page_size
            projection = {"pwd": 0, "system_role": 0}
            
            return await self.repo.find_all({"system_role": SystemUserRole.ADMINISTRATOR.value}, projection, skip, page_size)
        except Exception as e:
            print(e)
            
    async def update_admin(self, record: UpdateAdminSchema) -> bool:
        record = record.model_dump()
        record.update({"modified_at": get_current_hcm_datetime()})
        if record.get("pwd", None) is None:
            record.pop("pwd")
        return await self.repo.update_one({"_id": record.pop("id")}, record)