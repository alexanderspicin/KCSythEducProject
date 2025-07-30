import uuid
from typing import List

from pydantic import BaseModel
from datetime import datetime


class Balance(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    amount: float


class Transaction(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    amount: float
    timestamp: datetime
    transaction_type: str
    transaction_status: str


class GenerationHistory(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    amount: float
    timestamp: datetime
    s3_link: str


class Users(BaseModel):
    id: uuid.UUID
    balance: Balance
    transactions: List[Transaction]
    generation_history: List[GenerationHistory]
