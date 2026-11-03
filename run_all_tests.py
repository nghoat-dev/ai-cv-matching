"""
Master Test & Verification Runner for AI CV-Job Matching System.
Executes the full test suite across Sprints 1, 2, and 3.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent
PYTHON_EXE = sys.executable


def run_step(title: str, cmd: list[str]) -> bool:
    print("\n" + "=" * 65)
    print(f"  RUNNING: {title}")
    print("=" * 65)
    res = subprocess.run(cmd, cwd=str(_PROJECT_ROOT))
    if res.returncode == 0:
        print(f"--> [PASS] {title}")
        return True
    else:
        print(f"--> [FAIL] {title} (Exit Code: {res.returncode})")
        return False


def main():
    print("=" * 65)
    print("      AI CV-JOB MATCHING — MASTER TEST SUITE (SPRINTS 1-3)")
    print("=" * 65)

    steps = [
        (
            "1. Environment & Dependencies Verification",
            [PYTHON_EXE, "backend/verify_env.py"],
        ),
        (
            "2. ML Pipeline Unit Tests (Cleaning, Preprocessing, Features)",
            [PYTHON_EXE, "ml_pipeline/tests/test_pipeline_unit.py"],
        ),
        (
            "3. Sprint 2 & 3 Full End-to-End API Integration Suite",
            [PYTHON_EXE, "-u", "backend/tests/test_api_direct.py"],
        ),
        (
            "4. Sprint 2 Advanced ML Model Evaluation on Held-Out Test Set",
            [PYTHON_EXE, "ml_pipeline/evaluate_advanced.py"],
        ),
    ]

    all_passed = True
    for title, cmd in steps:
        if not run_step(title, cmd):
            all_passed = False
            break

    print("\n" + "=" * 65)
    if all_passed:
        print("  ALL TEST SUITES PASSED (100% SUCCESS RATE) - SYSTEM READY FOR DEMO!")
    else:
        print("  SOME TESTS FAILED - REVIEW LOGS ABOVE")
    print("=" * 65)
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()

