"""
Environment verification script for AI CV-Job Matching.

Run this script to confirm that all required packages are importable and
print their versions.  Exits with code 0 on success, non-zero on failure.

Usage:
    d:\\anacoda\\python.exe backend/verify_env.py
"""

import sys
import io

# Force UTF-8 output on Windows consoles that default to cp1252
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def check_imports() -> bool:
    """Import each required package and print its version."""
    ok = True
    checks = [
        ("fastapi", "fastapi", "__version__"),
        ("scikit-learn", "sklearn", "__version__"),
        ("pandas", "pandas", "__version__"),
        ("numpy", "numpy", "__version__"),
        ("pymupdf", "fitz", "__version__"),
        ("sqlalchemy", "sqlalchemy", "__version__"),
    ]

    print("=" * 50)
    print("  AI CV-Matching - Environment Verification")
    print("=" * 50)

    for display_name, module_name, version_attr in checks:
        try:
            mod = __import__(module_name)
            version = getattr(mod, version_attr, "unknown")
            print(f"  [OK]  {display_name:<20} {version}")
        except ImportError as exc:
            print(f"  [MISSING]  {display_name:<20} ({exc})")
            ok = False

    print("=" * 50)
    return ok


if __name__ == "__main__":
    success = check_imports()
    if success:
        print("\nAll packages verified successfully.")
        sys.exit(0)
    else:
        print("\nOne or more packages are missing.")
        sys.exit(1)
