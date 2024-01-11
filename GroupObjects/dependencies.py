from typing_extensions import Annotated

from fastapi import Depends

from GroupObjects.services import GroupObjectServices, IGroupObjectServices


GroupObjectServiceDepend = Annotated[IGroupObjectServices, Depends(GroupObjectServices)]