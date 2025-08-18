"""
Integration tests for KCSythEducProject
These tests cover end-to-end functionality
"""
import uuid
import pytest
from database.database import SessionLocal
from database.schema import CreateUserSchema, CreateTransactionSchema
from database.enums import TransactionType, Status
from services.user_service import create_user
from services.transaction_service import create_transaction, process_transaction
from logger_config import get_logger

logger = get_logger(__name__)


@pytest.mark.integration
class TestUserWorkflow:
    """Test complete user workflow from creation to transactions"""
    
    def test_complete_user_workflow(self, db_session):
        """Test complete user workflow: create user, balance, transactions"""
        try:
            logger.info("=== Starting Complete User Workflow Test ===")
            
            # 1. Create test user
            test_email = f"workflow_test_{uuid.uuid4().hex[:8]}@example.com"
            user_data = CreateUserSchema(
                email=test_email,
                password="workflow_password_123"
            )
            
            user = create_user(user_data=user_data, db=db_session)
            logger.info(f"Created user: {user.email}")
            
            # 2. Verify initial state
            from database.models import Balance, Transaction
            
            balance = db_session.query(Balance).filter(Balance.user_id == user.id).first()
            assert balance is not None, "Initial balance should be created"
            assert balance.amount == 100.0, "Initial balance should be 100.0"
            
            initial_transaction = db_session.query(Transaction).filter(
                Transaction.user_id == user.id,
                Transaction.transaction_type == TransactionType.CREDIT,
                Transaction.amount == 100.0
            ).first()
            assert initial_transaction is not None, "Initial transaction should be created"
            assert initial_transaction.transaction_status == Status.DONE, "Initial transaction should be DONE"
            
            logger.info(f"Initial balance: {balance.amount}, Initial transaction: {initial_transaction.id}")
            
            # 3. Create and process multiple transactions
            transaction_amounts = [250.0, 150.0, 300.0]
            created_transactions = []
            
            for amount in transaction_amounts:
                transaction_data = CreateTransactionSchema(
                    user_id=user.id,
                    amount=amount,
                    transaction_type=TransactionType.CREDIT
                )
                
                transaction = create_transaction(transaction_data=transaction_data, db=db_session)
                created_transactions.append(transaction)
                logger.info(f"Created transaction: {transaction.id} with amount: {amount}")
            
            # 4. Process all transactions
            for transaction in created_transactions:
                processed_transaction = process_transaction(transaction_id=transaction.id, db=db_session)
                assert processed_transaction.transaction_status == Status.DONE
                logger.info(f"Processed transaction: {transaction.id}")
            
            # 5. Verify final state
            db_session.refresh(balance)
            final_balance = balance.amount
            
            # Calculate expected balance: 100 (initial) + sum(amounts * 1.2)
            expected_balance = 100.0 + sum(amount * 1.2 for amount in transaction_amounts)
            
            assert final_balance == expected_balance, f"Final balance {final_balance} != expected {expected_balance}"
            
            # Verify all transactions
            all_transactions = db_session.query(Transaction).filter(Transaction.user_id == user.id).all()
            assert len(all_transactions) == 4, f"Expected 4 transactions, got {len(all_transactions)}"
            
            for transaction in all_transactions:
                assert transaction.transaction_status == Status.DONE, f"Transaction {transaction.id} not DONE"
            
            logger.info(f"Final balance: {final_balance}, Total transactions: {len(all_transactions)}")
            logger.info("=== Complete User Workflow Test Passed ===")
            
        except Exception as e:
            logger.error(f"Workflow test failed: {str(e)}")
            raise
        finally:
            # Cleanup
            try:
                for transaction in created_transactions:
                    db_session.delete(transaction)
                db_session.delete(balance)
                db_session.delete(user)
                db_session.commit()
            except Exception as e:
                logger.warning(f"Cleanup failed: {e}")
                db_session.rollback()


@pytest.mark.integration
class TestDatabaseConsistency:
    """Test database consistency and constraints"""
    
    def test_database_relationships_consistency(self, db_session):
        """Test that all database relationships are consistent"""
        try:
            # Create a user
            test_email = f"consistency_test_{uuid.uuid4().hex[:8]}@example.com"
            user_data = CreateUserSchema(
                email=test_email,
                password="consistency_password_123"
            )
            
            user = create_user(user_data=user_data, db=db_session)
            
            # Test all relationships
            from database.models import Balance, Transaction
            
            # User -> Balance
            assert user.balance is not None, "User should have balance"
            assert user.balance.user_id == user.id, "Balance user_id should match user id"
            
            # User -> Transactions
            assert len(user.transactions) >= 1, "User should have at least initial transaction"
            for transaction in user.transactions:
                assert transaction.user_id == user.id, "Transaction user_id should match user id"
            
            # Balance -> User
            balance = user.balance
            assert balance.user is not None, "Balance should have user"
            assert balance.user.id == user.id, "Balance user should match user"
            
            # Transaction -> User
            for transaction in user.transactions:
                assert transaction.user is not None, "Transaction should have user"
                assert transaction.user.id == user.id, "Transaction user should match user"
            
            logger.info("=== Database Relationships Consistency Test Passed ===")
            
        except Exception as e:
            logger.error(f"Database consistency test failed: {str(e)}")
            raise
        finally:
            # Cleanup
            try:
                db_session.delete(user)
                db_session.commit()
            except Exception as e:
                logger.warning(f"Cleanup failed: {e}")
                db_session.rollback()


def run_standalone_integration_test():
    """
    Run integration test when script is executed directly
    This function can be called for manual testing
    """
    db = SessionLocal()
    
    try:
        logger.info("=== Starting Standalone Integration Test ===")
        
        # Create test user
        test_email = f"standalone_test_{uuid.uuid4().hex[:8]}@example.com"
        user_data = CreateUserSchema(
            email=test_email,
            password="standalone_password_123"
        )
        
        user = create_user(user_data=user_data, db=db)
        logger.info(f"Created user: {user.email}")
        
        # Test balance operations
        from database.models import Balance
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
        
        logger.info("=== Standalone Integration Test Completed Successfully ===")
        return True
        
    except Exception as e:
        logger.error(f"Standalone integration test failed: {str(e)}")
        db.rollback()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    # Run integration test when script is executed directly
    success = run_standalone_integration_test()
    exit(0 if success else 1)
