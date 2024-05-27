from typing import Dict, List

from pymongo import ReturnDocument

from CustomViewRecord.models import CustomViewRecordModel
from FieldObject.repository import FieldObjectRepository
from Object.repository import ObjectRepository
from RecordObject.models import RecordObjectModel
from RootAdministrator.constants import HIDDEN_METADATA_INFO

from app.common.db_connector import DBCollections, client
from app.common.enums import FieldObjectType
from app.common.errors import HTTPBadRequest

class CustomViewRecordRepository:
    def __init__(self, db_str: str, coll: str):
        global client
        self.db = client.get_database(db_str)
        self.custom_view_record_coll = self.db.get_collection(coll)
        self.db_str = db_str


    async def insert_one(self, view: CustomViewRecordModel) -> str:
        result = await self.custom_view_record_coll.insert_one(view)
        return result.inserted_id