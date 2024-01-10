from app.common.enums import SystemUserRole
from functools import wraps

def protected_route(role: SystemUserRole):
    def auth_required(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            print(role.value)
            print(kwargs)
            return await func(*args, **kwargs)
        return wrapper
    return auth_required