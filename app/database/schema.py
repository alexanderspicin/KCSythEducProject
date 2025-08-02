import re
import uuid
from typing import List

from pydantic import BaseModel, field_validator
from datetime import datetime


class BalanceSchema(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    amount: float


class TransactionSchema(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    amount: float
    timestamp: datetime
    transaction_type: str
    transaction_status: str


class GenerationHistorySchema(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    amount: float
    timestamp: datetime
    s3_link: str


class UserSchema(BaseModel):
    id: uuid.UUID
    email: str
    balance: BalanceSchema
    transactions: List[TransactionSchema]
    generation_history: List[GenerationHistorySchema]


class CreateUserSchema(BaseModel):
    email: str
    password: str

    @field_validator('email')
    def validate_email(cls, email):
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        if not email_pattern.match(email):
            raise ValueError("Invalid email format")
        return email


class CreateTransactionSchema(BaseModel):
    user_id: uuid.UUID
    amount: float
    transaction_type: str


class ExchangeServiceSchema(BaseModel):
    id: uuid.UUID
    rate: float
    last_update: datetime

    class Config:
        from_attributes = True


class UpdateExchangeRateSchema(BaseModel):
    rate: float

    @field_validator('rate')
    def validate_rate(cls, rate):
        if rate <= 0:
            raise ValueError("Exchange rate must be positive")
        return rate