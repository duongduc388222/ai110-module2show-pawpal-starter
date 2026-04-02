"""PawPal+ CLI demo — showcases 1 Owner, 2 Pets, 6 Tasks, and Scheduler logic."""

from pawpal_system import Owner, Pet, Task, Scheduler

_WIDTH = 57


def _divider(label: str = "") -> None:
    if label:
        pad = (_WIDTH - len(label) - 2) // 2
        remainder = _WIDTH - pad - len(label) - 2
        print(f"\n{'─' * pad} {label} {'─' * remainder}")
    else:
        print("─" * _WIDTH)


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
    rex.add_task(Task("Grooming",      "09:00", 45, "medium", "Rex", "weekly"))
    rex.add_task(Task("Evening walk",  "18:00", 30, "high",   "Rex", "daily"))

    scheduler = Scheduler(owner=owner)

    print("=" * _WIDTH)
    print(f"  PawPal+ Demo  —  {owner}")
    print("=" * _WIDTH)

    # ── Full sorted schedule ──────────────────────────────────────────────────
    _divider("Full Schedule — sorted by time")
    for task in scheduler.build_schedule():
        print(" ", task)

    # ── Filter to a single pet ────────────────────────────────────────────────
    _divider("Rex's tasks only")
    for task in scheduler.filter_tasks(pet_name="Rex"):
        print(" ", task)

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

    # ── Recurrence: complete a daily task, then regenerate ────────────────────
    _divider("Recurrence")
    feeding = mochi.tasks[0]
    mochi.complete_task(feeding.task_id)
    print(f"  Marked complete: {feeding.title} ({feeding.pet_name})")

    new_tasks = scheduler.generate_recurring()
    for t in new_tasks:
        print(f"  New recurring task: {t.title} @ {t.time} for {t.pet_name}")

    # ── Updated schedule after recurrence ─────────────────────────────────────
    _divider("Updated Schedule (pending tasks only)")
    for task in scheduler.build_schedule():
        print(" ", task)

    _divider()


if __name__ == "__main__":
    main()
