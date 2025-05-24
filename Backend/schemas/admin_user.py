from pydantic import BaseModel, EmailStr

class AdminCreate(BaseModel):
    username: str
    password: str
    company_list: list[str]
    email: EmailStr

class AdminLogin(BaseModel):
    username: str
    password: str