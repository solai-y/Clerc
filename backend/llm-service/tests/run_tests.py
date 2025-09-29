#!/usr/bin/env python3
"""
Test runner script for LLM service tests
"""
import subprocess
import sys
import os
import argparse


def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.stdout:
        print("STDOUT:")
        print(result.stdout)
    
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    
    if result.returncode != 0:
        print(f"❌ {description} failed with return code {result.returncode}")
        return False
    else:
        print(f"✅ {description} passed")
        return True


def main():
    parser = argparse.ArgumentParser(description="Run LLM service tests")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--e2e", action="store_true", help="Run e2e tests only")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--install", action="store_true", help="Install test dependencies")
    parser.add_argument("--coverage", action="store_true", help="Run with coverage reporting")
    
    args = parser.parse_args()
    
    # Change to test directory
    test_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(test_dir)
    
    success = True
    
    # Install dependencies if requested
    if args.install:
        success &= run_command(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            "Installing test dependencies"
        )
        if not success:
            return 1
    
    # Determine which tests to run
    test_commands = []
    
    if args.unit or args.all:
        cmd = [sys.executable, "-m", "pytest", "unit/", "-m", "unit"]
        if args.coverage:
            cmd.extend(["--cov=../", "--cov-report=html", "--cov-report=term"])
        test_commands.append((cmd, "Unit Tests"))
    
    if args.integration or args.all:
        cmd = [sys.executable, "-m", "pytest", "integration/", "-m", "integration"]
        if args.coverage:
            cmd.extend(["--cov=../", "--cov-report=html", "--cov-report=term", "--cov-append"])
        test_commands.append((cmd, "Integration Tests"))
    
    if args.e2e or args.all:
        cmd = [sys.executable, "-m", "pytest", "e2e/", "-m", "e2e"]
        test_commands.append((cmd, "End-to-End Tests"))
    
    # If no specific test type specified, run all
    if not any([args.unit, args.integration, args.e2e, args.all]):
        cmd = [sys.executable, "-m", "pytest", "."]
        if args.coverage:
            cmd.extend(["--cov=../", "--cov-report=html", "--cov-report=term"])
        test_commands.append((cmd, "All Tests"))
    
    # Run the tests
    for cmd, description in test_commands:
        success &= run_command(cmd, description)
    
    if success:
        print(f"\n{'='*60}")
        print("🎉 All tests passed!")
        print(f"{'='*60}")
        return 0
    else:
        print(f"\n{'='*60}")
        print("❌ Some tests failed!")
        print(f"{'='*60}")
        return 1


if __name__ == "__main__":
    sys.exit(main())