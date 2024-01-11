
# Services
from typing_extensions import Annotated

from fastapi import Depends

from RootAdministrator.services import IRootAdministratorServices, RootAdministratorServices


RootAdminServiceDepend = Annotated[IRootAdministratorServices, Depends(RootAdministratorServices)]