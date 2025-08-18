#!/usr/bin/env python3
"""
Test runner script for KCSythEducProject
Provides easy ways to run different types of tests
"""
import sys
import subprocess
import argparse
from pathlib import Path

def run_pytest_tests(test_type="all", verbose=False):
    """Run pytest tests with specified options"""
    cmd = ["python", "-m", "pytest"]
    
    if verbose:
        cmd.append("-v")
    
    if test_type == "unit":
        cmd.extend(["-m", "unit"])
    elif test_type == "integration":
        cmd.extend(["-m", "integration"])
    elif test_type == "fast":
        cmd.extend(["-m", "not slow"])
    
    print(f"Running tests with command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent, check=True)
        print("✅ All tests passed!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Tests failed with exit code: {e.returncode}")
        return False

def run_integration_test():
    """Run the integration test directly"""
    print("Running integration test...")
    try:
        from tests.test_integration import run_standalone_integration_test
        success = run_standalone_integration_test()
        if success:
            print("✅ Integration test passed!")
            return True
        else:
            print("❌ Integration test failed!")
            return False
    except Exception as e:
        print(f"❌ Error running integration test: {e}")
        return False

def run_specific_test(test_name):
    """Run a specific test file or test class"""
    # Add .py extension if not present
    if not test_name.endswith('.py'):
        test_name = f"{test_name}.py"
    
    cmd = ["python", "-m", "pytest", f"tests/{test_name}"]
    print(f"Running specific test: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent, check=True)
        print("✅ Test passed!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Test failed with exit code: {e.returncode}")
        return False

def list_available_tests():
    """List all available test files"""
    tests_dir = Path(__file__).parent / "tests"
    test_files = list(tests_dir.glob("test_*.py"))
    
    print("Available test files:")
    for test_file in test_files:
        print(f"  - {test_file.stem}")
    
    print("\nTest categories:")
    print("  - test_user_creation.py: User creation tests")
    print("  - test_balance_operations.py: Balance operation tests")
    print("  - test_transactions.py: Transaction processing tests")
    print("  - test_api.py: API endpoint tests")
    print("  - test_integration.py: Integration tests")

def main():
    parser = argparse.ArgumentParser(description="Run tests for KCSythEducProject")
    parser.add_argument(
        "--type", 
        choices=["all", "unit", "integration", "fast"],
        default="all",
        help="Type of tests to run"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--integration-only",
        action="store_true",
        help="Run only the integration test"
    )
    parser.add_argument(
        "--test", "-t",
        help="Run a specific test file (e.g., test_user_creation)"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List available test files"
    )
    
    args = parser.parse_args()
    
    if args.list:
        list_available_tests()
        return
    
    if args.test:
        success = run_specific_test(args.test)
        sys.exit(0 if success else 1)
    
    if args.integration_only:
        success = run_integration_test()
        sys.exit(0 if success else 1)
    
    success = run_pytest_tests(args.type, args.verbose)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
