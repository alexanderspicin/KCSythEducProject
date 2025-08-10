import uuid
from typing import Optional

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from database.enums import Status, TransactionType
from database.models import Transaction, Balance, Users
from database.schema import CreateTransactionSchema, TransactionSchema
from database.dependency import get_db
from services.exchange_service import convert_rub_to_tokens
from logger_config import get_logger

logger = get_logger(__name__)


def create_transaction(transaction_data: CreateTransactionSchema, db: Session = Depends(get_db)) -> TransactionSchema:
    logger.info(
        f"Creating transaction for user {transaction_data.user_id}, amount: {transaction_data.amount}, type: {transaction_data.transaction_type}")

    try:
        user = db.query(Users).filter(Users.id == transaction_data.user_id).first()
        if not user:
            logger.error(f"User {transaction_data.user_id} not found")
            raise HTTPException(status_code=404, detail="User not found")

        # Создаем транзакцию
        db_transaction = Transaction(
            user_id=transaction_data.user_id,
            amount=transaction_data.amount,
            transaction_type=transaction_data.transaction_type,
            transaction_status=Status.PROCESSING
        )

        db.add(db_transaction)
        db.commit()
        db.refresh(db_transaction)

        result = TransactionSchema.model_validate(db_transaction)
        logger.info(f"Transaction created successfully with ID: {db_transaction.id}")
        return result

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error creating transaction: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error creating transaction: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


def process_transaction(transaction_id: uuid.UUID, db: Session = Depends(get_db)) -> TransactionSchema:
    """
    Обрабатывает транзакцию: обновляет баланс пользователя и статус транзакции
    """
    logger.info(f"Processing transaction with ID: {transaction_id}")

    try:
        db_transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
        if not db_transaction:
            logger.warning(f"Transaction {transaction_id} not found")
            raise HTTPException(status_code=404, detail="Transaction not found")

        if db_transaction.transaction_status != Status.PROCESSING:
            logger.warning(
                f"Transaction {transaction_id} already processed with status: {db_transaction.transaction_status}")
            return TransactionSchema.model_validate(db_transaction)

        user_balance = db.query(Balance).filter(Balance.user_id == db_transaction.user_id).first()
        if not user_balance:
            logger.error(f"Balance for user {db_transaction.user_id} not found")
            db_transaction.transaction_status = Status.FAILED
            db.commit()
            raise HTTPException(status_code=404, detail="User balance not found")

        if db_transaction.transaction_type == TransactionType.CREDIT:
            amount_in_rub = float(db_transaction.amount)
            tokens_to_add = convert_rub_to_tokens(amount_in_rub, db)
            user_balance.amount += tokens_to_add
            logger.info(f"Added {tokens_to_add} tokens to user {db_transaction.user_id} balance")

        elif db_transaction.transaction_type == TransactionType.DEBIT:
            if user_balance.amount < db_transaction.amount:
                logger.warning(
                    f"Insufficient balance for user {db_transaction.user_id}: {user_balance.amount} < {db_transaction.amount}")
                db_transaction.transaction_status = Status.FAILED
                db.commit()
                db.refresh(db_transaction)
                return TransactionSchema.model_validate(db_transaction)

            user_balance.amount -= db_transaction.amount
            logger.info(f"Debited {db_transaction.amount} tokens from user {db_transaction.user_id} balance")

        else:
            logger.error(f"Unknown transaction type: {db_transaction.transaction_type}")
            db_transaction.transaction_status = Status.FAILED
            db.commit()
            raise HTTPException(status_code=400, detail="Invalid transaction type")

        db_transaction.transaction_status = Status.DONE

        db.commit()
        db.refresh(db_transaction)
        db.refresh(user_balance)

        logger.info(f"Transaction {transaction_id} processed successfully. New balance: {user_balance.amount}")
        return TransactionSchema.model_validate(db_transaction)

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error processing transaction {transaction_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error processing transaction {transaction_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


def get_transaction_by_id(transaction_id: uuid.UUID, db: Session = Depends(get_db)) -> Optional[TransactionSchema]:
    """
    Получает транзакцию по ID
    """
    logger.debug(f"Fetching transaction with ID: {transaction_id}")

    try:
        db_transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
        if not db_transaction:
            logger.warning(f"Transaction {transaction_id} not found")
            return None

        return TransactionSchema.model_validate(db_transaction)

    except SQLAlchemyError as e:
        logger.error(f"Database error fetching transaction {transaction_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error occurred")


def get_user_transactions(user_id: uuid.UUID, db: Session = Depends(get_db)) -> list[TransactionSchema]:
    """
    Получает все транзакции пользователя
    """
    logger.debug(f"Fetching transactions for user: {user_id}")

    try:
        db_transactions = db.query(Transaction).filter(Transaction.user_id == user_id).all()
        return [TransactionSchema.model_validate(transaction) for transaction in db_transactions]

    except SQLAlchemyError as e:
        logger.error(f"Database error fetching transactions for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error occurred")
