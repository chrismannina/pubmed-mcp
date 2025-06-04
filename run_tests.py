#!/usr/bin/env python3
"""
Test runner for PubMed MCP Server.

This script provides a convenient way to run tests with different configurations.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str]) -> int:
    """Run a command and return the exit code."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    return result.returncode


def main():
    """Main test runner."""
    if len(sys.argv) < 2:
        print("Usage: python run_tests.py [unit|integration|all|coverage]")
        sys.exit(1)

    test_type = sys.argv[1]

    if test_type == "unit":
        exit_code = run_command(["python", "-m", "pytest", "tests/", "-m", "unit", "-v"])
    elif test_type == "integration":
        exit_code = run_command(["python", "-m", "pytest", "tests/", "-m", "integration", "-v"])
    elif test_type == "all":
        exit_code = run_command(["python", "-m", "pytest", "tests/", "-v"])
    elif test_type == "coverage":
        exit_code = run_command(
            [
                "python",
                "-m",
                "pytest",
                "tests/",
                "--cov=src",
                "--cov-report=html",
                "--cov-report=term-missing",
                "-v",
            ]
        )
    else:
        print(f"Unknown test type: {test_type}")
        sys.exit(1)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
