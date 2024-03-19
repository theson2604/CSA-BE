from abc import ABC, abstractmethod

from FieldObject.repository import FieldObjectRepository
from Object.repository import ObjectRepository
from RecordObject.repository import RecordObjectRepository
from RecordObject.schemas import RecordObjectSchema
from app.common.errors import HTTPBadRequest


class IRecordObjectService(ABC):
    @abstractmethod
    async def create_record(self, record: RecordObjectSchema) -> str:
        raise NotImplementedError
    
class RecordObjectService(IRecordObjectService):
    def __init__(self, db_str: str, obj_id: str):
        self.obj_repo = ObjectRepository(db_str)
        obj = self.obj_repo.find_one_by_id(obj_id)
        if not obj:
            raise HTTPBadRequest(f"Not found object _id {obj_id}")
        
        self.repo = RecordObjectRepository(db_str, coll=obj.get("obj_id"))
        self.field_obj_repo = FieldObjectRepository(db_str)
        
    async def create_record(self, record: RecordObjectSchema) -> str:
        record = record.model_dump()
        obj_id = record.pop("object_id")
        obj_details = await self.obj_repo.get_object_with_all_fields(obj_id)
        fields_obj = obj_details.get("fields")
        