@echo off
REM Quick test runner for Windows
REM Usage:
REM   test.cmd              - Run all tests
REM   test.cmd -v           - Verbose output
REM   test.cmd -m buff_ui   - Run only buff_ui tests
REM   test.cmd --help       - Show all options

uv run python run_tests.py %*
