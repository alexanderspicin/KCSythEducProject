"""
Tests for transaction processing functionality
"""
import pytest
from database.models import Balance, Transaction
from database.schema import CreateTransactionSchema
from database.enums import TransactionType, Status
from services.transaction_service import create_transaction, process_transaction


class TestTransactionProcessing:
    """Test transaction processing functionality"""
    
    def test_create_credit_transaction(self, db_session, test_user_with_balance):
        """Test creating a credit transaction"""
        transaction_data = CreateTransactionSchema(
            user_id=test_user_with_balance.id,
            amount=500.0,
            transaction_type=TransactionType.CREDIT
        )
        
        transaction = create_transaction(transaction_data=transaction_data, db=db_session)
        
        assert transaction is not None
        assert transaction.amount == 500.0
        assert transaction.transaction_type == TransactionType.CREDIT
        assert transaction.transaction_status == Status.PROCESSING
        assert transaction.user_id == test_user_with_balance.id
    
    def test_process_transaction_success(self, db_session, test_user_with_balance):
        """Test successful transaction processing"""
        # Create a transaction first
        transaction_data = CreateTransactionSchema(
            user_id=test_user_with_balance.id,
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
            Balance.user_id == test_user_with_balance.id
        ).first()
        
        # Expected: 100 (initial) + 300*1.2 (exchange rate) = 460
        expected_balance = 100.0 + (300.0 * 1.2)
        assert user_balance.amount == expected_balance
    
    def test_multiple_transactions(self, db_session, test_user_with_balance):
        """Test processing multiple transactions"""
        transactions = []
        amounts = [100.0, 200.0, 150.0]
        
        # Create multiple transactions
        for amount in amounts:
            transaction_data = CreateTransactionSchema(
                user_id=test_user_with_balance.id,
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
            Balance.user_id == test_user_with_balance.id
        ).first()
        
        # Expected: 100 (initial) + sum(amounts * 1.2)
        expected_balance = 100.0 + sum(amount * 1.2 for amount in amounts)
        assert user_balance.amount == expected_balance
        
        # Verify all transactions are processed
        all_transactions = db_session.query(Transaction).filter(
            Transaction.user_id == test_user_with_balance.id
        ).all()
        
        assert len(all_transactions) == 4  # 1 initial + 3 new
        for transaction in all_transactions:
            assert transaction.transaction_status == Status.DONE
    
    def test_transaction_user_relationship(self, db_session, test_user_with_balance):
        """Test transaction-user relationship"""
        # Create a transaction
        transaction_data = CreateTransactionSchema(
            user_id=test_user_with_balance.id,
            amount=100.0,
            transaction_type=TransactionType.CREDIT
        )
        create_transaction(transaction_data=transaction_data, db=db_session)
        
        # Test relationship
        assert len(test_user_with_balance.transactions) >= 2  # Initial + new transaction
        
        for transaction in test_user_with_balance.transactions:
            assert transaction.user_id == test_user_with_balance.id


class TestTransactionValidation:
    """Test transaction validation and error handling"""
    
    def test_invalid_user_id(self, db_session):
        """Test handling of invalid user ID"""
        import uuid
        invalid_user_id = uuid.uuid4()
        
        transaction_data = CreateTransactionSchema(
            user_id=invalid_user_id,
            amount=100.0,
            transaction_type=TransactionType.CREDIT
        )
        
        # This should handle the case gracefully
        with pytest.raises(Exception):
            create_transaction(transaction_data=transaction_data, db=db_session)
    
    def test_invalid_transaction_amount(self, db_session, test_user_with_balance):
        """Test handling of invalid transaction amounts"""
        invalid_amounts = [-100.0, 0.0]
        
        for amount in invalid_amounts:
            transaction_data = CreateTransactionSchema(
                user_id=test_user_with_balance.id,
                amount=amount,
                transaction_type=TransactionType.CREDIT
            )
            
            # Should handle invalid amounts appropriately
            with pytest.raises(Exception):
                create_transaction(transaction_data=transaction_data, db=db_session)
    
    def test_process_nonexistent_transaction(self, db_session):
        """Test processing a transaction that doesn't exist"""
        import uuid
        nonexistent_id = uuid.uuid4()
        
        with pytest.raises(Exception):
            process_transaction(transaction_id=nonexistent_id, db=db_session)
