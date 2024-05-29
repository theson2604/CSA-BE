from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, EmailStr, model_validator

class EmailSchema(BaseModel):
    email: EmailStr
    pwd: str = Field(..., alias="pwd")
    db_str: str = Field(..., alias="db_str")
    # admin_id: str = Field(..., alias="admin_id")
    template_id: str = Field(..., alias="template_id")
    mail_server: str = ""
    protocol: str = ""

class ScanMailSchema(BaseModel):
    template: str = Field(..., alias="template_id")
    # object: str = Field(..., alias="object_id")
    email: str = Field(..., max_length=100)

    @field_validator("email")
    def validate_send_to(cls, v):
        if not v:
            raise ValueError("email cannot be empty")
        # for email in v:
        #     if not email:
        #         raise ValueError("email address cannot be empty")
        return v

class SendMailSchema(ScanMailSchema):
    record: str = Field(..., alias="record_id")
    send_to: str = Field(..., max_length=100)

class TemplateSchema(BaseModel):
    name: str = Field(..., max_length=100)
    object: str = Field(..., alias="object_id")
    subject: str = None
    body: str = Field(...)
    type: str = Field(..., alias="type")

    @model_validator(mode="after")
    def validate_type(self):
        schema = self.model_dump()
        template_type = schema.get("type")
        if template_type not in ["send", "scan"]:
            raise ValueError(f"type must be either 'send' or 'scan' not '{template_type}'")
        elif template_type == "send" and not schema.get("subject"):
            raise ValueError(f"missing email subject for template type '{template_type}'")
        return self
    

class ReplyMailSchema(BaseModel):
    from_: str
    subject: str
    body: str
    sent_at: str
