"""
Tests for user creation functionality
"""
import pytest
from database.models import Users
from database.schema import CreateUserSchema
from services.user_service import create_user


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
    
    def test_create_user_invalid_email(self, db_session):
        """Test user creation with invalid email format"""
        invalid_emails = ["", "invalid-email", "@example.com", "user@"]
        
        for invalid_email in invalid_emails:
            user_data = CreateUserSchema(
                email=invalid_email,
                password="valid_password"
            )
            
            # Should handle invalid email appropriately
            with pytest.raises(Exception):
                create_user(user_data=user_data, db=db_session)
    
    def test_create_user_short_password(self, db_session):
        """Test user creation with short password"""
        user_data = CreateUserSchema(
            email="test@example.com",
            password="123"  # Too short
        )
        
        # Should handle short password appropriately
        with pytest.raises(Exception):
            create_user(user_data=user_data, db=db_session)
