from typing import List
from RootAdministrator.models import AdministratorModel, UserModel
from pydantic import ConfigDict, EmailStr, Field, BaseModel, create_model

from app.common.enums import GroupObjectType
from app.common.utils import get_current_hcm_datetime

class DatasetAIModel(BaseModel):
    id: str = Field(..., alias="_id")
    histogram_labels: dict = Field(..., alias="histogram_labels")
    
    model_config = ConfigDict(
        populate_by_name=True
    )
