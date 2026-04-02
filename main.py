"""PawPal+ CLI demo — showcases 1 Owner, 2 Pets, 6 Tasks, and Scheduler logic.

Challenge 4: uses tabulate for polished table output.
Challenge 1: demonstrates find_next_slot (Next Available Slot).
Challenge 3: demonstrates sort_by_priority_then_time.
Challenge 2: demonstrates save_to_json / load_from_json.
"""

from tabulate import tabulate

from pawpal_system import Owner, Pet, Task, Scheduler, save_to_json, load_from_json

_WIDTH = 57


def _divider(label: str = "") -> None:
    if label:
        pad = (_WIDTH - len(label) - 2) // 2
        remainder = _WIDTH - pad - len(label) - 2
        print(f"\n{'─' * pad} {label} {'─' * remainder}")
    else:
        print("─" * _WIDTH)


def _task_rows(tasks: list[Task]) -> list[list]:
    PRIORITY_ICON = {"high": "🔴", "medium": "🟡", "low": "🟢"}
    return [
        [
            "✓" if t.completed else "○",
            t.time,
            t.end_time(),
            t.title,
            t.pet_name,
            f"{PRIORITY_ICON.get(t.priority, '')} {t.priority}",
            t.frequency,
        ]
        for t in tasks
    ]


_HEADERS = ["", "Start", "End", "Task", "Pet", "Priority", "Freq"]


def main() -> None:
    # ── Setup ─────────────────────────────────────────────────────────────────
    owner = Owner(name="Jordan", email="jordan@example.com")

    mochi = Pet(name="Mochi", species="cat")
    rex = Pet(name="Rex", species="dog")
    owner.add_pet(mochi)
    owner.add_pet(rex)

    # Tasks for Mochi (includes a deliberate overlap for conflict demo)
    mochi.add_task(Task("Morning feeding", "07:00", 10, "high",   "Mochi", "daily"))
    mochi.add_task(Task("Playtime",        "10:00", 20, "medium", "Mochi", "daily"))
    mochi.add_task(Task("Vet checkup",     "10:10", 60, "high",   "Mochi", "once"))

    # Tasks for Rex
    rex.add_task(Task("Morning walk",  "07:30", 30, "high",   "Rex", "daily"))
    rex.add_task(Task("Grooming",      "09:00", 45, "low",    "Rex", "weekly"))
    rex.add_task(Task("Evening walk",  "18:00", 30, "medium", "Rex", "daily"))

    scheduler = Scheduler(owner=owner)

    print("=" * _WIDTH)
    print(f"  PawPal+ Demo  —  {owner}")
    print("=" * _WIDTH)

    # ── Sorted schedule (Challenge 4: tabulate) ───────────────────────────────
    _divider("Full Schedule — sorted by time")
    print(tabulate(_task_rows(scheduler.build_schedule()), headers=_HEADERS, tablefmt="rounded_outline"))

    # ── Challenge 3: Priority-then-time sort ──────────────────────────────────
    _divider("Priority Sort — high first, then time")
    print(tabulate(
        _task_rows(scheduler.sort_by_priority_then_time()),
        headers=_HEADERS,
        tablefmt="rounded_outline",
    ))

    # ── Filter to a single pet ────────────────────────────────────────────────
    _divider("Rex's tasks only")
    print(tabulate(_task_rows(scheduler.filter_tasks(pet_name="Rex")), headers=_HEADERS, tablefmt="rounded_outline"))

    # ── Conflict detection ────────────────────────────────────────────────────
    _divider("Conflict Detection")
    conflicts = scheduler.detect_conflicts()
    if conflicts:
        for a, b in conflicts:
            print(
                f"  ⚠  '{a.title}' ({a.time}–{a.end_time()}) overlaps "
                f"'{b.title}' ({b.time}–{b.end_time()}) for {a.pet_name}"
            )
    else:
        print("  ✓  No conflicts detected.")

    # ── Challenge 1: Next Available Slot ─────────────────────────────────────
    _divider("Next Available Slot (Challenge 1)")
    slot_global = scheduler.find_next_slot(duration=30, after="07:00")
    print(f"  Next free 30-min slot (all pets): {slot_global}")
    slot_mochi = scheduler.find_next_slot(duration=30, after="07:00", pet_name="Mochi")
    print(f"  Next free 30-min slot for Mochi:  {slot_mochi}")

    # ── Recurrence ────────────────────────────────────────────────────────────
    _divider("Recurrence")
    feeding = mochi.tasks[0]
    mochi.complete_task(feeding.task_id)
    print(f"  Marked complete: {feeding.title} ({feeding.pet_name})")
    new_tasks = scheduler.generate_recurring()
    for t in new_tasks:
        print(f"  New recurring task: {t.title} @ {t.time} for {t.pet_name}")

    # ── Challenge 2: JSON Persistence ─────────────────────────────────────────
    _divider("JSON Persistence (Challenge 2)")
    save_to_json(owner, "pawpal_data.json")
    print("  Saved to pawpal_data.json")
    loaded = load_from_json("pawpal_data.json")
    print(f"  Loaded back: {loaded}")
    print(f"  Pets: {[p.name for p in loaded.get_pets()]}")
    task_count = sum(len(p.tasks) for p in loaded.get_pets())
    print(f"  Total tasks loaded: {task_count}")

    _divider()


if __name__ == "__main__":
    main()
