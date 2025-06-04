#!/usr/bin/env python3
"""
Test runner for PubMed MCP Server.
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path

def run_tests(
    test_pattern: str = None,
    coverage: bool = False,
    verbose: bool = True,
    parallel: bool = False,
    markers: str = None
):
    """
    Run tests with various options.
    
    Args:
        test_pattern: Specific test pattern to run (e.g., "test_utils.py")
        coverage: Generate coverage report
        verbose: Run in verbose mode
        parallel: Run tests in parallel
        markers: Pytest markers to use (e.g., "not slow")
    """
    # Ensure we're in the right directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Build pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add test pattern if specified
    if test_pattern:
        cmd.append(f"tests/{test_pattern}")
    else:
        cmd.append("tests/")
    
    # Add options
    if verbose:
        cmd.extend(["-v", "--tb=short"])
    
    if coverage:
        cmd.extend([
            "--cov=src",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-fail-under=70"
        ])
    
    if parallel:
        cmd.extend(["-n", "auto"])  # Requires pytest-xdist
    
    if markers:
        cmd.extend(["-m", markers])
    
    # Add color output
    cmd.extend(["--color=yes"])
    
    print(f"Running command: {' '.join(cmd)}")
    print("-" * 50)
    
    # Run tests
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\nTests interrupted by user.")
        return 130
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1

def main():
    """Main function to parse arguments and run tests."""
    parser = argparse.ArgumentParser(description="Run PubMed MCP Server tests")
    
    parser.add_argument(
        "pattern",
        nargs="?",
        help="Test pattern to run (e.g., test_utils.py, test_pubmed_client.py::TestPubMedClient::test_client_initialization)"
    )
    
    parser.add_argument(
        "--coverage", "-c",
        action="store_true",
        help="Generate coverage report"
    )
    
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Run in quiet mode"
    )
    
    parser.add_argument(
        "--parallel", "-p",
        action="store_true",
        help="Run tests in parallel (requires pytest-xdist)"
    )
    
    parser.add_argument(
        "--markers", "-m",
        help="Pytest markers to use (e.g., 'not slow', 'unit')"
    )
    
    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="Install test dependencies before running tests"
    )
    
    args = parser.parse_args()
    
    # Install dependencies if requested
    if args.install_deps:
        print("Installing test dependencies...")
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], check=True)
        print("Dependencies installed.\n")
    
    # Check if pytest is available
    try:
        subprocess.run([sys.executable, "-m", "pytest", "--version"], 
                      check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("ERROR: pytest is not installed. Please install it first:")
        print("pip install pytest pytest-asyncio pytest-mock")
        return 1
    
    # Run tests
    return run_tests(
        test_pattern=args.pattern,
        coverage=args.coverage,
        verbose=not args.quiet,
        parallel=args.parallel,
        markers=args.markers
    )

if __name__ == "__main__":
    sys.exit(main()) 