# Testing Guide for KCSythEducProject

This document explains how to use the comprehensive test suite for the KCSythEducProject application.

## Overview

The test suite covers:
- **User Creation**: Testing user registration and validation
- **Balance Operations**: Testing balance creation and management
- **Transaction Processing**: Testing transaction creation and processing
- **Database Relationships**: Testing ORM relationships and constraints
- **API Endpoints**: Testing FastAPI endpoints
- **Error Handling**: Testing edge cases and error scenarios

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
```

### Option 2: Using pytest directly

```bash
# Run all tests
python -m pytest

# Run with verbose output
python -m pytest -v

# Run specific test class
python -m pytest tests.py::TestUserCreation

# Run specific test method
python -m pytest tests.py::TestUserCreation::test_create_user_success

# Run tests matching a pattern
python -m pytest -k "user"

# Run tests excluding slow ones
python -m pytest -m "not slow"
```

### Option 3: Run tests directly

```bash
# Run the integration test directly
python tests.py
```

## Test Structure

### Test Classes

1. **TestUserCreation**: Tests user creation functionality
   - `test_create_user_success`: Tests successful user creation
   - `test_create_user_duplicate_email`: Tests duplicate email handling

2. **TestBalanceOperations**: Tests balance-related operations
   - `test_initial_balance_creation`: Tests initial balance creation
   - `test_initial_transaction_creation`: Tests initial transaction creation

3. **TestTransactionProcessing**: Tests transaction processing
   - `test_create_credit_transaction`: Tests transaction creation
   - `test_process_transaction_success`: Tests transaction processing
   - `test_multiple_transactions`: Tests multiple transaction handling

4. **TestDatabaseRelationships**: Tests database relationships
   - `test_user_balance_relationship`: Tests user-balance relationships
   - `test_user_transactions_relationship`: Tests user-transaction relationships

5. **TestAPIEndpoints**: Tests FastAPI endpoints
   - `test_health_check`: Tests health check endpoint

6. **TestErrorHandling**: Tests error scenarios
   - `test_invalid_user_id`: Tests invalid user ID handling
   - `test_invalid_transaction_amount`: Tests invalid amount handling

### Test Fixtures

- `db_session`: Provides a database session for testing
- `test_user_data`: Provides test user data
- `test_user`: Creates and provides a test user

## Test Markers

Tests can be marked with categories:

- `@pytest.mark.unit`: Unit tests (fast, isolated)
- `@pytest.mark.integration`: Integration tests (slower, require database)
- `@pytest.mark.slow`: Slow tests that can be excluded

## Configuration

The `pytest.ini` file configures:
- Test discovery patterns
- Default options
- Warning filters
- Custom markers

## Best Practices

1. **Isolation**: Each test should be independent and not rely on other tests
2. **Cleanup**: Tests should clean up after themselves
3. **Fixtures**: Use fixtures for common setup and teardown
4. **Assertions**: Use descriptive assertion messages
5. **Naming**: Test names should clearly describe what they test

## Troubleshooting

### Common Issues

1. **Database Connection**: Ensure your database is running and accessible
2. **Import Errors**: Make sure all required modules are installed
3. **Test Discovery**: Check that test files follow the naming convention

### Debug Mode

Run tests with more verbose output:

```bash
python -m pytest -v -s --tb=long
```

### Running Single Tests

To debug a specific test:

```bash
python -m pytest tests.py::TestUserCreation::test_create_user_success -v -s
```

## Continuous Integration

The test suite is designed to work with CI/CD pipelines. Tests can be run automatically on:
- Code commits
- Pull requests
- Scheduled intervals

## Contributing

When adding new tests:
1. Follow the existing naming conventions
2. Use appropriate test markers
3. Ensure tests are isolated and clean
4. Add proper documentation
5. Include both positive and negative test cases
