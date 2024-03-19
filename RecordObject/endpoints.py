from fastapi import APIRouter, HTTPException
from Authentication.dependencies import AuthCredentialDepend, AuthServiceDepend
from RecordObject.schemas import RecordObjectSchema
from RecordObject.services import RecordObjectService
from app.common.enums import SystemUserRole
from app.common.errors import HTTPBadRequest
from app.dependencies.authentication import protected_route

router = APIRouter()

@router.post("/create-record")
@protected_route([SystemUserRole.ADMINISTRATOR, SystemUserRole.USER])
async def create_record(
    record: RecordObjectSchema,
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    try:
        db_str, current_user_id = CURRENT_USER.get("db"), CURRENT_USER.get("_id")
        record_service = RecordObjectService(db_str, record.get("object_id"))
        # return await obj_service.create_object_only(obj, current_user_id)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))