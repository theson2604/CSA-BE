from typing import List
from pydantic import BaseModel, Field

from FieldObject.schemas import FieldObjectSchema

class ObjectSchema(BaseModel):
    obj_name: str = Field(..., max_length=100)
    group_obj_id: str
    
class ObjectWithFieldSchema(ObjectSchema):
    fields: List[FieldObjectSchema]
    