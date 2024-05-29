from typing import List
from pydantic import BaseModel, model_validator
import re

class DatasetConfigSchema(BaseModel):
    obj_id: str
    obj_id_str: str
    features: List[str]
    label: str
    dataset_name: str
    dataset_description: str
    
    @model_validator(mode='after')
    def validate_schema(self):
        schema = self.model_dump()
        features = schema.get("features", [])
        label = schema.get("label", "")
        obj_id_str = schema.get("obj_id_str", "")
        
        regex_obj_str = r"^obj_\w+_\d{6}$"
        # obj_id_str
        match = re.search(regex_obj_str, obj_id_str)
        if not match:
            raise ValueError(f"invalid 'obj_id_str' {obj_id_str}. It must be {regex_obj_str}.")
        
        regex_fd_str = r"^fd_\w+_\d{6}$"
        # features
        for feature in features:
            match = re.search(regex_fd_str, feature)
            if not match:
                raise ValueError(f"invalid 'features' {feature}. It must be {regex_fd_str}.")
            
        # label
        match = re.search(regex_fd_str, label)
        if not match:
            raise ValueError(f"invalid 'label' {label}. It must be {regex_fd_str}.")
        
        return self
        
        