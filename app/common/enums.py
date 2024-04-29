from enum import Enum

class SystemUserRole(str, Enum):
    ROOT = 'root'
    ADMINISTRATOR = 'admin'
    USER = 'user'

class FieldObjectType(str, Enum):
    ID = 'id'
    FLOAT = 'float'
    TEXT = 'text'
    TEXTAREA = 'textarea'
    EMAIL = 'email'
    SELECT = 'select'
    PHONE_NUMBER = 'phonenumber'
    DATE = 'date'
    REFERENCE_OBJECT = 'ref_obj'
    REFERENCE_FIELD_OBJECT = 'ref_field_obj'
    
class StatusCodeException(int, Enum):
    BAD_REQUEST = 400

FIELD_ID = "ID"
