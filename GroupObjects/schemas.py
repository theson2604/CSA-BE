from pydantic import BaseModel

class GroupObjectSchema(BaseModel):
    group_name: str
    manager_id: str