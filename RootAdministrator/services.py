from typing import List, Union
from RootAdministrator.models import RootModel, AdministratorModel, UserModel
from RootAdministrator.schemas import RootSchema, AdminSchema, UpdateAdminSchema, UserSchema, UpdateUserSchema
from app.common.db_connector import RootCollections
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
    async def create_system_admin(self, admin: AdminSchema) -> bool:
        raise NotImplementedError
    
    @abstractmethod
    async def find_all_system_admins(self, page: int = 0, page_size: int = 0) -> List[Union[RootModel, AdministratorModel]]:
        raise NotImplementedError
    
    @abstractmethod
    async def update_admin(self, record: dict) -> bool:
        raise NotImplementedError
    
    @abstractmethod
    async def count_all_admin(self) -> int:
        raise NotImplementedError
    
    @abstractmethod
    async def create_system_user(self, user: UserSchema, db: str) -> str:
        raise NotImplementedError
    
    @abstractmethod
    async def find_all_company_users(self, db: str, page: int = 0, page_size: int = 0) -> List[Union[RootModel, UserModel]]:
        raise NotImplementedError
    
    @abstractmethod
    async def update_user(self, record: UpdateUserSchema) -> bool:
        raise NotImplementedError
    
    @abstractmethod
    async def count_all_company_user(self, db: str) -> int:
        raise NotImplementedError
    
    @abstractmethod
    async def search_company_users_by_email_fullname(self, db: str, query: str) -> List[dict]:
        raise NotImplementedError

class RootAdministratorServices(IRootAdministratorServices):
    def __init__(self, repo: IRootAdministratorRepository = Depends(lambda: RootAdministratorRepository(ROOT_CSA_DB, RootCollections.USERS.value))):
        self.repo = repo
            
    async def create_system_admin(self, admin: AdminSchema) -> bool:
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
        return True
    
    async def find_all_system_admins(self, page: int = 1, page_size: int = 100) -> List[Union[RootModel, AdministratorModel]]: # type: ignore
        skip = (page - 1) * page_size
        projection = {"pwd": 0, "system_role": 0}
        
        return await self.repo.find_all({"system_role": SystemUserRole.ADMINISTRATOR.value}, projection, skip, page_size)
    
    async def update_admin(self, record: UpdateAdminSchema) -> bool:
        record = record.model_dump()
        record.update({"modified_at": get_current_hcm_datetime()})
        raw_pwd = record.get("pwd", None)
        if raw_pwd is None:
            record.pop("pwd")
        else:
            salt = bcrypt.gensalt()
            hashed_pwd = bcrypt.hashpw(raw_pwd.encode('utf-8'), salt).decode("utf-8")
            record.update({"pwd": hashed_pwd})
            
        return await self.repo.update_one_by_id(record.pop("id"), record)

    async def count_all_admin(self) -> int:
        return await self.repo.count_all({"system_role": SystemUserRole.ADMINISTRATOR})

    async def create_system_user(self, user: UserSchema, db: str) -> str:
        user_obj = user.model_dump()
        raw_pwd = user_obj.get("pwd", "")
        # Hashing pwd
        salt = bcrypt.gensalt()
        hashed_pwd = bcrypt.hashpw(raw_pwd.encode('utf-8'), salt).decode("utf-8")

        record = UserModel(
            _id = str(ObjectId()),
            full_name = user_obj.get("full_name"),
            email = user_obj.get("email"),
            db = db,
            system_role = SystemUserRole.USER,
            pwd = hashed_pwd,
            is_manager = False
        )
        return await self.repo.insert_user(record.model_dump(by_alias=True))

    async def find_all_company_users(self, db: str, page: int = 1, page_size: int = 100) -> List[Union[RootModel, UserModel]]: # type: ignore
        skip = (page - 1) * page_size
        projection = {"pwd": 0, "system_role": 0}
        
        return await self.repo.find_all({"db": db, "system_role": SystemUserRole.USER.value}, projection, skip, page_size)

    async def update_user(self, record: UpdateUserSchema) -> bool:
        record = record.model_dump()
        record.update({"modified_at": get_current_hcm_datetime()})
        raw_pwd = record.get("pwd", None)
        if raw_pwd is None:
            record.pop("pwd")
        else:
            salt = bcrypt.gensalt()
            hashed_pwd = bcrypt.hashpw(raw_pwd.encode('utf-8'), salt).decode("utf-8")
            record.update({"pwd": hashed_pwd})
        return await self.repo.update_one_by_id(record.pop("id"), record)

    async def count_all_company_user(self, db: str) -> int:
        return await self.repo.count_all({"db": db, "system_role": SystemUserRole.USER})
    
    async def search_company_users_by_email_fullname(self, db: str, query: str) -> List[dict]:
        return await self.repo.find_all_by_email_fullname(query, SystemUserRole.USER, db)
 