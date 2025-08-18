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
        from tests import run_integration_test
        success = run_integration_test()
        if success:
            print("✅ Integration test passed!")
            return True
        else:
            print("❌ Integration test failed!")
            return False
    except Exception as e:
        print(f"❌ Error running integration test: {e}")
        return False

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
    
    args = parser.parse_args()
    
    if args.integration_only:
        success = run_integration_test()
        sys.exit(0 if success else 1)
    
    success = run_pytest_tests(args.type, args.verbose)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
