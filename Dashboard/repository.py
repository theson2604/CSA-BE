from typing import List, Union
from Dashboard.models import DashboardModel
from app.common.db_connector import client, DBCollections


class DashboardRepository:
    def __init__(self, db_str: str, coll = DBCollections.DASHBOARD.value):
        global client
        self.db = client.get_database(db_str)
        self.dashboard_coll = self.db.get_collection(coll)

    async def insert_one(self, dashboard: DashboardModel) -> str:
        result = await self.dashboard_coll.insert_one(dashboard)
        return result.inserted_id

    async def insert_many(self, dashboards: List[DashboardModel]) -> str:
        result = await self.dashboard_coll.insert_many(dashboards)
        return result.inserted_ids

    async def find_one_by_id(self, id: str) -> Union[DashboardModel]:
        return await self.dashboard_coll.find_one({"_id": id})
    
    async def find_one(self, query: dict, projection: dict = None) -> Union[DashboardModel]:
        return await self.dashboard_coll.find_one(query, projection)
    
    async def find_many(self,  query: dict = {}, projection: dict = None) -> List[Union[DashboardModel]]:
        cursor = self.dashboard_coll.find(query, projection)
        return await cursor.to_list(length=None)
    
    async def update_one_by_id(self, id: str, dashboard: dict) -> str:
        result = await self.dashboard_coll.update_one({"_id": id}, {"$set": dashboard})
        return result.modified_count
    
    async def delete_one_by_id(self, id: str) -> int:
        return (await self.dashboard_coll.delete_one({"_id": id})).deleted_count
    
    async def delete_many(self, query: dict) -> int:
        return (await self.dashboard_coll.delete_many(query)).deleted_count