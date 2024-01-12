from typing import List, Optional
from pydantic import BaseModel

from app.common.enums import FieldObjectType

class FieldObjectSchema(BaseModel):
    field_type: FieldObjectType
    field_name: str
    # Text
    length: Optional[int]
    # Select
    options: Optional[List[str]]
    # Phone Number
    country_code: Optional[str]
    number: Optional[str]
    # Reference Object
    source: Optional[str]