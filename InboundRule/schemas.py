from typing import List, Optional
from pydantic import BaseModel, Field, validator, EmailStr
from fastapi import UploadFile

class FileSchema(BaseModel):
    file: UploadFile
    pwd: str = Field(..., alias="pwd")
    admin: str = Field(..., alias="admin_id")
    mail_server: str = ""
    protocol: str = ""