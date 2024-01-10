from fastapi import HTTPException, status
from app.common.enums import SystemUserRole
from functools import wraps

def protected_route(role: SystemUserRole):
    def auth_required(func):
        @wraps(func)
        async def wrapper(**kwargs):
            token = kwargs.get("credentials").credentials
            authen_service = kwargs.get("authen_service")
            current_user = await authen_service.get_user_by_token(token)
            current_user.pop("pwd")
            current_user.pop("created_at")
            kwargs["current_user"] = current_user
            if current_user.get("system_role") != role:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid System Role!",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return await func(**kwargs)
        return wrapper
    return auth_required