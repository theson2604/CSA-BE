from typing import List, Union
from bson import ObjectId
from Action.models import ActionBase
from Action.repository import ActionRepository
from Action.schemas import ActionSchema
from Action.models import *

from FieldObject.schemas import FieldObjectSchema, UpdateFieldObjectSchema
from InboundRule.repository import MailServiceRepository
from Object.repository import ObjectRepository
from Workflow.repository import WorkflowRepository
from app.common.enums import ActionType
from app.common.errors import HTTPBadRequest

class ActionServiceException(Exception):
    pass

    
class ActionService:
    def __init__(self, db_str: str):
        self.repo = ActionRepository(db_str)
        self.object_repo = ObjectRepository(db_str)
        self.mail_repo = MailServiceRepository(db_str)
        self.workflow_repo = WorkflowRepository(db_str)

        self.db_str = db_str

    async def validate_email(self, from_: str, current_user_id: str):
        email = self.mail_repo.find_email({"email": from_})
        if not email:
            raise HTTPBadRequest(f"System Email {from_} is not registered")
        
        if email.get("admin_id") != current_user_id:
            raise HTTPBadRequest(f"System Email {from_} can not be used by current credential")

    async def validate_and_get_all_action_models(self, workflow_id: str, actions: List[ActionSchema], current_user_id: str) -> List[ActionBase]:
        try:
            list_actions = []
            workflow = await self.workflow_repo.find_one_by_id(workflow_id)
            if not workflow:
                raise ActionServiceException(f"Not found workflow by _id {workflow_id}")

            for index, action in enumerate(actions):
                action = action.model_dump()
                object_id = action.get("object_id")
                obj = await self.object_repo.find_one_by_id(object_id)
                if not obj:
                    raise ActionServiceException(f"Not found object by _id {object_id}")

                action_base = {
                    "_id": str(ObjectId()) if not action.get("id") else action.get("id"),
                    "workflow_id": workflow_id,
                    "name": action.get("name"),
                    "type": action.get("type"),
                    "description": action.get("description"),
                    "sorting_id": index,
                    "object_id": object_id
                }
                action_type = action.get("type")
                if action_type is ActionType.SEND:
                    from_ = action.get("from_")
                    to = action.get("to")
                    if len(to) == 0:
                        raise HTTPBadRequest(f"field 'to' of action type '{action_type}' can not be empty.")

                    self.validate_email(from_, current_user_id)
                    action_base.update({
                        "from_": from_,
                        "to": action.get("to"),
                        "template_id": action.get("template_id")
                    })
                    list_actions.append(ActionSend.model_validate(action_base).model_dump(by_alias=True))
                
                elif action_type is ActionType.SCAN:
                    from_ = action.get("from_")
                    self.validate_email(from_, current_user_id)
                    action_base.update({
                        "from_": from_,
                        "time": action.get("time"),
                        "template_id": action.get("template_id")
                    })
                    list_actions.append(ActionScan.model_validate(action_base).model_dump(by_alias=True))
                    
                elif action_type in [ActionType.CREATE, ActionType.UPDATE]:
                    action_base.update({
                        "option": action.get("option"),
                        "field_contents": action.get("field_contents"),
                        "field_configs": action.get("field_configs")
                    })
                    list_actions.append(ActionRecord.model_validate(action_base).model_dump(by_alias=True))
                
            return list_actions
        
        except Exception as e:
            raise ActionServiceException(e)
        
    async def create_many_actions(self, workflow_id: str, actions: List[ActionSchema], current_user_id: str) -> List[str]:
        action_models = await self.validate_and_get_all_action_models(workflow_id, actions, current_user_id)
        return await self.repo.insert_many(action_models)
    
    async def update_one_action(self, action: UpdateFieldObjectSchema) -> int:
        action_dump = action.model_dump()
        action_models = await self.validate_and_get_all_action_models(action_dump.get("object_id"), [action])
        if isinstance(action_models, list) and len(action_models) == 1:
            action_model = action_models[0]
            action_model.update({"sorting_id": action_dump.get("sorting_id")})
            return await self.repo.update_one_by_id(action_model.pop("_id"), action_model)
        
    async def update_sorting(self, fields: List[str]):
        sorted_list = []
        for index, field_id in enumerate(fields):
            sorted_list += [{"_id": field_id, "sorting_id": index}]
        
        await self.repo.update_many(sorted_list)
        
    async def create_one_action(self, action: ActionSchema, current_user_id: str) -> str:
        action_dump = action.model_dump()
        action_models = await self.validate_and_get_all_action_models(action_dump.get("workflow_id"), [action], current_user_id)
        if isinstance(action_models, list) and len(action_models) == 1:
            action_model = action_models[0]
            action_model.update({"sorting_id": action_dump.get("sorting_id")})
            return await self.repo.insert_one(action_model)
    
    async def delete_one_action_by_id(self, id: str) -> bool:
        action = self.repo.find_one_by_id(id)
        if not action:
            raise HTTPBadRequest(f"Can not find Action by id {id}")
        
        return await self.repo.delete_one_by_id(id)
    

    def activate_send():
        pass

    # async def delete_all_fields_by_obj_id(self, object_id: str) -> bool:
    #     object = await self.obj_repo.find_one_by_id(object_id)
    #     if not object:
    #         raise HTTPBadRequest("Cannot find Object by object_id")
        
    #     return await self.repo.delete_many({"object_id": object_id})