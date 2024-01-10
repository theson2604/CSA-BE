from pydantic import BaseModel, EmailStr

class LoginSchema(BaseModel):
    email: EmailStr
    pwd: str
    