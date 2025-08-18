"""
Test suite for KCSythEducProject application
Tests user creation, balance operations, and transaction processing
"""
import uuid
import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from database.database import SessionLocal, get_db
from database.models import Users, Balance, Transaction
from database.schema import CreateUserSchema, CreateTransactionSchema
from database.enums import TransactionType, Status
from services.user_service import create_user
from services.transaction_service import create_transaction, process_transaction
from logger_config import setup_logging, get_logger
from main import app

# Setup logging for tests
setup_logging(log_level="INFO", log_to_file=False)
logger = get_logger(__name__)

# Test client for FastAPI
client = TestClient(app)


@pytest.fixture
def db_session():
    """Provide a database session for testing"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_user_data():
    """Provide test user data"""
    return {
        "email": f"test_user_{uuid.uuid4().hex[:8]}@example.com",
        "password": "test_password_123"
    }


@pytest.fixture
def test_user(db_session, test_user_data):
    """Create and return a test user"""
    user_data = CreateUserSchema(**test_user_data)
    user = create_user(user_data=user_data, db=db_session)
    db_session.commit()
    return user


class TestUserCreation:
    """Test user creation functionality"""
    
    def test_create_user_success(self, db_session, test_user_data):
        """Test successful user creation"""
        user_data = CreateUserSchema(**test_user_data)
        created_user = create_user(user_data=user_data, db=db_session)
        
        assert created_user is not None
        assert created_user.email == test_user_data["email"]
        assert created_user.id is not None
        assert created_user.password is not None
        
        # Verify user exists in database
        db_user = db_session.query(Users).filter(Users.id == created_user.id).first()
        assert db_user is not None
        assert db_user.email == test_user_data["email"]
    
    def test_create_user_duplicate_email(self, db_session, test_user):
        """Test user creation with duplicate email fails"""
        duplicate_user_data = CreateUserSchema(
            email=test_user.email,
            password="another_password"
        )
        
        # This should raise an exception or return None
        with pytest.raises(Exception):
            create_user(user_data=duplicate_user_data, db=db_session)


class TestBalanceOperations:
    """Test balance-related operations"""
    
    def test_initial_balance_creation(self, db_session, test_user):
        """Test that initial balance is created with user"""
        user_balance = db_session.query(Balance).filter(
            Balance.user_id == test_user.id
        ).first()
        
        assert user_balance is not None
        assert user_balance.amount == 100.0  # Initial balance
        assert user_balance.user_id == test_user.id
    
    def test_initial_transaction_creation(self, db_session, test_user):
        """Test that initial transaction is created with user"""
        initial_transaction = db_session.query(Transaction).filter(
            Transaction.user_id == test_user.id,
            Transaction.transaction_type == TransactionType.CREDIT,
            Transaction.amount == 100.0
        ).first()
        
        assert initial_transaction is not None
        assert initial_transaction.transaction_status == Status.DONE
        assert initial_transaction.user_id == test_user.id


class TestTransactionProcessing:
    """Test transaction processing functionality"""
    
    def test_create_credit_transaction(self, db_session, test_user):
        """Test creating a credit transaction"""
        transaction_data = CreateTransactionSchema(
            user_id=test_user.id,
            amount=500.0,
            transaction_type=TransactionType.CREDIT
        )
        
        transaction = create_transaction(transaction_data=transaction_data, db=db_session)
        
        assert transaction is not None
        assert transaction.amount == 500.0
        assert transaction.transaction_type == TransactionType.CREDIT
        assert transaction.transaction_status == Status.PROCESSING
        assert transaction.user_id == test_user.id
    
    def test_process_transaction_success(self, db_session, test_user):
        """Test successful transaction processing"""
        # Create a transaction first
        transaction_data = CreateTransactionSchema(
            user_id=test_user.id,
            amount=300.0,
            transaction_type=TransactionType.CREDIT
        )
        
        transaction = create_transaction(transaction_data=transaction_data, db=db_session)
        
        # Process the transaction
        processed_transaction = process_transaction(
            transaction_id=transaction.id, 
            db=db_session
        )
        
        assert processed_transaction is not None
        assert processed_transaction.transaction_status == Status.DONE
        
        # Verify balance was updated
        user_balance = db_session.query(Balance).filter(
            Balance.user_id == test_user.id
        ).first()
        
        # Expected: 100 (initial) + 300*1.2 (exchange rate) = 460
        expected_balance = 100.0 + (300.0 * 1.2)
        assert user_balance.amount == expected_balance
    
    def test_multiple_transactions(self, db_session, test_user):
        """Test processing multiple transactions"""
        transactions = []
        amounts = [100.0, 200.0, 150.0]
        
        # Create multiple transactions
        for amount in amounts:
            transaction_data = CreateTransactionSchema(
                user_id=test_user.id,
                amount=amount,
                transaction_type=TransactionType.CREDIT
            )
            transaction = create_transaction(transaction_data=transaction_data, db=db_session)
            transactions.append(transaction)
        
        # Process all transactions
        for transaction in transactions:
            process_transaction(transaction_id=transaction.id, db=db_session)
        
        # Verify final balance
        user_balance = db_session.query(Balance).filter(
            Balance.user_id == test_user.id
        ).first()
        
        # Expected: 100 (initial) + sum(amounts * 1.2)
        expected_balance = 100.0 + sum(amount * 1.2 for amount in amounts)
        assert user_balance.amount == expected_balance
        
        # Verify all transactions are processed
        all_transactions = db_session.query(Transaction).filter(
            Transaction.user_id == test_user.id
        ).all()
        
        assert len(all_transactions) == 4  # 1 initial + 3 new
        for transaction in all_transactions:
            assert transaction.transaction_status == Status.DONE


class TestDatabaseRelationships:
    """Test database relationships and constraints"""
    
    def test_user_balance_relationship(self, db_session, test_user):
        """Test user-balance relationship"""
        user_balance = db_session.query(Balance).filter(
            Balance.user_id == test_user.id
        ).first()
        
        # Test forward relationship
        assert test_user.balance is not None
        assert test_user.balance.amount == user_balance.amount
        
        # Test reverse relationship
        assert user_balance.user is not None
        assert user_balance.user.email == test_user.email
    
    def test_user_transactions_relationship(self, db_session, test_user):
        """Test user-transactions relationship"""
        # Create a transaction
        transaction_data = CreateTransactionSchema(
            user_id=test_user.id,
            amount=100.0,
            transaction_type=TransactionType.CREDIT
        )
        create_transaction(transaction_data=transaction_data, db=db_session)
        
        # Test relationship
        assert len(test_user.transactions) >= 2  # Initial + new transaction
        
        for transaction in test_user.transactions:
            assert transaction.user_id == test_user.id


class TestAPIEndpoints:
    """Test FastAPI endpoints"""
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestErrorHandling:
    """Test error handling scenarios"""
    
    def test_invalid_user_id(self, db_session):
        """Test handling of invalid user ID"""
        invalid_user_id = uuid.uuid4()
        
        transaction_data = CreateTransactionSchema(
            user_id=invalid_user_id,
            amount=100.0,
            transaction_type=TransactionType.CREDIT
        )
        
        # This should handle the case gracefully
        with pytest.raises(Exception):
            create_transaction(transaction_data=transaction_data, db=db_session)
    
    def test_invalid_transaction_amount(self, db_session, test_user):
        """Test handling of invalid transaction amounts"""
        invalid_amounts = [-100.0, 0.0, None]
        
        for amount in invalid_amounts:
            if amount is not None:
                transaction_data = CreateTransactionSchema(
                    user_id=test_user.id,
                    amount=amount,
                    transaction_type=TransactionType.CREDIT
                )
                
                # Should handle invalid amounts appropriately
                with pytest.raises(Exception):
                    create_transaction(transaction_data=transaction_data, db=db_session)


def run_integration_test():
    """
    Run a comprehensive integration test
    This function can be called directly for manual testing
    """
    db = SessionLocal()
    
    try:
        logger.info("=== Starting Integration Test ===")
        
        # Create test user
        test_email = f"integration_test_{uuid.uuid4().hex[:8]}@example.com"
        user_data = CreateUserSchema(
            email=test_email,
            password="integration_password_123"
        )
        
        user = create_user(user_data=user_data, db=db)
        logger.info(f"Created user: {user.email}")
        
        # Test balance operations
        balance = db.query(Balance).filter(Balance.user_id == user.id).first()
        logger.info(f"Initial balance: {balance.amount}")
        
        # Test transaction processing
        transaction_data = CreateTransactionSchema(
            user_id=user.id,
            amount=250.0,
            transaction_type=TransactionType.CREDIT
        )
        
        transaction = create_transaction(transaction_data=transaction_data, db=db)
        logger.info(f"Created transaction: {transaction.id}")
        
        processed_transaction = process_transaction(transaction_id=transaction.id, db=db)
        logger.info(f"Processed transaction status: {processed_transaction.transaction_status}")
        
        # Verify final state
        db.refresh(balance)
        final_balance = balance.amount
        logger.info(f"Final balance: {final_balance}")
        
        # Cleanup
        db.delete(transaction)
        db.delete(balance)
        db.delete(user)
        db.commit()
        
        logger.info("=== Integration Test Completed Successfully ===")
        return True
        
    except Exception as e:
        logger.error(f"Integration test failed: {str(e)}")
        db.rollback()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    # Run integration test when script is executed directly
    success = run_integration_test()
    exit(0 if success else 1)