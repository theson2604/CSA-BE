import re
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field, model_validator  

from app.common.enums import ActionType, ActionWorkflowStatus

class ActionSchema(BaseModel):
    name: str
    type: ActionType
    description: str
    status: ActionWorkflowStatus
    object_id: str # target record to apply action to
    
    workflow_id: Optional[str] = None # container workflow, no need to consider container object
    sorting_id: Optional[int] = None
    
    # Scoring Sentiment
    field_score: Optional[str] = None
    model_id_str: Optional[str] = None
    field_update_score: Optional[str] = None
    
    # Send
    to: Optional[List[str]] = None
    
    # Scan
    time: Optional[str] = None

    # Send/Scan
    from_: Optional[str] = None
    template_id: Optional[str] = None
    
    # Create/Update
    field_configs: Optional[List[Dict[str, Any]]] = []

    # Create
    option: Optional[str] = None # True if use scan else False
    field_contents: Optional[List[str]] = []

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
            field_configs, field_contents = schema.get("field_configs"), schema.get("field_contents")
            # if not field_configs and not field_contents:
            #     raise ValueError(f"missing both required 'field_configs' and 'field_contents' for type {type}.")
            
            if len(field_configs) == 0 and len(field_contents) == 0:
                raise ValueError(f"'field_configs' and 'field_contents' can not be both empty.")

            
            if type == ActionType.CREATE:
                option = schema.get("option")
                if not option:
                    raise ValueError(f"missing required 'option' for type {type}.")
                
                if option not in ["yes", "no"]:
                    raise ValueError(f"invalid option {option}")
        
        elif type == ActionType.SENTIMENT:
            field_score = schema.get("field_score")
            model_id_str = schema.get("model_id_str")
            field_update_score = schema.get("field_update_score")
            
            if not field_score:
                raise ValueError(f"missing required 'field_score' for type {type}.")
            
            if not field_update_score:
                raise ValueError(f"missing required 'field_update_score' for type {type}.")
            
            regex_str = r"^fd_\w+_\d{6}$"
            match = re.search(regex_str, field_score)
            if not match:
                raise ValueError(f"invalid 'field_score' {field_score}. It must be {regex_str}")
            
            regex_str = r"^fd_\w+_\d{6}$"
            match = re.search(regex_str, field_update_score)
            if not match:
                raise ValueError(f"invalid 'field_update_score' {field_update_score}. It must be {regex_str}")
            
            regex_str = r"^model_\w+_\d{6}$"
            match = re.search(regex_str, model_id_str)
            if not match:
                raise ValueError(f"invalid 'model_id_str' {model_id_str}. It must be {regex_str}")
            
        else:
            raise ValueError(f"invalid 'type' {type}.")
                    
        return self
    
class UpdateActionSchema(ActionSchema):
    action_id: str
    workflow_id: str
    object_id: str
    sorting_id: str
