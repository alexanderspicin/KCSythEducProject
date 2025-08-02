import uuid

import bcrypt
from fastapi import Depends
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from logger_config import get_logger

from database.enums import TransactionStatus, TransactionType
from database.models import Users, Balance, Transaction
from database.schema import CreateUserSchema, UserSchema, BalanceSchema, TransactionSchema

from database.dependency import get_db

logger = get_logger(__name__)


def hash_password(password: str) -> str:
    """Хеширование пароля"""
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed_password.decode("utf-8")


def create_user(user_data: CreateUserSchema, db: Session = Depends(get_db)) -> UserSchema:
    """
    Создает нового пользователя с начальным балансом 100 токенов
    """
    logger.info(f"Creating new user with email: {user_data.email}")
    try:
        # Создаем пользователя
        db_user = Users(
            id=uuid.uuid4(),
            email=user_data.email,
            password=hash_password(user_data.password)
        )
        db.add(db_user)
        db.flush()  # Получаем ID без коммита

        # Создаем начальный баланс (по умолчанию 100)
        db_balance = Balance(
            user_id=db_user.id,
        )
        db.add(db_balance)

        # Создаем транзакцию начального депозита
        initial_transaction = Transaction(
            user_id=db_user.id,
            amount=100.0,
            transaction_status=TransactionStatus.DONE,
            transaction_type=TransactionType.CREDIT
        )
        db.add(initial_transaction)

        # Коммитим все изменения
        db.commit()
        db.refresh(db_user)
        
        logger.info(f"User created successfully with ID: {db_user.id}")

        # Возвращаем пользователя в формате Pydantic
        return UserSchema(
            id=db_user.id,
            email=db_user.email,
            balance=BalanceSchema(
                id=db_balance.id,
                user_id=db_balance.user_id,
                amount=db_balance.amount
            ),
            transactions=[TransactionSchema(
                id=initial_transaction.id,
                user_id=initial_transaction.user_id,
                amount=initial_transaction.amount,
                timestamp=initial_transaction.timestamp,
                transaction_type=initial_transaction.transaction_type.value,
                transaction_status=initial_transaction.transaction_status.value
            )],
            generation_history=[]
        )

    except IntegrityError as e:
        db.rollback()
        logger.error(f"Integrity error creating user {user_data.email}: {str(e)}")
        raise Exception(f"Ошибка целостности данных: {str(e)}")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error creating user {user_data.email}: {str(e)}")
        raise Exception(f"Неожиданная ошибка при создании пользователя: {str(e)}")