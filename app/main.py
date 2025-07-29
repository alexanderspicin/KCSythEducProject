import datetime
import re
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import List
import bcrypt


@dataclass
class ExchangeService:
    """
    Класс для представления обменного курса валюты в токены

    Attributes:
        rate (float): Обменный курс
        last_update (datetime.datetime): Дата последнего изменения обменного курса(UTC)
    """
    rate: float
    last_update: datetime.datetime = field(default=datetime.datetime.now(tz=datetime.timezone.utc))

    def update_rate(self, rate: float) -> None:
        """Метод для обновления обменного курса"""
        self.rate = rate
        self.last_update = datetime.datetime.now(tz=datetime.timezone.utc)

    def convert_rub_to_tokens(self, amount_in_rub: float) -> float:
        """Метод для конвертации рублей в токены по текущему курсу"""
        return amount_in_rub * self.rate


"""Инициализация exchange service"""
exchange_service = ExchangeService(rate=1.2)


@dataclass
class Balance:
    """
    Класс для представления пользовательского баланса

    Attributes:
        user_id (uuid.UUID): Идентификатор пользователя
        id (uuid.UUID): Уникальный идентификатор баланса
        tokens (int): Текущий баланс токенов доступных для генерации аудиозаписи
    """
    user_id: uuid.UUID
    id: uuid.UUID = uuid.uuid4()
    tokens: float = field(default=100)

    def credit(self, tokens: float) -> None:
        self.tokens += tokens

    def debit(self, tokens: float) -> None:
        self.tokens -= tokens


@dataclass
class AudioGenerationHistory:
    """
    Класс для предоставления сгенерированных аудиозаписей

    Attributes:
        user_id (uuid.UUID): Идентификатор пользователя
        id (uuid.UUID): Уникальный идентификатор аудиозаписи
        s3_link (str): Ссылка на файл в S3 хранилище
        timestamp (datetime.datetime): Время генерации (UTC)
        tokens_spent (float): Количество токенов потраченных на генерацию
    """
    user_id: uuid.UUID
    s3_link: str
    tokens_spent: float
    timestamp: datetime.datetime
    id: uuid.UUID = uuid.uuid4()
    timestamp: datetime.datetime = field(default=datetime.datetime.now(tz=datetime.timezone.utc))

    def get_audio(self) -> bytes:
        """Метод для получения аудиозаписи из S3"""


class TransactionType(str, Enum):
    """Класс в котором обозначены все возможные типы транзакций"""
    CREDIT = "CREDIT"
    DEBIT = "DEBIT"


class TransactionStatus(str, Enum):
    """Класс в котором обозначены все возможные типы транзакций"""
    PROCESSING = "PROCESSING"
    DONE = "DONE"
    FAILED = "FAILED"


class Transaction:
    """Класс транзакций с типом и суммой"""

    def __init__(self, transaction_type: TransactionType, amount: float) -> None:
        self.id = uuid.uuid4()
        self.timestamp = datetime.datetime.now(tz=datetime.timezone.utc)
        self.transaction_type = transaction_type
        self.transaction_status = TransactionStatus.PROCESSING
        self.amount = amount

    def transaction_processing(self, balance: Balance) -> None:
        match self.transaction_type:
            case "CREDIT":
                amounts_of_tokens = exchange_service.convert_rub_to_tokens(self.amount)
                balance.credit(amounts_of_tokens)
                self.transaction_status = TransactionStatus.DONE

            case "DEBIT":
                balance.debit(self.amount)
                self.transaction_status = TransactionStatus.DONE

            case _:
                self.transaction_status = TransactionStatus.FAILED


@dataclass
class User:
    """
    Класс для представления пользователя в системе.

    Attributes:
        id (int): Уникальный идентификатор пользователя
        email (str): Email пользователя
        __password (str): Пароль пользователя
    """
    email: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    balance: Balance = field(default=None)
    generation_history: List[AudioGenerationHistory] = field(default_factory=list)
    transaction_history: List[Transaction] = field(default_factory=list)
    __password: bytes = b""

    def __post_init__(self):
        self._validate_email()
        if self.balance is None:
            self.balance = Balance(user_id=self.id)

    def _validate_email(self) -> None:
        """Проверяет корректность email."""
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        if not email_pattern.match(self.email):
            raise ValueError("Invalid email format")

    def set_password(self, plain_password: str) -> None:
        """Хеширует введенный пароль и сохраняет его в классе."""
        hashed_password = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt())
        self.__password = hashed_password

    def check_password(self, plain_password: str) -> bool:
        """Проверяет, совпадает ли введённый пароль с хранимым хэшем."""
        return bcrypt.checkpw(plain_password.encode("utf-8"), self.__password)

    def get_generation_history(self) -> List[AudioGenerationHistory]:
        return self.generation_history

    def get_transaction_history(self) -> List[Transaction]:
        return self.transaction_history

    def update_balance(self, transaction_type: TransactionType, amount: float) -> None:
        match transaction_type:
            case "CREDIT":
                transaction = Transaction(TransactionType.CREDIT, amount)
                self.transaction_history.append(transaction)
                transaction.transaction_processing(self.balance)

            case "DEBIT":
                transaction = Transaction(TransactionType.DEBIT, amount)
                self.transaction_history.append(transaction)
                transaction.transaction_processing(self.balance)

            case _:
                raise ValueError("Invalid transaction type")


class GenerationService(ABC):
    """Абстрактный сервис генерации аудио"""

    @abstractmethod
    def synthesize(self, text: str, user_id: uuid) -> str:
        """
        Абстрактный метод синтеза аудио из текста.
        """
        pass


class TTSGenerationService(GenerationService):
    def synthesize(self, text: str, user_id: uuid.UUID) -> str:
        # Логика реализации синтеза речи
        return f"Generated audio for {text}"


class VoiceCloneService(GenerationService):
    def synthesize(self, text: str, user_id: uuid.UUID) -> str:
        # Логика голосового клонирования
        return f"Copied voice and generated audio for {text}"
