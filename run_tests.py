#!/usr/bin/env python
"""Test runner script for asset-extractor integration tests.

This script provides convenient ways to run the test suite with various options.
"""

import argparse
import subprocess
import sys


def main():
    """Run tests with specified options."""
    parser = argparse.ArgumentParser(description="Run asset-extractor integration tests")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Verbose output (shows individual test names)"
    )
    parser.add_argument("-vv", "--very-verbose", action="store_true", help="Very verbose output (shows test details)")
    parser.add_argument(
        "-m",
        "--marker",
        type=str,
        help="Run only tests with specified marker (buff_ui, pool, mapping, etc.)",
    )
    parser.add_argument(
        "-k",
        "--keyword",
        type=str,
        help="Run only tests matching the keyword expression",
    )
    parser.add_argument(
        "--list-markers",
        action="store_true",
        help="List all available test markers",
    )
    parser.add_argument(
        "-x",
        "--exitfirst",
        action="store_true",
        help="Exit on first test failure",
    )
    parser.add_argument(
        "--no-summary",
        action="store_true",
        help="Don't show test summary",
    )
    parser.add_argument(
        "test_files",
        nargs="*",
        help="Specific test files or directories to run",
    )

    args = parser.parse_args()

    # Build pytest command
    cmd = ["pytest"]

    # Add verbosity
    if args.very_verbose:
        cmd.append("-vv")
    elif args.verbose:
        cmd.append("-v")

    # Add marker filter
    if args.marker:
        cmd.extend(["-m", args.marker])

    # Add keyword filter
    if args.keyword:
        cmd.extend(["-k", args.keyword])

    # List markers
    if args.list_markers:
        cmd.append("--markers")

    # Exit on first failure
    if args.exitfirst:
        cmd.append("-x")

    # No summary
    if args.no_summary:
        cmd.append("--tb=no")

    # Add test files/directories
    if args.test_files:
        cmd.extend(args.test_files)
    else:
        cmd.append("tests/integration")

    # Run pytest
    print(f"Running: {' '.join(cmd)}")
    print("-" * 80)

    result = subprocess.run(cmd)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
