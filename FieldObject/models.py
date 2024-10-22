from typing import List
from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import FieldObjectType

class FieldObjectBase(BaseModel):
    id: str = Field(..., alias="_id")
    field_type: FieldObjectType = Field(..., alias="field_type")
    field_name: str = Field(..., max_length=100, alias="field_name")
    field_id: str = Field(..., alias="field_id")
    object_id: str = Field(..., alias="object_id")
    sorting_id: int = Field(..., ge=0)
    
    model_config = ConfigDict(
        populate_by_name=True
    )

class FieldId(FieldObjectBase):
    prefix: str = Field(..., alias="prefix")
    
class FieldText(FieldObjectBase):
    length: int = Field(..., gt=0, alias="length")
    
class FieldFloat(FieldObjectBase):
    pass

class FieldInteger(FieldObjectBase):
    pass
    
class FieldTextArea(FieldObjectBase):
    pass
    
class FieldEmail(FieldObjectBase):
    pass

class FieldSelect(FieldObjectBase):
    options: List[str] = Field(..., alias="options")
    
class FieldPhoneNumber(FieldObjectBase):
    country_code: str = Field(..., alias="country_code")

class FieldDate(FieldObjectBase):
    format: str = Field(..., alias="format")
    separator: str = Field(..., alilas="separtor")
    
class FieldReferenceObject(FieldObjectBase):
    display_value: str = Field(..., alias="display_value")
    ref_obj_id: str = Field(..., alias="ref_obj_id")
    ref_obj_id_value: str = Field(..., alias="ref_obj_id_value")
    cascade_option: str = Field(..., alias="cascade_option")
    
class FieldReferenceFieldObject(FieldObjectBase):
    display_value: str = Field(..., alias="display_value")
    ref_field_obj_id: str = Field(..., alias="ref_field_obj_id")
    ref_obj_id_value: str = Field(..., alias="ref_obj_id_value")
    cascade_option: str = Field(..., alias="cascade_option")
