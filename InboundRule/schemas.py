from typing import List, Optional
from pydantic import BaseModel, Field, validator, EmailStr
from fastapi import UploadFile, File

class FileSchema(BaseModel):
    object: str = Field(..., alias="object_id")
    map: dict = Field(..., alias="mapping")