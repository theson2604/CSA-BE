from pydantic import BaseModel, EmailStr

class RootSchema(BaseModel):
    email: EmailStr
    pwd: str
    
class AdminSchema(BaseModel):
    full_name: str
    email: EmailStr
    pwd: str
    company: str
    domain: str
    
class UpdateAdminSchema(BaseModel):
    id: str 
    full_name: str
    email: EmailStr
    pwd: str = None
    company: str
    domain: str
    