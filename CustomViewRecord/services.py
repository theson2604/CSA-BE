from typing import List

from bson import ObjectId
from CustomViewRecord.models import CustomViewMailModel, CustomViewMainModel, CustomViewRecordModel, CustomViewRelatedObjectModel
from CustomViewRecord.repository import CustomViewRecordRepository
from CustomViewRecord.schemas import CustomViewRecordSchema, UpdateCustomViewRecordSchema
from Object.repository import ObjectRepository
from app.common.enums import CustomViewRecordType
from app.common.errors import HTTPBadRequest
from app.common.utils import get_current_hcm_datetime


class CustomViewRecordService:
    def __init__(self, db_str: str):
        self.repo = CustomViewRecordRepository(db_str)
        self.obj_repo = ObjectRepository(db_str)
        self.db_str = db_str

    async def validate_and_get_all_view_record_models(self, view_records: List[CustomViewRecordSchema], current_user_id: str, parent_id: str = None) -> List[CustomViewRecordModel]:
        list_view_records = []

        for view_record in view_records:
            view_record = view_record.model_dump()
            view_record.update({
                "_id": str(ObjectId()),
                "created_at": get_current_hcm_datetime(),
                "modified_at": get_current_hcm_datetime(),
                "created_by": current_user_id,
                "modified_by": current_user_id,
            })
            type = view_record.get("type")
            if type == CustomViewRecordType.MAIN:
                object_id = view_record.get("object_id")
                if not object_id or not (await self.obj_repo.find_one_by_id(object_id)):
                    raise HTTPBadRequest(f"Can not find Object by id {object_id}")
                if (await self.repo.find_one({"object_id": object_id})):
                    raise HTTPBadRequest(f"Custom Record View type '{CustomViewRecordType.MAIN}' with object_id {object_id} existed")
                
                view_record.pop("main_id")
                view_record.pop("related_obj_id")
                list_view_records.append(CustomViewMainModel.model_validate(view_record).model_dump(by_alias=True))
            else:
                if parent_id:
                    main_id = parent_id
                    view_record.update({"main_id": main_id})
                else:
                    main_id = view_record.get("main_id")
                main_view = await self.repo.find_one_by_id(main_id)
                if not main_view or main_view.get("type") != CustomViewRecordType.MAIN:
                    raise HTTPBadRequest(f"Can not find Custom View type '{CustomViewRecordType.MAIN}' by id {main_id}")
                
                view_record.pop("object_id")
                if type == CustomViewRecordType.RELATED:
                    related_obj_id = view_record.get("related_obj_id")
                    if not related_obj_id or not (await self.obj_repo.find_one_by_id(related_obj_id)):
                        raise HTTPBadRequest(f"Can not find ref object by id {related_obj_id}")
                    if (await self.repo.find_one({
                            "main_id": main_id, 
                            "type": CustomViewRecordType.RELATED,
                            "related_obj_id": related_obj_id
                        })):
                        raise HTTPBadRequest(f"Custom Record View type '{CustomViewRecordType.RELATED}' with main_id {main_id} and related_obj_id {related_obj_id} existed")

                    list_view_records.append(CustomViewRelatedObjectModel.model_validate(view_record).model_dump(by_alias=True))
                else:
                    if (await self.repo.find_one({
                            "main_id": main_id, 
                            "type": type
                        })):
                        raise HTTPBadRequest(f"Custom Record View type '{type}' with main_id {main_id} existed")
                    view_record.pop("related_obj_id")
                    list_view_records.append(CustomViewMailModel.model_validate(view_record).model_dump(by_alias=True))
        
        return list_view_records
            

    async def create_one_view(self, view_record: CustomViewRecordSchema, current_user_id: str):
        view_record = (await self.validate_and_get_all_view_record_models([view_record], current_user_id))[0]
        return await self.repo.insert_one(view_record)
    
    async def create_many_views(self, view_records: List[CustomViewRecordSchema], current_user_id: str):
        view_record = view_records[0].model_dump()
        main_component_id = None
        if view_record.get("type") == CustomViewRecordType.MAIN:
            #Create MAIN first
            main_component_id = await self.create_one_view(view_records[0], current_user_id)
            view_records.pop(0)

        view_record_models = await self.validate_and_get_all_view_record_models(view_records, current_user_id, main_component_id)
        results = await self.repo.insert_many(view_record_models)
        return [main_component_id] + results if main_component_id else results
    
    async def get_one_componet_by_id(self, id: str):
        return await self.repo.find_one_by_id(id)
    
    async def get_all_components_by_object_id(self, id: str):
        main_component = await self.repo.find_one({"object_id": id})
        if not main_component:
            raise HTTPBadRequest(f"Can not find Custom View Record by Object id {id}")
        
        other_components = await self.repo.find_many({"main_id": main_component.get("_id")})
        return [main_component] + other_components
    
    async def update_one_by_id(self, view_record: UpdateCustomViewRecordSchema, current_user_id):
        updated_view_record = (await self.validate_and_get_all_view_record_models([view_record], current_user_id))[0]
        updated_view_record.pop("_id")
        return await self.repo.update_one_by_id(updated_view_record.pop("view_record_id"), updated_view_record)
    
    async def delete_one_by_id(self, id: str) -> int:
        view_record = await self.repo.find_one_by_id(id)
        result = 0
        # if type main -> delete sub components first
        if view_record.get("type") == CustomViewRecordType.MAIN:
            result += await self.repo.delete_many({"main_id": id})

        return result + await self.repo.delete_one_by_id(id)
    
    async def delete_all_by_object_id(self, id: str) -> int:
        result = 0
        main_component_id = (await self.repo.find_one({"object_id": id})).get("_id")
        result += await self.repo.delete_many({"main_id": main_component_id})
        return result + await self.repo.delete_one_by_id(main_component_id)
