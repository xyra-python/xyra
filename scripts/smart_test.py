import os
import subprocess
import sys
from pathlib import Path


def get_changed_files():
    """
    Get the list of changed files between the current HEAD and the target branch.
    In a PR context, usually comparing against 'origin/main'.
    """
    # In GitHub Actions, GITHUB_BASE_REF is the target branch (e.g., 'main')
    base_ref = os.environ.get("GITHUB_BASE_REF", "main")

    # If running locally or unable to determine, might fallback to comparing with main
    # Fetch origin/main to ensure we have it for comparison
    try:
        subprocess.run(["git", "fetch", "origin", base_ref], check=False, capture_output=True)
        cmd = ["git", "diff", "--name-only", f"origin/{base_ref}...HEAD"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return [f for f in result.stdout.splitlines() if f.strip()]
    except subprocess.CalledProcessError:
        print(f"Warning: Could not diff against origin/{base_ref}. Returning empty list.")
        return []

def map_file_to_test(filepath):
    """
    Map a modified file to its corresponding test file.
    Strategies:
    1. If file is in tests/, run it.
    2. If file is in xyra/, look for tests/test_{filename}.py or tests/{filename}_test.py
    """
    path = Path(filepath)

    # If it's not a python file, ignore unless it's a config file
    if path.suffix != ".py":
        return None

    if str(path).startswith("tests/"):
        return str(path)

    if str(path).startswith("xyra/"):
        # xyra/application.py -> tests/test_application.py
        # xyra/middleware/cors.py -> tests/test_cors.py or tests/test_middleware.py

        # 1. Check for tests/test_{filename}
        candidate_1 = Path("tests") / f"test_{path.name}"
        if candidate_1.exists():
            return str(candidate_1)

        # 2. If inside xyra/middleware/foo.py, try tests/test_foo.py
        if "middleware" in path.parts:
            candidate_mw = Path("tests") / f"test_{path.name}"
            if candidate_mw.exists():
                return str(candidate_mw)

        # 3. Check for exact name match in tests/ (rare but possible)

        # Fallback: If we modified core framework code but can't find exact test,
        # it might be safer to run all tests or just log a warning.
        # But per user request "only changed files", we try our best.

    return None

def main():
    changed_files = get_changed_files()
    if not changed_files:
        print("No changed files detected. Running all tests to be safe.")
        sys.exit(subprocess.call(["uv", "run", "pytest"]))

    # Critical files that should trigger full test suite
    critical_files = ["pyproject.toml", "uv.lock", "xyra/__init__.py"]
    for f in changed_files:
        if f in critical_files:
            print(f"Critical file {f} changed. Running all tests.")
            sys.exit(subprocess.call(["uv", "run", "pytest"]))

    tests_to_run = set()
    for f in changed_files:
        test_file = map_file_to_test(f)
        if test_file:
            tests_to_run.add(test_file)

    if not tests_to_run:
        print("No relevant tests found for changed files.")
        # Determine policy: Run nothing? Or run all?
        # User said: "only test modified parts".
        # If I modified a README, I shouldn't run tests.
        # If I modified a python file with no test, maybe I should warn?

        # Check if any changed file was python source code in xyra/
        source_code_changed = any(f.startswith("xyra/") and f.endswith(".py") for f in changed_files)
        if source_code_changed:
            print("Source code changed but no direct test found. Running all tests as fallback.")
            sys.exit(subprocess.call(["uv", "run", "pytest"]))
        else:
            print("Only non-code files changed (or files with no impact). Skipping tests.")
            sys.exit(0)

    print(f"Running selected tests: {tests_to_run}")
    cmd = ["uv", "run", "pytest"] + list(tests_to_run)
    sys.exit(subprocess.call(cmd))

if __name__ == "__main__":
    main()
