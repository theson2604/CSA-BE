from typing import List
from bson import ObjectId

from fastapi import HTTPException
import pymongo
from Action.repository import ActionRepository
from Action.services import ActionService, ActionServiceException
from FieldObject.repository import FieldObjectRepository
from FieldObject.services import FieldObjectServiceException, FieldObjectService
from Object.models import ObjectModel
from Object.repository import ObjectRepository
from Object.schemas import ObjectSchema, ObjectWithFieldSchema
from Workflow.models import WorkflowModel
from Workflow.repository import WorkflowRepository
from Workflow.schemas import WorkflowSchema, WorkflowWithActionSchema
from app.common.enums import StatusCodeException
from app.common.errors import HTTPBadRequest


class WorkflowService:
    def __init__(self, db_str: str):
        # Repo
        self.repo = WorkflowRepository(db_str)
        self.obj_repo = ObjectRepository(db_str)
        self.action_repo = ActionRepository(db_str)
        # Services
        self.action_service = ActionService(db_str)
        # self.field_obj_service = FieldObjectService(db_str)
        
    async def create_workflow(self, workflow: WorkflowSchema, current_user_id: str) -> str:
        workflow = workflow.model_dump()
        object_id = workflow.get("object_id")
        object = await self.obj_repo.find_one_by_id(object_id)
        if not object:
            raise HTTPBadRequest(f"Cannot found Object by {object_id}")
        
        workflow_model = WorkflowModel(
            id = str(ObjectId()),
            name = workflow.get("name"),
            object_id = object_id,
            description = workflow.get("description"),
            trigger = workflow.get("trigger"),
            conditions = workflow.get("conditions")
            # modified_by = current_user_id,
            # created_by = current_user_id
        )
        
        return await self.repo.insert_one(workflow_model.model_dump(by_alias=True))
    
    async def create_workflow_with_actions(self, workflow_with_actions: WorkflowWithActionSchema, current_user_id: str) -> str:
        try:
            workflow_with_actions_schema = workflow_with_actions
            workflow_with_actions = (workflow_with_actions.model_dump())
            workflow_with_actions.pop("actions")
            new_workflow_id = await self.create_workflow(WorkflowSchema(**workflow_with_actions), current_user_id)
            # Create Actions
            await self.action_service.create_many_actions(new_workflow_id, workflow_with_actions_schema.actions, current_user_id)
            return new_workflow_id
        except ActionServiceException as e:
            if new_workflow_id:
                await self.repo.delete_one_by_id(new_workflow_id)
            return HTTPBadRequest(str(e))
        
    async def delete_workflow_and_actions_by_id(self, id: str):
        workflow = self.repo.find_one_by_id(id)
        if not workflow:
            raise HTTPBadRequest(f"Can not find Workflow by id {id}")
        
        return self.repo.delete_one_by_id(id), self.action_repo.delete_many_by_workflow_id(id)

    # async def get_all_objects_with_field_details(self) -> List[dict]:
    #     """
    #         Include parsing Fields
    #     """
    #     return await self.repo.get_all_objects_with_field_details()
    
    # async def get_object_detail_by_id(self, id: str) -> dict:
    #     return await self.repo.get_object_with_all_fields(id)
    
    # async def delete_one_object_by_id(self, object_id: str) -> bool:
    #     await self.field_obj_service.delete_all_fields_by_obj_id(object_id)

    #     return await self.repo.delete_one_by_id(object_id)

    # async def delete_all_objects_by_group_id(self, group_obj_id: str) -> bool:
    #     group = await self.group_obj_repo.find_one_by_id(group_obj_id)
    #     if not group:
    #         raise HTTPBadRequest("Cannot find Group Object by group_obj_id")
        
    #     list_obj = await self.repo.find_all({"group_obj_id": group_obj_id})
    #     for obj in list_obj:
    #         await self.field_obj_service.delete_all_fields_by_obj_id(obj.get('_id'))
        
    #     return await self.repo.delete_many({"group_obj_id": group_obj_id})
