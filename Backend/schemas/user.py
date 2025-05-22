from pydantic import BaseModel, EmailStr

class AdminCreate(BaseModel):
    username: str
    password: str
    email: EmailStr

class AdminOut(BaseModel):
    username: str
    email: EmailStr
