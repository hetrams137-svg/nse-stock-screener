"""
AI Code Debugger & Test Runner
--------------------------------
A reproducible workflow that takes source code + test cases, runs the code,
captures errors, and compares actual vs expected output. Designed to help
identify syntax, runtime, and logical issues with clear, structured
error reports.

Author: Dorilal Pandey
"""

import subprocess
import sys
import tempfile
import os


class TestResult:
    def __init__(self, test_name, passed, expected=None, actual=None, error=None):
        self.test_name = test_name
        self.passed = passed
        self.expected = expected
        self.actual = actual
        self.error = error

    def __str__(self):
        if self.passed:
            return f"[PASS] {self.test_name}"
        if self.error:
            return f"[ERROR] {self.test_name} -> {self.error}"
        return (
            f"[FAIL] {self.test_name} "
            f"(expected={self.expected!r}, actual={self.actual!r})"
        )


def run_code(code: str, input_data: str = "") -> tuple[str, str, int]:
    """
    Runs a Python code snippet in an isolated subprocess.
    Returns (stdout, stderr, return_code).
    """
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False
    ) as tmp_file:
        tmp_file.write(code)
        tmp_path = tmp_file.name

    try:
        result = subprocess.run(
            [sys.executable, tmp_path],
            input=input_data,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", "Execution timed out (possible infinite loop)", -1
    finally:
        os.remove(tmp_path)


def run_test_cases(code: str, test_cases: list[dict]) -> list[TestResult]:
    """
    test_cases: list of dicts like:
        {"name": "basic_add", "input": "2 3", "expected": "5"}
    """
    results = []

    for case in test_cases:
        stdout, stderr, return_code = run_code(code, case.get("input", ""))

        if return_code != 0:
            results.append(
                TestResult(case["name"], passed=False, error=stderr.strip())
            )
            continue

        actual_output = stdout.strip()
        expected_output = str(case.get("expected", "")).strip()
        passed = actual_output == expected_output

        results.append(
            TestResult(
                case["name"],
                passed=passed,
                expected=expected_output,
                actual=actual_output,
            )
        )

    return results


def print_report(results: list[TestResult]):
    passed_count = sum(1 for r in results if r.passed)
    total = len(results)

    print("\nTest Report")
    print("-" * 40)
    for r in results:
        print(r)
    print("-" * 40)
    print(f"{passed_count}/{total} tests passed\n")


if __name__ == "__main__":
    # Example: code under test reads two integers and prints their sum
    sample_code = """
a, b = map(int, input().split())
print(a + b)
"""

    sample_tests = [
        {"name": "positive_numbers", "input": "2 3", "expected": "5"},
        {"name": "negative_numbers", "input": "-2 3", "expected": "1"},
        {"name": "zeros", "input": "0 0", "expected": "0"},
        {"name": "wrong_expectation_demo", "input": "10 10", "expected": "21"},
    ]

    results = run_test_cases(sample_code, sample_tests)
    print_report(results)
