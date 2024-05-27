from typing import List
from RootAdministrator.models import AdministratorModel, UserModel
from pydantic import ConfigDict, EmailStr, Field, BaseModel, create_model

from app.common.enums import GroupObjectType
from app.common.utils import get_current_hcm_datetime

class DatasetAIModel(BaseModel):
    id: str = Field(..., alias="_id")
    features: List[str] = Field(..., alias="features")
    label: str = Field(..., alias="features")
    src_obj_id: str = Field(..., alias="src_obj_id")
    dest_obj_id: str = Field(..., alias="dest_obj_id")
    
    model_config = ConfigDict(
        populate_by_name=True
    )
