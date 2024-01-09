from pydantic import BaseModel, Field
from typing import List

# Fake
class UserRole(BaseModel):
    title: str = Field(...)
    position: str = Field(...)
    level: List[str] = Field(...)
    
