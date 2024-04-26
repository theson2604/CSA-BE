from typing_extensions import Annotated
from fastapi import Depends
from InboundRule.services import InboundRule, IInboundRule

# Services
InboundRuleDepend = Annotated[IInboundRule, Depends(InboundRule)]