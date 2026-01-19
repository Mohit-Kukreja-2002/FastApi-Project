from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

class Avatar(BaseModel):
    public_id: Optional[str] = None
    url: Optional[str] = None

class DonationItem(BaseModel):
    fundraiser: str
    fundraiserImg: Optional[str] = None
    amount: float
    date: Optional[datetime] = None

class UserCreate(BaseModel):
    name: Optional[str] = None
    email: EmailStr
    password: Optional[str] = None
    avatar: Optional[Avatar] = None

class UserResponse(BaseModel):
    _id: str
    name: Optional[str] = None
    email: str
    amountDonated: float = 0
    donationsArray: List[DonationItem] = []
    avatar: Optional[Avatar] = None
    createdFunds: List[str] = []
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_encoders = {ObjectId: str}

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    avatar: Optional[str] = None

class SocialAuth(BaseModel):
    email: EmailStr
    name: str
    avatar: Optional[str] = None

