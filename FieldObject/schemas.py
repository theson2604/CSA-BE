from typing import List, Optional
from pydantic import BaseModel, Field

from app.common.enums import FieldObjectType 

class FieldObjectSchema(BaseModel):
    field_type: FieldObjectType
    field_name: str
    # Text
    length: Optional[int] = None
    
    # Select
    options: Optional[List[str]] = None
    
    # Phone Number
    country_code: Optional[str] = None
    number: Optional[str] = None
    
    # Reference Object
    source: Optional[str] = None

class UpdateFieldObjectSchema(BaseModel):
    id: str = Field(..., alias="_id")
    field_type: FieldObjectType
    field_name: str
    # Text
    length: Optional[int] = None
    
    # Select
    options: Optional[List[str]] = None
    
    # Phone Number
    country_code: Optional[str] = None
    number: Optional[str] = None
    
    # Reference Object
    source: Optional[str] = None