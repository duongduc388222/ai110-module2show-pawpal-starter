"""PawPal+ — Evaluation harness for the AI Care Advisor.

Runs get_task_suggestions() against 6 predefined test cases and prints a
pass/fail summary table. Exit code 0 = all pass, 1 = any fail.

Usage:
    python eval_harness.py
"""

import re
import sys

from tabulate import tabulate

from ai_advisor import get_task_suggestions, AdvisorError

# ── Test case definitions ─────────────────────────────────────────────────────

# expect_error=True → the call must raise AdvisorError (guardrail case)
# expect_error=False → the call must return ≥1 valid task dicts
TEST_CASES = [
    {"pet_name": "Buddy",   "species": "dog",    "age_years": 2,  "notes": "outdoor, active", "expect_error": False},
    {"pet_name": "Mochi",   "species": "cat",    "age_years": 5,  "notes": "indoor only",     "expect_error": False},
    {"pet_name": "Thumper", "species": "rabbit", "age_years": 1,  "notes": "",                "expect_error": False},
    {"pet_name": "Tweety",  "species": "bird",   "age_years": 3,  "notes": "talks a lot",     "expect_error": False},
    {"pet_name": "Nemo",    "species": "dragon", "age_years": 2,  "notes": "",                "expect_error": True},
    {"pet_name": "",        "species": "dog",    "age_years": -1, "notes": "",                "expect_error": True},
]

_TIME_RE = re.compile(r"^\d{2}:\d{2}$")
_VALID_PRIORITY = {"low", "medium", "high"}
_VALID_FREQUENCY = {"once", "daily", "weekly"}
_REQUIRED_KEYS = {"title", "time", "duration_minutes", "priority", "frequency", "pet_name"}


def _check_tasks(tasks: list[dict]) -> list[str]:
    """Return a list of failure reasons for a task list; empty = all good."""
    failures = []
    if not tasks:
        failures.append("empty task list")
        return failures
    for i, t in enumerate(tasks):
        tag = f"task[{i}]"
        missing = _REQUIRED_KEYS - t.keys()
        if missing:
            failures.append(f"{tag} missing keys: {missing}")
            continue
        if not _TIME_RE.match(t["time"]):
            failures.append(f"{tag} bad time format: {t['time']!r}")
        if t["priority"] not in _VALID_PRIORITY:
            failures.append(f"{tag} bad priority: {t['priority']!r}")
        if t["frequency"] not in _VALID_FREQUENCY:
            failures.append(f"{tag} bad frequency: {t['frequency']!r}")
        if not isinstance(t["duration_minutes"], int) or t["duration_minutes"] < 1:
            failures.append(f"{tag} bad duration: {t['duration_minutes']!r}")
    return failures


def _run_case(case: dict) -> tuple[bool, str]:
    """Run one test case. Returns (passed, detail_string)."""
    label = f"{case['pet_name'] or '—'} ({case['species']}, {case['age_years']}y)"
    expect_error = case["expect_error"]

    try:
        tasks = get_task_suggestions(
            pet_name=case["pet_name"],
            species=case["species"],
            age_years=case["age_years"],
            notes=case["notes"],
        )
    except AdvisorError as e:
        if expect_error:
            return True, f"guardrail raised AdvisorError ✓  [{e}]"
        return False, f"unexpected AdvisorError: {e}"
    except Exception as e:
        return False, f"unexpected exception: {e}"

    if expect_error:
        return False, f"expected AdvisorError but got {len(tasks)} task(s)"

    failures = _check_tasks(tasks)
    if failures:
        return False, "schema failures: " + "; ".join(failures)

    return True, f"{len(tasks)} task(s) returned, all fields valid"


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    print("\nPawPal+ AI Advisor — Evaluation Harness")
    print("=" * 60)

    rows = []
    passed = 0

    for i, case in enumerate(TEST_CASES, start=1):
        label = f"{case['pet_name'] or '—'} ({case['species']}, {case['age_years']}y)"
        ok, detail = _run_case(case)
        passed += ok
        rows.append([f"Case {i}", label, "PASS ✅" if ok else "FAIL ❌", detail])

    print(tabulate(rows, headers=["#", "Input", "Result", "Detail"], tablefmt="simple"))
    print("=" * 60)
    total = len(TEST_CASES)
    print(f"Result: {passed}/{total} passed\n")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
