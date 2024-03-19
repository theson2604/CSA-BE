from abc import ABC, abstractmethod


class IRecordObjectUtils(ABC):
    @abstractmethod
    async def validate_record_values():
        raise NotImplementedError
    
class RecordObjectUtils(IRecordObjectUtils):
    async def validate_record_values():
        pass