from datetime import datetime, timezone
import uuid

from sqlalchemy import Column, UUID, String, DateTime, ForeignKey, Float
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import relationship

from .database import Base
from .enums import TransactionStatus, TransactionType


class Users(Base):
    __tablename__ = 'users'
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    password = Column(String)
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    balance = relationship("Balance", back_populates="user", uselist=False, cascade="all, delete-orphan")


class Transaction(Base):
    __tablename__ = 'transactions'
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime, default=datetime.now(tz=timezone.utc), nullable=False)
    user_id = Column(UUID, ForeignKey('users.id'), nullable=False)
    amount = Column(Float, nullable=False)
    transaction_status = Column(ENUM(TransactionStatus), nullable=False)
    transaction_type = Column(ENUM(TransactionType), nullable=False)
    user = relationship("User", back_populates="transactions")


class Balance(Base):
    __tablename__ = 'balance'
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey('users.id'), nullable=False)
    amount = Column(Float, default=100, nullable=False)
    user = relationship("User", back_populates="balance")


class GenerationHistory(Base):
    __tablename__ = 'generation_history'
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey('users.id'), nullable=False)
    s3_link = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.now(tz=timezone.utc), nullable=False)
    tokens_spent = Column(Float, nullable=False)
    user = relationship("User", back_populates="transactions")