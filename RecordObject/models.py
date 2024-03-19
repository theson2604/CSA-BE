from typing import List
from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import FieldObjectType
from app.common.utils import get_current_hcm_datetime

class RecordObjectModel(BaseModel, extra='allow'):
    id: str = Field(..., alias="_id")
    object_id: str = Field(..., alias="object_id")
    
    created_at: str = Field(..., alias="created_at", default_factory=get_current_hcm_datetime)
    modified_at: str = Field(..., alias="modified_at", default_factory=get_current_hcm_datetime)
    created_by: str = Field(..., alias="created_by")
    modified_by: str = Field(..., alias="modified_by")
    
    model_config = ConfigDict(
        populate_by_name=True
    )