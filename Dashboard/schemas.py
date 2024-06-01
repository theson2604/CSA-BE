from pydantic import BaseModel

from app.common.enums import DashboardType

class DashboardSchema(BaseModel):
    x: float
    y: float
    w: float
    h: float
    static: bool
    type: DashboardType
    object_id: str
    field_id: str

class UpdateDashboardSchema(DashboardSchema):
    dashboard_id: str