from typing import List
from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import FieldObjectType
from app.common.utils import get_current_hcm_datetime

class RecordObjectModel(BaseModel, extra='allow'):
    id: str = Field(..., alias="_id")
    object_id: str = Field(..., alias="object_id")
    
    model_config = ConfigDict(
        populate_by_name=True
    )