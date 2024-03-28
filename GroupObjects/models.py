from RootAdministrator.models import AdministratorModel, UserModel
from pydantic import ConfigDict, EmailStr, Field, BaseModel, create_model

from app.common.utils import get_current_hcm_datetime

class GroupObjectModel(BaseModel):
    id: str = Field(..., alias="_id")
    name: str = Field(..., max_length=100, alias="name")
    manager: str = Field(..., alias="manager_id", description="It must be _id (str) of the User")
    sorting_id: int = Field(..., ge=0)
    
    created_at: str = Field(..., alias="created_at", default_factory=get_current_hcm_datetime)
    modified_at: str = Field(..., alias="modified_at", default_factory=get_current_hcm_datetime)
    
    model_config = ConfigDict(
        populate_by_name=True
    )
