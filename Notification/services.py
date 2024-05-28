import json
from fastapi import WebSocket
from Action.repository import ActionRepository
from Action.models import *
from Object.repository import ObjectRepository
from Workflow.repository import WorkflowRepository
from app.common.enums import ActionType, TaskStatus
from app.common.errors import HTTPBadRequest

    
class NotificationService:
    def __init__(self, db_str: str):
        self.repo = ActionRepository(db_str)
        self.object_repo = ObjectRepository(db_str)
        # self.mail_repo = MailServiceRepository(db_str)
        self.workflow_repo = WorkflowRepository(db_str)

        self.db_str = db_str

    async def send_one(task_id: str, result, clients: List[WebSocket]):
        task_status = result.status
        from app.tasks import get_task_metadata
        metadata = get_task_metadata(task_id)
        if metadata:
            metadata = json.loads(metadata)
            task_type = metadata.get("type")
        else:
            task_type = "None"
        notification = {"task_id": task_id, "type": task_type, "status": task_status}
        if task_type == ActionType.SEND:
            if task_status == TaskStatus.SUCCESS:
                message = "Send email succesfully."
            else:
                message = "Failed to send email."
        elif task_type == ActionType.CREATE:
            if task_status == TaskStatus.SUCCESS:
                message = "Create record succesfully."
                task_result, fd_id = result.result
                notification.update({"records": [{
                    "object_id": record.get("object_id"),
                    "record_prefix": record.get(fd_id)
                } for record in task_result]})
            else:
                message = "Failed to create record."
        elif task_type == ActionType.UPDATE:
            if task_status == TaskStatus.SUCCESS:
                message = "Update record succesfully."
                task_result, fd_id = result.result
                notification.update({"record": {
                    "object_id": task_result.get("object_id"),
                    "record_prefix": task_result.get(fd_id)
                }})
                
            else:
                message = "Failed to update record."
        else:
            if task_status == TaskStatus.SUCCESS:
                message = "Upload file succesfully."
                object_id, created, failed = result.result
                notification.update({"record": {
                    "object_id": object_id,
                    "created": created,
                    "failed": failed
                }})
            else:
                message = "Failed to upload file."
        notification["message"] = message
        print("NOTIFICATION: ", notification)
        for client in clients:
            await client.send_json(notification)