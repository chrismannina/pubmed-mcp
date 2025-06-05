#!/usr/bin/env python3
"""
Test runner for PubMed MCP Server.

This script provides a convenient way to run tests with different configurations.
"""

import subprocess
import sys


def run_command(cmd: list[str]) -> int:
    """Run a command and return the exit code."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    return result.returncode


def main() -> None:
    """Main test runner."""
    if len(sys.argv) < 2:
        print("Usage: python run_tests.py [unit|integration|all|coverage]")
        sys.exit(1)

    test_type = sys.argv[1]

    print(f"Running tests with Python {sys.version_info.major}." f"{sys.version_info.minor}...")

    # Run pytest with proper configuration
    pytest_cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-v",
        "--tb=short",
        "--strict-markers",
    ]

    if test_type == "unit":
        pytest_cmd.extend(["tests/", "-m", "unit"])
    elif test_type == "integration":
        pytest_cmd.extend(["tests/", "-m", "integration"])
    elif test_type == "all":
        pytest_cmd.extend(["tests/"])
    elif test_type == "coverage":
        pytest_cmd.extend(
            [
                "--cov=src",
                "--cov-report=html",
                "--cov-report=term-missing",
            ]
        )
    else:
        print(f"Unknown test type: {test_type}")
        sys.exit(1)

    exit_code = run_command(pytest_cmd)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
