import os
from typing import List
from bson import ObjectId

from dotenv import load_dotenv
from fastapi import HTTPException
import pymongo
from Action.repository import ActionRepository
from Action.services import ActionService, ActionServiceException
from Object.repository import ObjectRepository
from Workflow.models import WorkflowModel
from Workflow.repository import WorkflowRepository
from Workflow.schemas import UpdateWorkflowSchema, WorkflowSchema, WorkflowWithActionSchema
from app.common.enums import ActionType, ActionWorkflowStatus
from app.common.errors import HTTPBadRequest
from app.common.utils import get_current_hcm_datetime
from app.tasks import activate_create, activate_score_sentiment, activate_send, activate_update, set_task_metadata

load_dotenv()


class WorkflowService:
    def __init__(self, db_str: str):
        # Repo
        self.repo = WorkflowRepository(db_str)
        self.obj_repo = ObjectRepository(db_str)
        self.action_repo = ActionRepository(db_str)
        # Services
        self.action_service = ActionService(db_str)
        
        self.db_str = db_str

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
            status = workflow.get("status"),
            trigger = workflow.get("trigger"),
            conditions = workflow.get("conditions"),
            modified_by = current_user_id,
            created_by = current_user_id
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
        
    async def get_all_workflows_by_object_id(self, object_id: str):
        return await self.repo.find_many({"object_id": object_id})
    
    async def get_workflow_with_all_actions(self, workflow_id: str):
        return await self.repo.get_workflow_with_all_actions(workflow_id)
        
    async def delete_workflow_and_actions_by_id(self, id: str):
        workflow = self.repo.find_one_by_id(id)
        if not workflow:
            raise HTTPBadRequest(f"Can not find Workflow by id {id}")
        
        return self.repo.delete_one_by_id(id), self.action_repo.delete_many_by_workflow_id(id)

    async def activate_workflow(self, workflow_id: str, current_user_id: str, access_token: str, record_id: str = None, mail_contents: List[str] = []):
        db = self.db_str
        workflow = await self.repo.find_one_by_id(workflow_id)
        if not workflow:
            raise HTTPBadRequest(f"Can not find workflow by id {workflow_id}")
        
        workflow_with_actions = await self.repo.get_workflow_with_all_actions(workflow_id)
        task = {}
        for action in workflow_with_actions.get("actions"): # for action in actions
            if action.get("status") == ActionWorkflowStatus.INACTIVE:
                continue
            
            type = action.get("type")
            if type == ActionType.SEND:
                task = activate_send.delay(db, action, record_id)
                set_task_metadata(task.id, {"type": ActionType.SEND})
            elif type == ActionType.CREATE:
                task =  activate_create.delay(db, action, current_user_id, mail_contents)
                set_task_metadata(task.id, {"type": ActionType.CREATE})
            elif type == ActionType.UPDATE:
                task = activate_update.delay(db, action, current_user_id, record_id, mail_contents)
                set_task_metadata(task.id, {"type": ActionType.UPDATE})
            elif type == ActionType.SENTIMENT:
                task = activate_score_sentiment(db, action, record_id, current_user_id, access_token)
                set_task_metadata(task.id, {"type": ActionType.SENTIMENT})
                
        return task.id if task != {} else task
    
    async def update_one_workflow(self, workflow: UpdateWorkflowSchema, current_user_id: str) -> int:
        workflow_dump = workflow.model_dump()
        workflow_dump.update({
            "modified_by": current_user_id,
            "modified_at": get_current_hcm_datetime
        })
        return await self.repo.update_one_by_id(workflow_dump.pop("workflow_id"), workflow_dump)
    
    async def update_many_workflows(self, workflows: List[UpdateWorkflowSchema], current_user_id) -> int:
        result = 0
        for workflow in workflows:
            workflow_dump = workflow.model_dump()
            workflow_dump.update({
                "modified_by": current_user_id,
                "modified_at": get_current_hcm_datetime
            })
            if await self.repo.update_one_by_id(workflow_dump.pop("workflow_id"), workflow_dump):
                result += 1
        return result