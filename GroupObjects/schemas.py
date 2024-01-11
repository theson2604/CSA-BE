from pydantic import BaseModel

class GroupObjectSchema(BaseModel):
    group_name: str
    manager_id: str
    sorting_id: int
    
class UpdateGroupObjectSchema(BaseModel):
    id: str
    group_name: str
    manager_id: str
    sorting_id: int