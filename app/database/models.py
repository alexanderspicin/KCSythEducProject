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
    email = Column(String, nullable=False, unique=True)
    password = Column(String)
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    balance = relationship("Balance", back_populates="user", uselist=False, cascade="all, delete-orphan")
    generation_history = relationship("GenerationHistory", back_populates="user", cascade="all, delete-orphan")


class Transaction(Base):
    __tablename__ = 'transactions'
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime, default=datetime.now(tz=timezone.utc), nullable=False)
    user_id = Column(UUID, ForeignKey('users.id'), nullable=False)
    amount = Column(Float, nullable=False)
    transaction_status = Column(ENUM(TransactionStatus), nullable=False)
    transaction_type = Column(ENUM(TransactionType), nullable=False)
    user = relationship("Users", back_populates="transactions")  # было "User"


class Balance(Base):
    __tablename__ = 'balance'
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey('users.id'), nullable=False)
    amount = Column(Float, default=100, nullable=False)
    user = relationship("Users", back_populates="balance")  # было "User"


class GenerationHistory(Base):
    __tablename__ = 'generation_history'
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey('users.id'), nullable=False)
    s3_link = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.now(tz=timezone.utc), nullable=False)
    tokens_spent = Column(Float, nullable=False)
    user = relationship("Users", back_populates="generation_history")


class ExchangeService(Base):
    __tablename__ = 'exchange_service'
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    rate = Column(Float, nullable=False, default=1.2)
    last_update = Column(DateTime, default=datetime.now(tz=timezone.utc), nullable=False)
    
    def __init__(self, **kwargs):
        # Проверяем, существует ли уже запись
        from sqlalchemy.orm import object_session
        session = object_session(self)
        if session and session.query(ExchangeService).count() > 0:
            raise ValueError("Cannot create more than one ExchangeService record")
        super().__init__(**kwargs)


