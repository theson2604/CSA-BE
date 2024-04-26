from typing import List, Tuple
from pydantic import BaseModel, ConfigDict, Field
# from fastapi import UploadFile, File, Form
# from Object.schemas import ObjectWithFieldSchema

class FileObjectSchema(BaseModel):
    obj_name: str = Field(..., max_length=100, min_length=1)
    group_obj_id: str = Field(..., alias="group_id")
    fields: str = Field(..., alias="fields")
    map: str = Field(..., alias="mapping")