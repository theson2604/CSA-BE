from typing import List, Optional
from pydantic import BaseModel, Field, validator, EmailStr
from fastapi import UploadFile, File

class FileSchema(BaseModel):
    # file: UploadFile = File(...)
    object: str = Field(..., alias="object_id")
    # map: dict = Field(..., alias="mapping")