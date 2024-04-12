from typing import List, Optional
from pydantic import BaseModel, Field, validator, EmailStr

class EmailSchema(BaseModel):
    email: EmailStr
    pwd: str = Field(..., alias="pwd")
    admin: str = Field(..., alias="admin_id")
    mail_server: str = ""
    protocol: str = ""

class SendMailSchema(BaseModel):
    record: str = Field(..., alias="record_id")
    template: str = Field(..., alias="template_id")
    object: str = Field(..., alias="object_id")
    send_from: str = Field(..., max_length=100)
    send_to: List[str] = Field(..., max_length=100)

    @validator("send_to")
    def validate_send_to(cls, v):
        if not v:
            raise ValueError("send_to cannot be empty")
        for email in v:
            if not email:
                raise ValueError("email address cannot be empty")
        return v
    
    # subject: str = Field(...)
    # body: str = Field(...)
    
class TemplateSchema(BaseModel):
    name: str = Field(..., max_length=100)
    object: str = Field(..., alias="object_id")
    subject: str = Field(..., max_length=100)
    body: str = Field(...)