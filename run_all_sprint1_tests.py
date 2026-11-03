"""
Sprint 1 Master Verification Suite.
Runs all verification checks across API, contracts, database, and ML pipeline.
"""
import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
PYTHON_EXE = sys.executable

def run_step(description: str, cmd: list[str]) -> bool:
    print(f"\n==================================================")
    print(f"  RUNNING: {description}")
    print(f"==================================================")
    res = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    if res.returncode == 0:
        print(f"--> [PASS] {description}")
        return True
    else:
        print(f"--> [FAIL] {description} (Exit code: {res.returncode})")
        return False

def main():
    print("=" * 60)
    print("       AI CV-JOB MATCHING — SPRINT 1 VERIFICATION")
    print("=" * 60)
    
    steps = [
        ("Environment & Dependency Verification", [PYTHON_EXE, "backend/verify_env.py"]),
        ("Backend API & Contract Tests (US-01 -> US-04)", [PYTHON_EXE, "backend/tests/test_api.py"]),
        ("ML Pipeline Unit Tests (US-06 -> US-13 Edge Cases)", [PYTHON_EXE, "ml_pipeline/tests/test_pipeline_unit.py"]),
    ]
    
    all_passed = True
    for desc, cmd in steps:
        success = run_step(desc, cmd)
        if not success:
            all_passed = False
            break
            
    print("\n" + "=" * 60)
    if all_passed:
        print("   ALL SPRINT 1 INTEGRATION & UNIT SUITES PASSED (100%)")
    else:
        print("   SOME TESTS FAILED - CHECK OUTPUT ABOVE")
    print("=" * 60)
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()

