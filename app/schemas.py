from pydantic import BaseModel, Field, EmailStr, ConfigDict
from decimal import Decimal
from datetime import datetime
from typing import Literal


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=100)


class UserResponse(BaseModel):
    id: int
    username: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class TransactionCreate(BaseModel):
    amount: Decimal = Field(gt=0)
    transaction_type: Literal["income", "expense"]
    category: str
    description: str | None = None
    date: datetime | None = None


class TransactionResponse(BaseModel):
    id: int
    user_id: int
    amount: Decimal
    transaction_type: str
    category: str
    description: str | None
    date: datetime

    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    email: str
    password: str

class TransactionUpdate(BaseModel):
    amount: Decimal = Field(gt=0)
    transaction_type: Literal["income", "expense"]
    category: str
    description: str | None = None