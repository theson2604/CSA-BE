from typing import List
from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import CustomViewRecordType

class CustomViewRecordModel(BaseModel, extra='allow'):
    id: str = Field(..., alias="_id")
    object_id: str = Field(..., alias="object_id")
    x: float = Field(..., alias="x")
    y: float = Field(..., alias="y")
    w: float = Field(..., alias="w")
    h: float = Field(..., alias="h")
    static: bool = Field(..., alias="static")
    type: CustomViewRecordType = Field(..., alias="type")
    
    model_config = ConfigDict(
        populate_by_name=True
    )
    

class CustomViewRelatedObjectModel(CustomViewRecordModel):
    related_obj_id: str = Field(..., alias="related_obj_id")