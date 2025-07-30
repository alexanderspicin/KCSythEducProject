from enum import Enum


class TransactionStatus(str, Enum):
    """Класс в котором обозначены все возможные типы транзакций"""
    PROCESSING = "PROCESSING"
    DONE = "DONE"
    FAILED = "FAILED"


class TransactionType(str, Enum):
    """Класс в котором обозначены все возможные типы транзакций"""
    CREDIT = "CREDIT"
    DEBIT = "DEBIT"