# Testing Guide for KCSythEducProject

This document explains how to use the comprehensive test suite for the KCSythEducProject application.

## Project Structure

```
app/
├── tests/                    # Test package
│   ├── __init__.py          # Package initialization
│   ├── conftest.py          # Pytest fixtures and configuration
│   ├── test_user_creation.py    # User creation tests
│   ├── test_balance_operations.py # Balance operation tests
│   ├── test_transactions.py      # Transaction processing tests
│   ├── test_api.py              # API endpoint tests
│   └── test_integration.py      # Integration tests
├── pytest.ini              # Pytest configuration
├── run_tests.py            # Test runner script
└── TESTING.md              # This file
```

## Overview

The test suite covers:
- **User Creation**: Testing user registration and validation
- **Balance Operations**: Testing balance creation and management
- **Transaction Processing**: Testing transaction creation and processing
- **Database Relationships**: Testing ORM relationships and constraints
- **API Endpoints**: Testing FastAPI endpoints
- **Error Handling**: Testing edge cases and error scenarios
- **Integration**: End-to-end workflow testing

## Prerequisites

Install the required testing dependencies:

```bash
pip install -r requirements.txt
```

## Running Tests

### Option 1: Using the Test Runner Script (Recommended)

```bash
# Run all tests
python run_tests.py

# Run only unit tests
python run_tests.py --type unit

# Run only integration tests
python run_tests.py --type integration

# Run fast tests (exclude slow ones)
python run_tests.py --type fast

# Run with verbose output
python run_tests.py --verbose

# Run only the integration test
python run_tests.py --integration-only

# List available test files
python run_tests.py --list

# Run a specific test file
python run_tests.py --test test_user_creation
```

### Option 2: Using pytest directly

```bash
# Run all tests
python -m pytest

# Run with verbose output
python -m pytest -v

# Run specific test file
python -m pytest tests/test_user_creation.py

# Run specific test class
python -m pytest tests/test_user_creation.py::TestUserCreation

# Run specific test method
python -m pytest tests/test_user_creation.py::TestUserCreation::test_create_user_success

# Run tests matching a pattern
python -m pytest -k "user"

# Run tests excluding slow ones
python -m pytest -m "not slow"

# Run only integration tests
python -m pytest -m integration
```

### Option 3: Run tests directly

```bash
# Run the integration test directly
python tests/test_integration.py
```

## Test Structure

### Test Files

1. **`test_user_creation.py`**: Tests user creation functionality
   - `TestUserCreation.test_create_user_success`: Tests successful user creation
   - `TestUserCreation.test_create_user_duplicate_email`: Tests duplicate email handling
   - `TestUserCreation.test_create_user_invalid_email`: Tests invalid email validation
   - `TestUserCreation.test_create_user_short_password`: Tests password validation

2. **`test_balance_operations.py`**: Tests balance-related operations
   - `TestBalanceOperations.test_initial_balance_creation`: Tests initial balance creation
   - `TestBalanceOperations.test_initial_transaction_creation`: Tests initial transaction creation
   - `TestBalanceOperations.test_balance_user_relationship`: Tests user-balance relationships
   - `TestBalanceOperations.test_balance_consistency`: Tests balance consistency

3. **`test_transactions.py`**: Tests transaction processing
   - `TestTransactionProcessing.test_create_credit_transaction`: Tests transaction creation
   - `TestTransactionProcessing.test_process_transaction_success`: Tests transaction processing
   - `TestTransactionProcessing.test_multiple_transactions`: Tests multiple transaction handling
   - `TestTransactionValidation.test_invalid_user_id`: Tests invalid user ID handling
   - `TestTransactionValidation.test_invalid_transaction_amount`: Tests invalid amount handling

4. **`test_api.py`**: Tests FastAPI endpoints
   - `TestAPIEndpoints.test_health_check`: Tests health check endpoint
   - `TestAPIEndpoints.test_health_check_response_format`: Tests response format
   - `TestAPIEndpoints.test_health_check_methods`: Tests HTTP methods
   - `TestAPIEndpoints.test_nonexistent_endpoint`: Tests 404 handling

5. **`test_integration.py`**: Integration tests
   - `TestUserWorkflow.test_complete_user_workflow`: Tests complete user workflow
   - `TestDatabaseConsistency.test_database_relationships_consistency`: Tests database consistency

### Test Fixtures (`conftest.py`)

- `db_session`: Provides a database session for testing
- `test_user_data`: Provides test user data
- `test_user`: Creates and provides a test user
- `test_user_with_balance`: Creates and provides a test user with initial balance
- `sample_transaction_data`: Provides sample transaction data

## Test Markers

Tests can be marked with categories:

- `@pytest.mark.unit`: Unit tests (fast, isolated)
- `@pytest.mark.integration`: Integration tests (slower, require database)
- `@pytest.mark.slow`: Slow tests that can be excluded

## Configuration

The `pytest.ini` file configures:
- Test discovery patterns (looks in `tests/` directory)
- Default options
- Warning filters
- Custom markers

## Best Practices

1. **Isolation**: Each test should be independent and not rely on other tests
2. **Cleanup**: Tests should clean up after themselves using fixtures
3. **Fixtures**: Use fixtures for common setup and teardown
4. **Assertions**: Use descriptive assertion messages
5. **Naming**: Test names should clearly describe what they test
6. **Organization**: Group related tests in separate files

## Troubleshooting

### Common Issues

1. **Database Connection**: Ensure your database is running and accessible
2. **Import Errors**: Make sure all required modules are installed
3. **Test Discovery**: Check that test files follow the naming convention (`test_*.py`)

### Debug Mode

Run tests with more verbose output:

```bash
python -m pytest -v -s --tb=long
```

### Running Single Tests

To debug a specific test:

```bash
python -m pytest tests/test_user_creation.py::TestUserCreation::test_create_user_success -v -s
```

### Test Organization

- **Unit Tests**: Fast, isolated tests in separate files
- **Integration Tests**: Slower tests that test complete workflows
- **Fixtures**: Shared in `conftest.py` for reuse across test files

## Continuous Integration

The test suite is designed to work with CI/CD pipelines. Tests can be run automatically on:
- Code commits
- Pull requests
- Scheduled intervals

## Contributing

When adding new tests:
1. Follow the existing naming conventions (`test_*.py`)
2. Use appropriate test markers
3. Ensure tests are isolated and clean
4. Add proper documentation
5. Include both positive and negative test cases
6. Place fixtures in `conftest.py` if they're used by multiple test files
