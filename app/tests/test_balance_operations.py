"""
Tests for balance-related operations
"""
import pytest
from database.models import Balance, Transaction
from database.enums import TransactionType, Status


class TestBalanceOperations:
    """Test balance-related operations"""
    
    def test_initial_balance_creation(self, db_session, test_user_with_balance):
        """Test that initial balance is created with user"""
        user_balance = db_session.query(Balance).filter(
            Balance.user_id == test_user_with_balance.id
        ).first()
        
        assert user_balance is not None
        assert user_balance.amount == 100.0  # Initial balance
        assert user_balance.user_id == test_user_with_balance.id
    
    def test_initial_transaction_creation(self, db_session, test_user_with_balance):
        """Test that initial transaction is created with user"""
        initial_transaction = db_session.query(Transaction).filter(
            Transaction.user_id == test_user_with_balance.id,
            Transaction.transaction_type == TransactionType.CREDIT,
            Transaction.amount == 100.0
        ).first()
        
        assert initial_transaction is not None
        assert initial_transaction.transaction_status == Status.DONE
        assert initial_transaction.user_id == test_user_with_balance.id
    
    def test_balance_user_relationship(self, db_session, test_user_with_balance):
        """Test balance-user relationship"""
        user_balance = db_session.query(Balance).filter(
            Balance.user_id == test_user_with_balance.id
        ).first()
        
        # Test forward relationship
        assert test_user_with_balance.balance is not None
        assert test_user_with_balance.balance.amount == user_balance.amount
        
        # Test reverse relationship
        assert user_balance.user is not None
        assert user_balance.user.email == test_user_with_balance.email
    
    def test_balance_consistency(self, db_session, test_user_with_balance):
        """Test that balance is consistent across queries"""
        balance1 = db_session.query(Balance).filter(
            Balance.user_id == test_user_with_balance.id
        ).first()
        
        balance2 = db_session.query(Balance).filter(
            Balance.user_id == test_user_with_balance.id
        ).first()
        
        assert balance1.amount == balance2.amount
        assert balance1.id == balance2.id
