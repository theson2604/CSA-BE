from typing_extensions import Annotated
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from Authentication.services import AuthenticationServices, IAuthenticationServices

security = HTTPBearer()

# Services
AuthServiceDepend = Annotated[IAuthenticationServices, Depends(AuthenticationServices)]

# 
AuthCredentialDepend = Annotated[HTTPAuthorizationCredentials, Depends(security)]