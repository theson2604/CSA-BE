from UserRole.models import UserRole
from app.common.enums import SystemUserRole
from pydantic import ConfigDict, EmailStr, Field, BaseModel, create_model

from app.common.utils import get_current_hcm_datetime

class RootBase(BaseModel):
    id: str = Field(..., alias="_id")
    email: EmailStr = Field(..., alias="email")
    pwd: str = Field(..., alias="pwd")
    db: str = Field(..., alias="db")
    system_role: SystemUserRole = Field(..., alias="system_role")
    
    model_config = ConfigDict(
        populate_by_name=True
    )

RootModel = create_model(
    'RootModel',
    created_at=(str, get_current_hcm_datetime()),
    modified_at=(str, get_current_hcm_datetime()),
    __base__=RootBase
)

class AdministratorModel(RootBase):
    full_name: str = Field(..., alias="full_name" , max_length=30)
    company: str = Field(..., alias="company" ,max_length=80)
    domain: str = Field(..., alias="domain" ,max_length=30)
    
    created_at: str = Field(..., alias="created_at", default_factory=get_current_hcm_datetime)
    modified_at: str = Field(..., alias="modified_at", default_factory=get_current_hcm_datetime)
    
    model_config = ConfigDict(
        populate_by_name=True
    )

    
# class User(Root):
#     user_role: UserRole = Field(...)
#     pass
