from RootAdministrator.models import RootModel, AdministratorModel
from RootAdministrator.schemas import RootSchema, AdminSchema
from app.common.enums import SystemUserRole
from app.common.utils import generate_db_company
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