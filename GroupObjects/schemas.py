from pydantic import BaseModel, Field

class GroupObjectSchema(BaseModel):
    name: str
    manager_id: str
    
class UpdateGroupObjectSchema(BaseModel):
    id: str = Field(..., alias="_id")
    name: str
    manager_id: str