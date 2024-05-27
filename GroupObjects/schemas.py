from pydantic import BaseModel, Field

from app.common.enums import GroupObjectType

class GroupObjectSchema(BaseModel):
    name: str
    manager_id: str
    
class UpdateGroupObjectSchema(BaseModel):
    id: str = Field(..., alias="_id")
    name: str
    manager_id: str
    type: GroupObjectType