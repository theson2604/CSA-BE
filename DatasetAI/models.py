from typing import List
from pydantic import ConfigDict, Field, BaseModel

from app.common.utils import get_current_hcm_datetime

class HistogramLabels(BaseModel):
    labels: List[int]
    counts: List[int]

class DatasetAIModel(BaseModel):
    id: str = Field(..., alias="_id")
    features: List[str] = Field(..., alias="features")
    label: str = Field(..., alias="label")
    name: str = Field(..., alias="name")
    dataset_obj_id_str: str = Field(..., alias="dataset_obj_id_str")
    description: str = Field(..., alias="description")
    histogram_labels: HistogramLabels
    
    created_at: str = Field(..., alias="created_at", default_factory=get_current_hcm_datetime)
    
    model_config = ConfigDict(
        populate_by_name=True
    )
