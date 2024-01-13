from enum import Enum

class SystemUserRole(str, Enum):
    ROOT = 'root'
    ADMINISTRATOR = 'admin'
    USER = 'user'

class FieldObjectType(str, Enum):
    TEXT = 'text'
    EMAIL = 'email'
    SELECT = 'select'
    PHONE_NUMBER = 'phonenumber'
    REFERENCE_OBJECT = 'refobject'
    
class StatusCodeException(int, Enum):
    BAD_REQUEST = 400