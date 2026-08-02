#!/usr/bin/env python3
"""
Test runner script for the Instrument Designer project.
"""
import sys
import subprocess
import argparse
from pathlib import Path


def run_tests(
    test_type: str = "all",
    verbose: bool = True,
    coverage: bool = False,
    markers: str = None,
    output_dir: str = None
) -> int:
    """Run tests with specified options."""
    
    cmd = ["python", "-m", "pytest"]
    
    # Test type filtering
    if test_type == "unit":
        cmd.extend(["-m", "unit"])
    elif test_type == "integration":
        cmd.extend(["-m", "integration"])
    elif test_type == "benchmark":
        cmd.extend(["-m", "benchmark"])
    elif test_type == "regression":
        cmd.extend(["-m", "regression"])
    elif test_type == "comparison":
        cmd.extend(["-m", "comparison"])
    elif test_type != "all":
        print(f"Unknown test type: {test_type}")
        return 1
    
    # Verbosity
    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")
    
    # Coverage
    if coverage:
        cmd.extend(["--cov=backend", "--cov=woodwind_designer", "--cov-report=term-missing"])
    
    # Custom markers
    if markers:
        cmd.extend(["-m", markers])
    
    # Output directory for reports
    if output_dir:
        cmd.extend(["--junitxml", f"{output_dir}/junit.xml", "--html", f"{output_dir}/report.html"])
    
    # Run tests
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="Run instrument designer tests")
    parser.add_argument("type", nargs="?", default="all", 
                        choices=["all", "unit", "integration", "benchmark", "regression", "comparison"],
                        help="Type of tests to run")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-q", "--quiet", action="store_true", help="Quiet output")
    parser.add_argument("-c", "--coverage", action="store_true", help="Enable coverage reporting")
    parser.add_argument("-m", "--markers", help="Custom pytest markers")
    parser.add_argument("-o", "--output", help="Output directory for reports")
    parser.add_argument("--list", action="store_true", help="List available tests")
    
    args = parser.parse_args()
    
    if args.list:
        # List available tests
        result = subprocess.run(["python", "-m", "pytest", "--collect-only", "-q"], 
                                cwd=Path(__file__).parent.parent)
        return result.returncode
    
    verbose = args.verbose and not args.quiet
    
    return run_tests(
        test_type=args.type,
        verbose=verbose,
        coverage=args.coverage,
        markers=args.markers,
        output_dir=args.output
    )


if __name__ == "__main__":
    sys.exit(main())