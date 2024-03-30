from app.common.enums import SystemUserRole
from pydantic import ConfigDict, EmailStr, Field, BaseModel, create_model

from app.common.utils import get_current_hcm_datetime

class EmailModel(BaseModel):
    id: str = Field(..., alias="_id")
    email: EmailStr = Field(..., alias="email")
    pwd:bytes = Field(..., alias="pwd")
    key: bytes = Field(..., alias="key")
    iv: bytes = Field(..., alias="iv")
    admin: str = Field(..., alias="admin_id", description="It must be _id (str) of an Admin")

    created_at: str = Field(..., alias="created_at", default_factory=get_current_hcm_datetime)
    modified_at: str = Field(..., alias="modified_at", default_factory=get_current_hcm_datetime)
    
    model_config = ConfigDict(
        populate_by_name=True
    )

class TemplateModel(BaseModel):
    id: str = Field(..., alias="_id")
    name: str = Field(..., alias="name")
    object: str = Field(..., alias="object_id")
    subject: str = Field(..., alias="subject")
    body: str = Field(..., alias="body")