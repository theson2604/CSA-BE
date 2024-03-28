import re
from typing import List, Optional
from pydantic import BaseModel, Field, model_validator

from app.common.enums import FieldObjectType 

class FieldObjectSchema(BaseModel):
    field_type: FieldObjectType
    field_name: str
    
    sorting_id: Optional[int] = None
    # Id
    prefix: Optional[str] = None
    
    # Text
    length: Optional[int] = None
    
    # Select
    options: Optional[List[str]] = None
    
    # Phone Number
    country_code: Optional[str] = None
    
    # Reference Object / Field Object
    src: Optional[str] = None
    
    @model_validator(mode='after')
    def validate_field_obj_schema(self):
        schema = self.model_dump()
        field_type = schema.get("field_type")
        if field_type == FieldObjectType.ID:
            if not schema.get("prefix"):
                raise ValueError(f"missing required key 'prefix' for field_type {FieldObjectType.ID}.")
            
        elif field_type == FieldObjectType.TEXT:
            if not schema.get("length"):
                raise ValueError(f"missing required key 'length' for field_type {FieldObjectType.TEXT}.")
            
        elif field_type == FieldObjectType.EMAIL:
            pass
        
        elif field_type == FieldObjectType.TEXTAREA:
            pass
            
        elif field_type == FieldObjectType.SELECT:
            if not schema.get("options"):
                raise ValueError(f"missing required key 'options' for field_type {FieldObjectType.SELECT}.")
        
        elif field_type == FieldObjectType.PHONE_NUMBER:
            country_code = schema.get("country_code")
            if not country_code:
                raise ValueError(f"missing required key 'country_code' for field_type {FieldObjectType.PHONE_NUMBER}.")
            
            regex_str = "^\+?\d{1,2}|\d{1,3}$"
            match = re.search(regex_str, country_code)
            if not match:
                raise ValueError(f"invalid 'country_code' {country_code}. It must be {regex_str}.")
        
        elif field_type == FieldObjectType.REFERENCE_OBJECT:
            src = schema.get("src")
            if not src:
                raise ValueError(f"missing required key 'src' for 'field_type' {FieldObjectType.REFERENCE_OBJECT}.")
            
            regex_str = "^obj_\w+_\d{3}$"
            match = re.search(regex_str, src)
            if not match:
                raise ValueError(f"invalid 'src' {src}. It must be {regex_str}.")
        
        elif field_type == FieldObjectType.REFERENCE_FIELD_OBJECT:
            src = schema.get("src")
            if not src:
                raise ValueError(f"missing required key 'src' for 'field_type' {FieldObjectType.REFERENCE_FIELD_OBJECT}.")
            
            regex_str = "^obj_\w+_\d{3}.fd_\w+_\d{3}$"
            match = re.search(regex_str, src)
            if not match:
                raise ValueError(f"invalid 'src' {src}. It must be {regex_str}.")
        
        else:
            raise ValueError(f"invalid 'field_type' {field_type}.")
                    
        return self
    
class UpdateFieldObjectSchema(FieldObjectSchema):
    id: str = Field(..., alias="_id")
    object_id: str
    field_id: str
    sorting_id: int
