from typing import List
from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import DashboardType

class DashboardModel(BaseModel, extra='allow'):
    id: str = Field(..., alias="_id")
    x: float = Field(..., alias="x")
    y: float = Field(..., alias="y")
    w: float = Field(..., alias="w")
    h: float = Field(..., alias="h")
    static: bool = Field(..., alias="static")
    type: DashboardType = Field(..., alias="type")
    object_id: str = Field(..., alias="object_id")
    obj_id: str = Field(..., alias="obj_id")
    field_id: str = Field(..., alias="field_id_str")
    
    model_config = ConfigDict(
        populate_by_name=True
    )