from enum import Enum
from typing_extensions import Annotated
import motor.motor_asyncio
from pydantic import BeforeValidator
from app.settings.config import MongoConfig

client = motor.motor_asyncio.AsyncIOMotorClient(MongoConfig.MONGO_URI)

PyObjectId = Annotated[str, BeforeValidator(str)]

# DB Collections
class DBCollections(str, Enum):
    GROUP_OBJECTS = "GroupObjects"

# Root Collections
class RootCollections(str, Enum):
    USERS = "SystemUsers"
    