from app.common.enums import SystemUserRole
from pydantic import ConfigDict, EmailStr, Field, BaseModel, create_model

from app.common.utils import get_current_hcm_datetime

class EmailModel(BaseModel):
    id: str = Field(..., alias="_id")
    email: EmailStr = Field(..., alias="email")
    pwd: bytes = Field(..., alias="pwd")
    key: bytes = Field(..., alias="key")
    iv: bytes = Field(..., alias="iv")
    db: str = Field(..., alias="db_str")
    admin_id: str = Field(..., alias="admin_id")
    template_id: str = Field(..., alias="template_id")

    created_at: str = Field(..., alias="created_at", default_factory=get_current_hcm_datetime)
    modified_at: str = Field(..., alias="modified_at", default_factory=get_current_hcm_datetime)
    
    model_config = ConfigDict(
        populate_by_name=True
    )

class TemplateModel(BaseModel):
    id: str = Field(..., alias="_id")
    name: str = Field(..., alias="name")
    object: str = Field(..., alias="object_id")
    subject: str = None
    body: str = Field(..., alias="body")
    type: str = Field(..., alias="type")

    created_at: str = Field(..., alias="created_at", default_factory=get_current_hcm_datetime)
    modified_at: str = Field(..., alias="modified_at", default_factory=get_current_hcm_datetime)
    
    model_config = ConfigDict(
        populate_by_name=True
    )

class ReplyEmailModel(BaseModel):
    # id: str = Field(..., alias="_id")
    from_: str = Field(..., alias="from")
    subject: str = Field(..., alias="subject")
    body: str = Field(..., alias="body")
    sent_at: str = Field(..., alias="sent_at")

    created_at: str = Field(..., alias="created_at", default_factory=get_current_hcm_datetime)
    
    model_config = ConfigDict(
        populate_by_name=True
    )