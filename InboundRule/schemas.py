import json
from typing import List, Tuple
from pydantic import BaseModel, Field, validator, EmailStr, model_validator
from fastapi import UploadFile, File, Form


class FileSchema(BaseModel):
    object: str = Field(..., alias="object_id")
    map: str = Field(..., alias="mapping")