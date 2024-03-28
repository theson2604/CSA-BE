
from fastapi import APIRouter, HTTPException
from Authentication.dependencies import AuthCredentialDepend, AuthServiceDepend
from FieldObject.services import FieldObjectService
from app.common.enums import SystemUserRole
from app.common.errors import HTTPBadRequest
from app.dependencies.authentication import protected_route

router = APIRouter()

@router.delete("/delete-one")
@protected_route([SystemUserRole.ADMINISTRATOR, SystemUserRole.USER])
async def delete_one_field(
    field_id: str,
    CREDENTIALS: AuthCredentialDepend,
    AUTHEN_SERVICE: AuthServiceDepend,
    CURRENT_USER = None
):
    try:
        field_service = FieldObjectService(CURRENT_USER.get("db"))
        await field_service.delete_one_field_by_id(field_id)

        return "Field has been deleted"
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if isinstance(e, Exception):
            raise HTTPBadRequest(str(e))