from enum import Enum

class SystemUserRole(str, Enum):
    ROOT = 'root'
    ADMINISTRATOR = 'admin'
    USER = 'user'
    DATASCIENTIST = 'data_scientist'

class FieldObjectType(str, Enum):
    ID = 'id'
    FLOAT = 'float'
    INTEGER = 'integer'
    TEXT = 'text'
    TEXTAREA = 'textarea'
    EMAIL = 'email'
    SELECT = 'select'
    PHONE_NUMBER = 'phonenumber'
    DATE = 'date'
    REFERENCE_OBJECT = 'ref_obj'
    REFERENCE_FIELD_OBJECT = 'ref_field_obj'
    DATASET = 'dataset'

class ActionType(str, Enum):
    SEND = 'send'
    SCAN = 'scan'
    CREATE  = 'create'
    UPDATE =  'update'
    SENTIMENT = 'sentiment'
    INBOUND = 'inbound'
    PREPROCESS_DATASET = 'preprocess_dataset'
    
class ActionWorkflowStatus(str, Enum):
    ACTIVE = 'active'
    INACTIVE = 'inactive'

class TaskStatus(str, Enum):
    SUCCESS = 'SUCCESS'
    FAILURE = 'FAILURE'
    
class CustomViewRecordType(str, Enum):
    MAIN = 'main'
    RELATED = 'related'
    SEND_EMAIL = 'send_email'
    MAILBOX = 'mailbox'

class DashboardType(str, Enum):
    PIE = 'pie'
    BAR = 'bar'
    
class StatusCodeException(int, Enum):
    BAD_REQUEST = 400

FIELD_ID = "ID"
# Default field Sentiment Score
DEFAULT_SENTIMENT_SCORE_FIELD = "Sentiment Score"
DEFAULT_SENTIMENT_SCORE_FIELD_ID = "sentimentscore"

class GroupObjectType(str, Enum):
    AI_DATASETS = "ai_dataset"
    OBJECT = "obj" 
