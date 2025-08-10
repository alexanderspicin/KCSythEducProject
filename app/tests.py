"""
Тесты для проверки создания пользователя и операций с балансом
"""
import uuid
from sqlalchemy.orm import Session

from database.database import SessionLocal
from database.models import Users, Balance, Transaction
from database.schema import CreateUserSchema, CreateTransactionSchema
from database.enums import TransactionType, Status
from services.user_service import create_user
from services.transaction_service import create_transaction, process_transaction
from logger_config import setup_logging, get_logger

# Настраиваем логирование для тестов
setup_logging(log_level="INFO", log_to_file=False)
logger = get_logger(__name__)


def test_user_creation_and_balance_operations():
    """
    Комплексный тест:
    1. Создание пользователя
    2. Проверка создания начального баланса
    3. Создание транзакции пополнения
    4. Обработка транзакции
    5. Проверка обновления баланса
    """
    # Создаем отдельную сессию для теста
    db: Session = SessionLocal()
    
    try:
        logger.info("=== Начало комплексного теста ===")
        
        # 1. Создание тестового пользователя
        logger.info("1. Создание тестового пользователя")
        test_email = f"test_user_{uuid.uuid4().hex[:8]}@example.com"
        test_password = "test_password_123"
        
        user_data = CreateUserSchema(
            email=test_email,
            password=test_password
        )
        
        # Создаем пользователя
        created_user = create_user(user_data=user_data, db=db)
        
        # Проверяем, что пользователь создан корректно
        assert created_user is not None, "Пользователь не был создан"
        assert created_user.email == test_email, f"Email не совпадает: {created_user.email} != {test_email}"
        assert created_user.id is not None, "ID пользователя не присвоен"
        logger.info(f"✓ Пользователь создан: ID={created_user.id}, Email={created_user.email}")
        
        # 2. Проверка создания пользователя в базе данных
        logger.info("2. Проверка пользователя в базе данных")
        db_user = db.query(Users).filter(Users.id == created_user.id).first()
        assert db_user is not None, "Пользователь не найден в базе данных"
        assert db_user.email == test_email, "Email в БД не совпадает"
        assert db_user.password is not None, "Пароль не сохранен"
        logger.info(f"✓ Пользователь найден в БД: {db_user.email}")
        
        # 3. Проверка создания начального баланса
        logger.info("3. Проверка начального баланса")
        user_balance = db.query(Balance).filter(Balance.user_id == created_user.id).first()
        assert user_balance is not None, "Баланс пользователя не создан"
        assert user_balance.amount == 100.0, f"Начальный баланс неверный: {user_balance.amount} != 100.0"
        assert user_balance.user_id == created_user.id, "User ID в балансе не совпадает"
        logger.info(f"✓ Начальный баланс создан: {user_balance.amount} токенов")
        
        # 4. Проверка начальной транзакции
        logger.info("4. Проверка начальной транзакции")
        initial_transaction = db.query(Transaction).filter(
            Transaction.user_id == created_user.id,
            Transaction.transaction_type == TransactionType.CREDIT,
            Transaction.amount == 100.0
        ).first()
        assert initial_transaction is not None, "Начальная транзакция не создана"
        assert initial_transaction.transaction_status == Status.DONE, "Статус начальной транзакции неверный"
        logger.info(f"✓ Начальная транзакция найдена: ID={initial_transaction.id}")
        
        # 5. Создание дополнительной транзакции пополнения
        logger.info("5. Создание транзакции пополнения")
        top_up_amount = 500.0  # 500 рублей
        
        transaction_data = CreateTransactionSchema(
            user_id=created_user.id,
            amount=top_up_amount,
            transaction_type=TransactionType.CREDIT
        )
        
        new_transaction = create_transaction(transaction_data=transaction_data, db=db)
        assert new_transaction is not None, "Транзакция не создана"
        assert new_transaction.amount == top_up_amount, f"Сумма транзакции неверная: {new_transaction.amount}"
        assert new_transaction.transaction_status == Status.PROCESSING, "Статус новой транзакции должен быть PROCESSING"
        logger.info(f"✓ Транзакция создана: ID={new_transaction.id}, Сумма={new_transaction.amount}")
        
        # 6. Обработка транзакции
        logger.info("6. Обработка транзакции")
        processed_transaction = process_transaction(transaction_id=new_transaction.id, db=db)
        assert processed_transaction is not None, "Транзакция не обработана"
        assert processed_transaction.transaction_status == Status.DONE, "Статус обработанной транзакции должен быть DONE"
        logger.info(f"✓ Транзакция обработана: статус={processed_transaction.transaction_status}")
        
        # 7. Проверка обновления баланса
        logger.info("7. Проверка обновленного баланса")
        db.refresh(user_balance)  # Обновляем объект из БД
        
        # Рассчитываем ожидаемый баланс (100 начальных + 500*1.2 курс)
        expected_balance = 100.0 + (top_up_amount * 1.2)  # 100 + 600 = 700
        
        assert user_balance.amount == expected_balance, f"Баланс после пополнения неверный: {user_balance.amount} != {expected_balance}"
        logger.info(f"✓ Баланс обновлен корректно: {user_balance.amount} токенов")
        
        # 8. Проверка всех транзакций пользователя
        logger.info("8. Проверка всех транзакций пользователя")
        all_transactions = db.query(Transaction).filter(Transaction.user_id == created_user.id).all()
        assert len(all_transactions) == 2, f"Количество транзакций неверное: {len(all_transactions)} != 2"
        
        # Проверяем, что обе транзакции имеют статус DONE
        for transaction in all_transactions:
            assert transaction.transaction_status == Status.DONE, f"Транзакция {transaction.id} имеет неверный статус"
            assert transaction.transaction_type == TransactionType.CREDIT, f"Все транзакции должны быть CREDIT"
        
        logger.info(f"✓ Все транзакции проверены: {len(all_transactions)} транзакций со статусом DONE")
        
        # 9. Проверка связей в базе данных
        logger.info("9. Проверка связей в базе данных")
        
        # Проверяем связь пользователь -> баланс
        assert db_user.balance is not None, "Связь пользователь->баланс не работает"
        assert db_user.balance.amount == expected_balance, "Баланс через связь неверный"
        
        # Проверяем связь пользователь -> транзакции
        assert len(db_user.transactions) == 2, f"Связь пользователь->транзакции неверная: {len(db_user.transactions)}"
        
        # Проверяем связь баланс -> пользователь
        assert user_balance.user.email == test_email, "Связь баланс->пользователь неверная"
        
        logger.info("✓ Все связи в базе данных работают корректно")
        
        # 10. Итоговая проверка данных
        logger.info("10. Итоговая проверка")
        final_user_data = {
            "user_id": str(created_user.id),
            "email": created_user.email,
            "balance": user_balance.amount,
            "transactions_count": len(all_transactions),
            "final_status": "SUCCESS"
        }
        
        logger.info("=== РЕЗУЛЬТАТЫ ТЕСТА ===")
        logger.info(f"User ID: {final_user_data['user_id']}")
        logger.info(f"Email: {final_user_data['email']}")
        logger.info(f"Final Balance: {final_user_data['balance']} токенов")
        logger.info(f"Transactions Count: {final_user_data['transactions_count']}")
        logger.info(f"Status: {final_user_data['final_status']}")
        logger.info("=== ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО! ===")
        
        return final_user_data
        
    except Exception as e:
        logger.error(f"Ошибка в тесте: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()