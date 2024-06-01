from typing import Any, Dict, List
from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import ActionWorkflowStatus
from app.common.utils import get_current_hcm_datetime

class WorkflowModel(BaseModel):
    id: str = Field(..., alias="_id")
    object_id: str = Field(..., alias="object_id")
    name: str = Field(..., alias="name", max_length=100)
    description: str = Field(..., alias="description", max_length=200)
    status: ActionWorkflowStatus = Field(..., alias="status")
    trigger: str = Field(..., alias="trigger")
    conditions: List[Dict[str, Any]] = Field(..., alias="conditions")

    created_at: str = Field(..., alias="created_at", default_factory=get_current_hcm_datetime)
    modified_at: str = Field(..., alias="modified_at", default_factory=get_current_hcm_datetime)
    created_by: str = Field(..., alias="created_by")
    modified_by: str = Field(..., alias="modified_by")
    
    model_config = ConfigDict(
        populate_by_name=True
    )