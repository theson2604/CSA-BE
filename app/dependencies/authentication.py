from typing import List
from fastapi import HTTPException, status
from app.common.enums import SystemUserRole
from functools import wraps

def protected_route(role: List[SystemUserRole]):
    def auth_required(func):
        @wraps(func)
        async def wrapper(**kwargs):
            token = kwargs.get("CREDENTIALS").credentials
            authen_service = kwargs.get("AUTHEN_SERVICE")
            current_user = await authen_service.get_user_by_token(token, {"pwd": 0, "created_at": 0})
            kwargs["CURRENT_USER"] = current_user
            if current_user.get("system_role") not in role:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid System Role!",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return await func(**kwargs)
        return wrapper
    return auth_required