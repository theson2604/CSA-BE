from typing import List

from bson import ObjectId
from Dashboard.models import DashboardModel
from Dashboard.repository import DashboardRepository
from Dashboard.schemas import DashboardSchema, UpdateDashboardSchema
from FieldObject.repository import FieldObjectRepository
from Object.repository import ObjectRepository
from RecordObject.repository import RecordObjectRepository
from app.common.enums import DashboardType
from app.common.errors import HTTPBadRequest
from app.common.utils import get_current_hcm_datetime


class DashboardService:
    def __init__(self, db_str: str):
        self.repo = DashboardRepository(db_str)
        self.obj_repo = ObjectRepository(db_str)
        self.field_repo = FieldObjectRepository(db_str)
        self.db_str = db_str

    async def validate_and_get_all_dashboard_models(self, dashboards: List[DashboardSchema], current_user_id: str) -> List[DashboardModel]:
        list_dashboards = []

        for dashboard in dashboards:
            dashboard = dashboard.model_dump()
            type = dashboard.get("type")
            object_id = dashboard.get("object_id")
            field_id = dashboard.get("field_id")
            if not object_id:
                raise HTTPBadRequest(f"object_id can not be")
            obj = await self.obj_repo.find_one_by_id(object_id)
            if not obj:
                raise HTTPBadRequest(f"Can not find Object by id {object_id}")
            if not field_id or not (await self.field_repo.find_one_by_field_id_str(object_id, field_id)):
                raise HTTPBadRequest(f"Can not find Field by id string {field_id}")

            if type == DashboardType.PIE:
                if (await self.repo.find_one({"object_id": object_id, "field_id_str": field_id, "type": DashboardType.PIE})):
                    raise HTTPBadRequest(f"Dashboard type '{DashboardType.PIE}' with object_id {object_id} and field_id {field_id} existed")
            else:
                if (await self.repo.find_one({"object_id": object_id, "field_id_str": field_id, "type": DashboardType.BAR})):
                    raise HTTPBadRequest(f"Dashboard type '{DashboardType.BAR}' with object_id {object_id} and field_id {field_id} existed")
                
            dashboard.update({
                "_id": str(ObjectId()),
                "obj_id": obj.get("obj_id"),
                "created_at": get_current_hcm_datetime(),
                "modified_at": get_current_hcm_datetime(),
                "created_by": current_user_id,
                "modified_by": current_user_id,
            })
            list_dashboards.append(DashboardModel.model_validate(dashboard).model_dump(by_alias=True))
        
        return list_dashboards
            

    async def create_one_dashboard(self, dashboard: DashboardSchema, current_user_id: str):
        dashboard = (await self.validate_and_get_all_dashboard_models([dashboard], current_user_id))[0]
        return await self.repo.insert_one(dashboard)
    
    async def create_many_dashboards(self, dashboards: List[DashboardSchema], current_user_id: str):
        dashboard_models = await self.validate_and_get_all_dashboard_models(dashboards, current_user_id)
        results = await self.repo.insert_many(dashboard_models)
        return results
    
    async def get_one_by_id(self, id: str):
        dashboard = await self.repo.find_one_by_id(id)
        if not dashboard:
            return None

        record_repo = RecordObjectRepository(self.db_str, dashboard.get("obj_id"))
        field_counts = await record_repo.get_field_value_count(dashboard.get("field_id_str"))
        dashboard.update({
            "value": [field_count.get("_id") for field_count in field_counts],
            "count": [field_count.get("count") for field_count in field_counts]
        })
        return dashboard
    
    async def get_all_by_object_id(self, id: str):
        dashboards = await self.repo.find_many({"object_id": id})
        if len(dashboards) == 0:
            return None
        
        record_repo = RecordObjectRepository(self.db_str, dashboards[0].get("obj_id"))
        for index, dashboard in enumerate(dashboards):
            field_counts = await record_repo.get_field_value_count(dashboard.get("field_id_str"))
            dashboards[index].update({
                "value": [field_count.get("_id") for field_count in field_counts],
                "count": [field_count.get("count") for field_count in field_counts]
            })

        return dashboards

    async def get_all_components(self):
        dashboards = await self.repo.find_many()
        if len(dashboards) == 0:
            return None
        
        for index, dashboard in enumerate(dashboards):
            record_repo = RecordObjectRepository(self.db_str, dashboard.get("obj_id"))
            field_counts = await record_repo.get_field_value_count(dashboard.get("field_id_str"))
            dashboards[index].update({
                "value": [field_count.get("_id") for field_count in field_counts],
                "count": [field_count.get("count") for field_count in field_counts]
            })

        return dashboards
    
    async def update_one_by_id(self, dashboard: UpdateDashboardSchema, current_user_id):
        updated_dashboard = (await self.validate_and_get_all_dashboard_models([dashboard], current_user_id))[0]
        updated_dashboard.pop("_id")
        return await self.repo.update_one_by_id(updated_dashboard.pop("dashboard_id"), updated_dashboard)
    
    async def delete_one_by_id(self, id: str) -> int:
        return await self.repo.delete_one_by_id(id)
    
    async def delete_all_by_object_id(self, id: str) -> int:
        return await self.repo.delete_many({"object_id": id})
