from pydantic import BaseModel, EmailStr
from typing import Optional

class PaymentCreate(BaseModel):
    email: EmailStr
    fundId: str
    payment_info: Optional[dict] = None
    amount: float

class PaymentIntent(BaseModel):
    amount: float

class PaymentResponse(BaseModel):
    success: bool
    client_secret: Optional[str] = None

