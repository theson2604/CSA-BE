from typing import Union
import bcrypt
from fastapi import Depends
from pydantic import EmailStr
from RootAdministrator.repository import IRootAdministratorRepository, RootAdministratorRepository
from abc import ABC, abstractmethod
import jwt
from app.settings.config import SECRET_SALT, JWT_ALGORITHM

class IAuthenticationServices(ABC):
    @abstractmethod
    def encode_jwt(self, obj: dict) -> str:
        raise NotImplementedError
    
    @abstractmethod
    def decode_jwt(self, jwt: str) -> dict:
        raise NotImplementedError
    
    @abstractmethod
    def is_valid_password(self, raw_pwd: str, hashed_pwd: str) -> bool:
        raise NotImplementedError
    
    @abstractmethod
    async def validate_user(self, email: EmailStr, pwd: str) -> Union[str, None]:
        raise NotImplementedError
    
    @abstractmethod
    async def get_user_by_token(self, access_token: str):
        raise NotImplementedError

class AuthenticationServices:
    def __init__(self, repo: IRootAdministratorRepository = Depends(RootAdministratorRepository)):
        self.repo = repo
    
    def encode_jwt(self, obj: dict) -> str:
        return jwt.encode(obj, SECRET_SALT, algorithm=JWT_ALGORITHM)
       
    def decode_jwt(self, encoded_jwt: str) -> dict:
        return jwt.decode(encoded_jwt, SECRET_SALT, algorithms=[JWT_ALGORITHM])
    
    def is_valid_password(self, raw_pwd: str, hashed_pwd: str) -> bool:
        encoded_raw_pwd, encoded_hashed_pwd = raw_pwd.encode("utf-8"), hashed_pwd.encode("utf-8")
        return bcrypt.checkpw(encoded_raw_pwd, encoded_hashed_pwd)
    
    async def validate_user(self, email: EmailStr, pwd: str) -> Union[str, None]:
        user = await self.repo.find_one_by_email(email)
        if self.is_valid_password(pwd, user.get("pwd")):
            user.pop("pwd")
            user.pop("created_at")
            user.pop("modified_at")
            return self.encode_jwt(user)
            
        return None
        
    async def get_user_by_token(self, access_token: str):
        payload = self.decode_jwt(access_token)
        user_id = payload.get("_id")
        user = await self.repo.find_one_by_id(user_id)
        return user