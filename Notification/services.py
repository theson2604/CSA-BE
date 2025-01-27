import json
import logging
from fastapi import WebSocket
from Action.repository import ActionRepository
from Action.models import *
from Object.repository import ObjectRepository
from Workflow.repository import WorkflowRepository
from app.common.enums import ActionType, TaskStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
    
class NotificationService:
    def __init__(self, db_str: str):
        self.repo = ActionRepository(db_str)
        self.object_repo = ObjectRepository(db_str)
        # self.mail_repo = MailServiceRepository(db_str)
        self.workflow_repo = WorkflowRepository(db_str)

        self.db_str = db_str

    async def send_one(task_id: str, result, clients):
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
                message = result.result
            else:
                message = "Failed to send email."
        elif task_type == ActionType.CREATE:
            if task_status == TaskStatus.SUCCESS:
                message = "Create record succesfully."
                task_results, fd_id = result.result
                if len(task_results) == 0:
                    task_results = [""]
                notification.update({"result": {
                    "object_id": task_results[0].get("object_id"),
                    "record_prefix": [task_result.get(fd_id) for task_result in task_results],
                }})
            else:
                message = "Failed to create record."
        elif task_type == ActionType.UPDATE:
            if task_status == TaskStatus.SUCCESS:
                message = "Update record succesfully."
                task_results, fd_id = result.result
                notification.update({"result": {
                    "object_id": task_results[0].get("object_id"),
                    "record_prefix": [task_result.get(fd_id) for task_result in task_results],
                }})
                
            else:
                message = "Failed to update record."
                notification.update({"result": {
                    "status": TaskStatus.FAILURE
                }})
                
        elif task_type == ActionType.PREPROCESS_DATASET:
            if task_status == TaskStatus.SUCCESS:
                task_result = result.result
                dataset_message = task_result.pop("message")
                message = f"Dataset AI - {dataset_message} preprocess succesfully."
                notification.update(**task_result)
                
            else:
                message = "Failed to preprocess datasets."
                notification.update({"result": {
                    "status": TaskStatus.FAILURE
                }})
                
        elif task_type == ActionType.SENTIMENT:
            if task_status == TaskStatus.SUCCESS:
                message = "Scoring sentiment succesfully."
                task_result = result.result
                notification.update({"result": {
                    "record_prefix": task_result.get("record_prefix"),
                    "score": task_result.get("score"),
                    "object_id": task_result.get("object_id")
                }})
                
            else:
                message = "Failed to score sentiment."
        elif task_type == ActionType.INBOUND:
            if task_status == TaskStatus.SUCCESS:
                message = "File uploading succesfully."
                object_id, success, fail = result.result
                notification.update({"result": {
                    "object_id": object_id,
                    "success": success,
                    "failed": fail,
                }})
                
            else:
                message = "Failed to upload file."
        else:
            if task_status == TaskStatus.SUCCESS:
                task_result = result.result
                message = "Email scanned successfully."
                notification.update({"result": {
                    "emails": len(task_result),
                }})
            else:
                message = "Failed to upload file."
        notification["message"] = message
        logger.info("NOTIFICATION: ", notification)
        # from app.main import clients
        for client in clients:
            await client.send_json(notification)