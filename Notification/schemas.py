from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel

from app.common.enums import TaskStatus 

class NotificationSchema(BaseModel):
    task_id: str
    type: str
    status: TaskStatus

    object_id: str

    # Create/Update
    record_prefix: Optional[str] = None

    #Inbound File
    created: Optional[int] = None
    failed: Optional[int] = None