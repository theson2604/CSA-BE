from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import ActionType, ActionWorkflowStatus
from app.common.utils import get_current_hcm_datetime

class ActionBase(BaseModel):
    id: str = Field(..., alias="_id")
    workflow_id: str = Field(..., alias="workflow_id")
    type: ActionType = Field(..., alias="type")
    name: str = Field(..., max_length=100, alias="name")
    description: str = Field(..., max_length=500, alias="description")
    status: ActionWorkflowStatus = Field(..., alias="status")
    object_id: str = Field(..., alias="object_id")
    sorting_id: int = Field(..., ge=0)

    # created_at: str = Field(..., alias="created_at", default_factory=get_current_hcm_datetime)
    # modified_at: str = Field(..., alias="modified_at", default_factory=get_current_hcm_datetime)
    # created_by: str = Field(..., alias="created_by")
    # modified_by: str = Field(..., alias="modified_by")
    
    model_config = ConfigDict(
        populate_by_name=True
    )

class ActionSend(ActionBase):
    from_: str = Field(..., alias="from")
    to: List[str] = Field(..., alias="to")
    template_id: str = Field(..., alias="template_id")
    
class ActionScan(ActionBase):
    time: str = Field(..., alias="time")
    template_id: str = Field(..., alias="template_id")
    
class ActionUpdate(ActionBase):
    field_configs: List[Dict[str, Any]]

class ActionCreate(ActionUpdate):
    option: str = Field(..., alias="option")
    field_contents: List[str]
    
class ActionScoreSentiment(ActionBase):
    field_score: str = Field(..., alias="field_score")
    model_id_str: str = Field(..., alias="model_id_str")
    field_update_score: str = Field(..., alias="field_update_score")
    
    
# class ActionUpdate(ActionBase):
#     country_code: str = Field(..., alias="country_code")

# class FieldDate(ActionBase):
#     format: str = Field(..., alias="format")
#     separator: str = Field(..., alilas="separtor")
    
# class FieldReferenceObject(ActionBase):
#     display_value: str = Field(..., alias="display_value")
#     ref_obj_id: str = Field(..., alias="ref_obj_id")
#     ref_obj_id_value: str = Field(..., alias="ref_obj_id_value")
#     cascade_option: str = Field(..., alias="cascade_option")
    
# class FieldReferenceFieldObject(ActionBase):
#     display_value: str = Field(..., alias="display_value")
#     ref_field_obj_id: str = Field(..., alias="ref_field_obj_id")
#     ref_obj_id_value: str = Field(..., alias="ref_obj_id_value")
#     cascade_option: str = Field(..., alias="cascade_option")
