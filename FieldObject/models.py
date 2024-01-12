from typing import List
from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import FieldObjectType

class FieldObjectBase(BaseModel):
    id: str = Field(..., alias="_id")
    field_type: FieldObjectType = Field(..., alias="field_type")
    field_name: str = Field(..., max_length=100, alias="name")
    field_id: str = Field(..., alias="field_id")
    sorting_id: int = Field(..., ge=0)
    
    model_config = ConfigDict(
        populate_by_name=True
    )
    
class FieldText(FieldObjectBase):
    length: int = Field(..., gt=0, alias="length")
    
class FieldEmail(FieldObjectBase):
    pass

class FieldSelect(FieldObjectBase):
    options: List[str] = Field(..., alias="options")
    
class FieldPhoneNumber(FieldObjectBase):
    country_code: str = Field(..., alias="country_code")
    number: str = Field(..., alias="phone_number")
    
class FieldReferenceObject(FieldObjectBase):
    source: str = Field(..., alias="source")