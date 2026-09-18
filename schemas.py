from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TransactionCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    type: str = Field(..., pattern="^(income|expense)$")
    category: str = Field(..., min_length=1, max_length=50)
    date: date

    @field_validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be positive')
        return v


class TransactionUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    amount: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    type: Optional[str] = Field(None, pattern="^(income|expense)$")
    category: Optional[str] = Field(None, min_length=1, max_length=50)
    date: Optional[date] = None


class TransactionResponse(BaseModel):
    id: int
    title: str
    amount: Decimal
    type: str
    category: str
    date: date
    owner_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True
