import json
from typing import List, Optional
from pydantic import BaseModel, Field, validator, EmailStr, model_validator
from fastapi import UploadFile, File

class FileSchema(BaseModel):
    object: str = Field(..., alias="object_id")
    map: dict