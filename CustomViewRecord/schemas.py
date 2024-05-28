import re
from typing import List, Optional
from pydantic import BaseModel

from app.common.enums import CustomViewRecordType, DisplayCustomViewRecordType 

class CustomViewRecordSchema(BaseModel):
    x: float
    y: float
    w: float
    h: float
    static: bool
    type: CustomViewRecordType
    display: DisplayCustomViewRecordType

    # Main component
    object_id: Optional[str] = None
    
    # Other component
    main_id: Optional[str] = None

    # Ref component
    related_obj_id: Optional[str] = None

class UpdateCustomViewRecordSchema(CustomViewRecordSchema):
    view_record_id: str