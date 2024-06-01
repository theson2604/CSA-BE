from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator

from Action.schemas import ActionSchema
from FieldObject.schemas import FieldObjectSchema
from app.common.enums import ActionWorkflowStatus

class WorkflowSchema(BaseModel):
    name: str = Field(..., max_length=100, min_length=1)
    object_id: str = Field(... ,alias="object_id") # container object
    description: str = Field(..., alias="description")
    status: ActionWorkflowStatus
    trigger: str = Field(..., alias="trigger")
    conditions: Optional[List[Dict[str, Any]]] = None

    @model_validator(mode='after')
    def validate_workflow_schema(self):
        schema = self.model_dump()
        trigger = schema.get("trigger")
        if trigger not in ["create", "update", "manual", "scan"]:
            raise ValueError(f"trigger must be either 'create' or 'update' or 'manual' not '{trigger}'")
        if trigger in ["create", "update"] and not schema.get("conditions") :
            raise ValueError(f"conditions can not be empty with trigger type '{trigger}'")
        
        return self
    
class WorkflowWithActionSchema(WorkflowSchema):
    actions: List[ActionSchema]
    