from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Union
from datetime import datetime, date, timezone
from bson import ObjectId
from models.user import Avatar

class FundraiserCreate(BaseModel):
    verified: bool = Field(default=False)
    donators: List[str] = Field(default_factory=list)
    category: str
    fundraiserTitle: str
    fundraiserStory: Optional[str] = None
    amountRequired: str
    endDateToRaise: Optional[Union[datetime, str]] = Field(default=None)
    includeTaxBenefit: Optional[str] = None
    createdBy: str
    creatorMail: str
    benefitterImg: Optional[Avatar] = None
    benefitterCreatorRelation: Optional[str] = None
    benefitterName: Optional[str] = None
    benefitterAge: Optional[int] = None
    benefitterGender: Optional[str] = None
    benefitterAddress: Optional[str] = None
    benefitterContact: Optional[str] = None
    amountRaised: float = Field(default=0)
    hospitalName: Optional[str] = None
    hospitalLocation: Optional[str] = None
    ailment: Optional[str] = None
    numberOfDonators: int = Field(default=0)
    coverImg: Optional[Avatar] = None
    
    @field_validator('endDateToRaise', mode='before')
    @classmethod
    def parse_end_date(cls, v):
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            # Try parsing as date string (YYYY-MM-DD) or datetime string
            try:
                # Try datetime format first
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                try:
                    # Try date format (YYYY-MM-DD)
                    date_obj = datetime.strptime(v, '%Y-%m-%d')
                    return date_obj
                except ValueError:
                    # Try other common formats
                    for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S.%f']:
                        try:
                            return datetime.strptime(v, fmt)
                        except ValueError:
                            continue
                    raise ValueError(f"Unable to parse date: {v}")
        return v

class FundraiserResponse(BaseModel):
    _id: str
    verified: bool
    donators: List[str]
    category: str
    fundraiserTitle: str
    fundraiserStory: Optional[str]
    amountRequired: str
    endDateToRaise: Optional[datetime] = None
    includeTaxBenefit: Optional[str]
    createdBy: str
    creatorMail: str
    benefitterImg: Optional[Avatar]
    benefitterCreatorRelation: Optional[str]
    benefitterName: Optional[str]
    benefitterAge: Optional[int]
    benefitterGender: Optional[str]
    benefitterAddress: Optional[str]
    benefitterContact: Optional[str]
    amountRaised: float
    hospitalName: Optional[str]
    hospitalLocation: Optional[str]
    ailment: Optional[str]
    numberOfDonators: int
    coverImg: Optional[Avatar]
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_encoders = {ObjectId: str}

class FundraiserUpdate(BaseModel):
    verified: Optional[bool] = None
    category: Optional[str] = None
    fundraiserTitle: Optional[str] = None
    fundraiserStory: Optional[str] = None
    amountRequired: Optional[str] = None
    endDateToRaise: Optional[datetime] = None
    includeTaxBenefit: Optional[str] = None
    benefitterImg: Optional[Avatar] = None
    benefitterCreatorRelation: Optional[str] = None
    benefitterName: Optional[str] = None
    benefitterAge: Optional[int] = None
    benefitterGender: Optional[str] = None
    benefitterAddress: Optional[str] = None
    benefitterContact: Optional[str] = None
    hospitalName: Optional[str] = None
    hospitalLocation: Optional[str] = None
    ailment: Optional[str] = None
    coverImg: Optional[Avatar] = None

class TypeWrapper(BaseModel):
    type: str

class FundraiserByType(BaseModel):
    type: TypeWrapper

class SearchWrapper(BaseModel):
    search: str

class FundraiserBySearch(BaseModel):
    search: SearchWrapper

