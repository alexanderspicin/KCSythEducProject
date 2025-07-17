import datetime
import re
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import List

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

    def credit(self, tokens: int) -> None:
        self.tokens += tokens

    def debit(self, tokens: int) -> None:
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


@dataclass
class User:
    """
    Класс для представления пользователя в системе.

    Attributes:
        id (int): Уникальный идентификатор пользователя
        email (str): Email пользователя
        password (str): Пароль пользователя
    """
    email: str
    password: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    balance: Balance = field(default=None)
    generation_history: List[AudioGenerationHistory] = field(default=List)

    def __post_init__(self):
        self._validate_email()
        self._validate_password()
        if self.balance is None:
            self.balance = Balance(user_id=self.id)

    def _validate_email(self) -> None:
        """Проверяет корректность email."""
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        if not email_pattern.match(self.email):
            raise ValueError("Invalid email format")

    def _validate_password(self) -> None:
        """Проверяет минимальную длину пароля."""
        if len(self.password) < 8:
            raise ValueError("Password must be at least 8 characters long")

    def get_generation_history(self) -> List[AudioGenerationHistory]:
        return self.generation_history


class TransactionType(str, Enum):
    """Класс в котором обозначены все возможные типы транзакций"""
    CREDIT = "CREDIT"
    DEBIT = "DEBIT"


class Transaction:
    """TODO:дописать класс транзакций"""
    def __init__(self, transaction_type: TransactionType, amount: float) -> None:
        self.id = uuid.uuid4()
        self.timestamp = datetime.datetime.now(tz=datetime.timezone.utc)
        self.transaction_type = transaction_type
        self.amount = amount


class GenerationService:
    """TODO: Дописать сервис генерации"""

if __name__ == "__main__":
    user = User(email='spicin@mail.ru', password='12345678')
