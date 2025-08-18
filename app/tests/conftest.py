"""
Pytest configuration and fixtures for KCSythEducProject tests
"""
import os
import uuid
import pytest
from sqlalchemy.orm import Session

# Set test environment variables before importing database modules
os.environ.setdefault('POSTGRES_USER', 'test_user')
os.environ.setdefault('POSTGRES_PASSWORD', 'test_password')
os.environ.setdefault('POSTGRES_HOST', 'localhost')
os.environ.setdefault('POSTGRES_PORT', '5432')
os.environ.setdefault('POSTGRES_DB', 'test_db')

from database.database import SessionLocal
from database.models import Users
from database.schema import CreateUserSchema
from services.user_service import create_user
from logger_config import setup_logging, get_logger

# Setup logging for tests
setup_logging(log_level="INFO", log_to_file=False)
logger = get_logger(__name__)


@pytest.fixture(scope="function")
def db_session():
    """Provide a database session for testing"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def test_user_data():
    """Provide test user data"""
    return {
        "email": f"test_user_{uuid.uuid4().hex[:8]}@example.com",
        "password": "test_password_123"
    }


@pytest.fixture(scope="function")
def test_user(db_session, test_user_data):
    """Create and return a test user"""
    user_data = CreateUserSchema(**test_user_data)
    user = create_user(user_data=user_data, db=db_session)
    db_session.commit()
    
    # Cleanup after test
    yield user
    
    # Cleanup
    try:
        db_session.delete(user)
        db_session.commit()
    except Exception as e:
        logger.warning(f"Failed to cleanup test user: {e}")
        db_session.rollback()


@pytest.fixture(scope="function")
def test_user_with_balance(db_session, test_user_data):
    """Create and return a test user with initial balance"""
    user_data = CreateUserSchema(**test_user_data)
    user = create_user(user_data=user_data, db=db_session)
    db_session.commit()
    
    # Verify balance was created
    from database.models import Balance
    balance = db_session.query(Balance).filter(Balance.user_id == user.id).first()
    assert balance is not None, "Initial balance should be created with user"
    
    yield user
    
    # Cleanup
    try:
        db_session.delete(user)
        db_session.commit()
    except Exception as e:
        logger.warning(f"Failed to cleanup test user with balance: {e}")
        db_session.rollback()


@pytest.fixture(scope="function")
def sample_transaction_data(test_user):
    """Provide sample transaction data for testing"""
    return {
        "user_id": test_user.id,
        "amount": 100.0,
        "transaction_type": "CREDIT"
    }
