from pydantic import BaseModel, EmailStr

class ContactCreate(BaseModel):
    name: str
    email: EmailStr
    message: str

class ContactResponse(BaseModel):
    _id: str
    name: str
    email: str
    message: str

    class Config:
        from_attributes = True

