from typing_extensions import Annotated
from fastapi import Depends
from MailService.services import MailServices, IMailServices

# Services
MailServiceDepend = Annotated[IMailServices, Depends(MailServices)]