from enum import Enum
from typing_extensions import Annotated
import motor.motor_asyncio
from pydantic import BeforeValidator
from dotenv import load_dotenv
import os

load_dotenv()

client = motor.motor_asyncio.AsyncIOMotorClient(os.environ.get("MONGO_URI"))

PyObjectId = Annotated[str, BeforeValidator(str)]

# DB Collections
class DBCollections(str, Enum):
    RECORD_COUNTER = "RecordCounter"
    GROUP_OBJECTS = "GroupObjects"
    FIELD_OBJECT = "FieldObject"
    OBJECT = "Object"
    EMAIL_TEMPLATE = "EmailTemplate"
    WORKFLOW = "Workflow"
    ACTION = "Action"
    AI_DATASET = "AIDataset"
    CUSTOM_VIEW_RECORD = "ViewRecord"
    REPLY_EMAIL = "ReplyEmail"

# Root Collections
class RootCollections(str, Enum):
    USERS = "SystemUsers"
    EMAILS = "SystemEmails"
