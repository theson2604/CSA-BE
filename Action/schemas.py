import re
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field, model_validator  

from app.common.enums import ActionType 

class ActionSchema(BaseModel):
    name: str
    type: ActionType
    description: str
    object_id: str # target record to apply action to

    workflow_id: Optional[str] = None # container workflow, no need to consider container object
    sorting_id: Optional[int] = None
    
    # Send
    to: Optional[List[str]] = None
    
    # Scan
    time: Optional[str] = None

    # Send/Scan
    from_: Optional[str] = None
    template_id: Optional[str] = None
    
    # Create/Update
    option: Optional[str] = None # True if use scan else False
    field_contents: Optional[List[str]] = None
    field_configs: Optional[List[Dict[str, Any]]] = None

    @model_validator(mode='after')
    def validate_field_obj_schema(self):
        schema = self.model_dump()
        type = schema.get("type")
        if type in [ActionType.SEND, ActionType.SCAN]:
            if not schema.get("template_id"):
                raise ValueError(f"missing required 'template_id' for type {type}.")
            if type == ActionType.SEND:
                if not schema.get("from_"):
                    raise ValueError(f"missing required 'from_' for type {ActionType.SEND}.")
                if not schema.get("to"):
                    raise ValueError(f"missing required 'to' for type {ActionType.SEND}.")
            else:
                if not schema.get("time"):
                    raise ValueError(f"missing required 'time' for type {ActionType.SCAN}.")
            
        elif type in [ActionType.CREATE, ActionType.UPDATE]:
            option = schema.get("option")
            if not option:
                raise ValueError(f"missing required 'option' for type {type}.")
            
            if option not in ["yes", "no"]:
                raise ValueError(f"invalid option {option}")
            
            field_configs = schema.get("field_configs")
            if not field_configs:
                raise ValueError(f"missing required 'field_configs' for type {type}.")
            if len(field_configs) == 0:
                raise ValueError(f"'field_configs' can not be empty.")
            
        else:
            raise ValueError(f"invalid 'type' {type}.")
                    
        return self
    
class UpdateActionSchema(ActionSchema):
    id: str = Field(..., alias="_id")
    object_id: str
    sorting_id: int