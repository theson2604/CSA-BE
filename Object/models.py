from pydantic import BaseModel, ConfigDict, Field

from app.common.utils import get_current_hcm_datetime

class ObjectModel(BaseModel):
    id: str = Field(..., alias="_id")
    obj_name: str = Field(..., alias="obj_name", max_length=100)
    obj_id: str = Field(..., alias="obj_id")
    group_obj_id: str = Field(..., alias="group_obj_id")
    sorting_id: int = Field(..., alias="sorting_id", ge=0)
    
    created_at: str = Field(..., alias="created_at", default_factory=get_current_hcm_datetime)
    modified_at: str = Field(..., alias="modified_at", default_factory=get_current_hcm_datetime)
    created_by: str = Field(..., alias="created_by")
    modified_by: str = Field(..., alias="modified_by")
    
    model_config = ConfigDict(
        populate_by_name=True
    )