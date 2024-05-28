from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator
import re

class RecordObjectSchema(BaseModel, extra='allow'):

    object_id: str = Field(..., alias="object_id")
    
    @model_validator(mode='after')
    def validate_field_id(self):
        fields = self.model_dump(exclude=["object_id", "record_id"])
        for field_id in fields.keys():
            regex_str = r"^fd_\w+_\d{6}$"
            match = re.search(regex_str, field_id)
            if not match:
                raise ValueError(f"invalid 'field_id' {field_id}. It must be {regex_str}")
            
        return self

class UpdateRecordSchema(RecordObjectSchema):

    record_id: str = Field(..., alias="record_id")

class DeleteRecordSchema(BaseModel):

    object_id: str = Field(..., alias="object_id")
    record_id: str = Field(..., alias="record_id")