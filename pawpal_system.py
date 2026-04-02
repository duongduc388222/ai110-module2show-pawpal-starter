"""PawPal+ – core domain model and scheduling engine.

UML Class Diagram (Mermaid):

```mermaid
classDiagram
    class Owner {
        +name: str
        +email: str
        +pets: list[Pet]
        +add_pet(pet) None
        +get_pets() list[Pet]
        +get_pet(name) Optional[Pet]
    }
    class Pet {
        +name: str
        +species: str
        +tasks: list[Task]
        +add_task(task) None
        +complete_task(task_id) bool
        +get_tasks() list[Task]
        +get_pending_tasks() list[Task]
    }
    class Task {
        +title: str
        +time: str
        +duration_minutes: int
        +priority: str
        +pet_name: str
        +frequency: str
        +completed: bool
        +task_id: str
        +end_time() str
        +mark_complete() None
        +clone_pending() Task
    }
    class Scheduler {
        +owner: Owner
        +get_all_tasks() list[Task]
        +sort_tasks(tasks) list[Task]
        +filter_tasks(pet_name, completed) list[Task]
        +detect_conflicts() list[tuple]
        +generate_recurring() list[Task]
        +build_schedule() list[Task]
    }
    Owner "1" --> "*" Pet : owns
    Pet "1" --> "*" Task : has
    Scheduler --> Owner : coordinates
```
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

# Priority rank used for multi-tier sorting (lower number = higher urgency)
PRIORITY_ORDER: dict[str, int] = {"high": 0, "medium": 1, "low": 2}


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@dataclass
class Task:
    """Represents a single pet-care activity with a scheduled start time."""

    title: str
    time: str                   # "HH:MM" scheduled start
    duration_minutes: int
    priority: str               # "low" | "medium" | "high"
    pet_name: str
    frequency: str = "once"     # "once" | "daily" | "weekly"
    completed: bool = False
    task_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def end_time(self) -> str:
        """Return the task's end time as 'HH:MM'."""
        h, m = map(int, self.time.split(":"))
        total = h * 60 + m + self.duration_minutes
        return f"{total // 60:02d}:{total % 60:02d}"

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.completed = True

    def clone_pending(self) -> Task:
        """Return a fresh pending copy — used when a recurring task regenerates."""
        return Task(
            title=self.title,
            time=self.time,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            pet_name=self.pet_name,
            frequency=self.frequency,
        )

    def __str__(self) -> str:
        status = "✓" if self.completed else "○"
        return (
            f"[{status}] {self.time}–{self.end_time()} "
            f"{self.title} ({self.pet_name}, {self.priority}, {self.frequency})"
        )


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    """A pet belonging to an Owner, carrying a list of care Tasks."""

    name: str
    species: str
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Append a task to this pet's task list."""
        self.tasks.append(task)

    def complete_task(self, task_id: str) -> bool:
        """Mark the task with the given ID complete; return True if found."""
        for t in self.tasks:
            if t.task_id == task_id:
                t.mark_complete()
                return True
        return False

    def get_tasks(self) -> list[Task]:
        """Return all tasks (completed and pending)."""
        return list(self.tasks)

    def get_pending_tasks(self) -> list[Task]:
        """Return only incomplete tasks."""
        return [t for t in self.tasks if not t.completed]

    def __str__(self) -> str:
        return f"{self.name} ({self.species}) — {len(self.tasks)} task(s)"


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

@dataclass
class Owner:
    """Top-level container that owns one or more Pets."""

    name: str
    email: str = ""
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner."""
        self.pets.append(pet)

    def get_pets(self) -> list[Pet]:
        """Return all registered pets."""
        return list(self.pets)

    def get_pet(self, name: str) -> Optional[Pet]:
        """Find a pet by name (case-insensitive); return None if not found."""
        for p in self.pets:
            if p.name.lower() == name.lower():
                return p
        return None

    def __str__(self) -> str:
        return f"Owner: {self.name} — {len(self.pets)} pet(s)"


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

@dataclass
class Scheduler:
    """Coordinates cross-pet scheduling logic for a given Owner.

    All algorithmic methods operate across every pet the owner has registered,
    satisfying the requirement that features work across multiple pets.
    """

    owner: Owner

    # ── data access ──────────────────────────────────────────────────────────

    def get_all_tasks(self) -> list[Task]:
        """Collect every task from all of the owner's pets."""
        tasks: list[Task] = []
        for pet in self.owner.pets:
            tasks.extend(pet.tasks)
        return tasks

    # ── algorithmic features ─────────────────────────────────────────────────

    def sort_tasks(self, tasks: Optional[list[Task]] = None) -> list[Task]:
        """Return tasks sorted chronologically by start time (HH:MM).

        Uses all owner tasks when no explicit list is supplied.
        Because HH:MM strings are zero-padded, lexicographic sort is correct.
        """
        source = tasks if tasks is not None else self.get_all_tasks()
        return sorted(source, key=lambda t: t.time)

    def filter_tasks(
        self,
        pet_name: Optional[str] = None,
        completed: Optional[bool] = None,
    ) -> list[Task]:
        """Return tasks filtered across all pets.

        Parameters
        ----------
        pet_name:  restrict to tasks for this pet (case-insensitive).
        completed: True → completed only; False → pending only; None → all.
        """
        tasks = self.get_all_tasks()
        if pet_name is not None:
            tasks = [t for t in tasks if t.pet_name.lower() == pet_name.lower()]
        if completed is not None:
            tasks = [t for t in tasks if t.completed == completed]
        return tasks

    def detect_conflicts(self) -> list[tuple[Task, Task]]:
        """Return pairs of *pending* tasks whose time windows overlap for the same pet.

        Cross-pet overlaps are not flagged — a different person can handle
        two pets simultaneously.
        """
        conflicts: list[tuple[Task, Task]] = []
        for pet in self.owner.pets:
            pending = pet.get_pending_tasks()
            for i, a in enumerate(pending):
                for b in pending[i + 1:]:
                    if self._overlaps(a, b):
                        conflicts.append((a, b))
        return conflicts

    def generate_recurring(self) -> list[Task]:
        """For each completed recurring task, append one fresh pending copy.

        Returns the newly created Task objects.
        Skips pets that already have a pending copy with the same title and time
        to prevent duplicates on repeated calls.
        """
        new_tasks: list[Task] = []
        for pet in self.owner.pets:
            for task in list(pet.tasks):    # snapshot avoids mutation-during-iteration
                if task.completed and task.frequency != "once":
                    already_pending = any(
                        t.title == task.title
                        and t.time == task.time
                        and not t.completed
                        for t in pet.tasks
                    )
                    if not already_pending:
                        clone = task.clone_pending()
                        pet.add_task(clone)
                        new_tasks.append(clone)
        return new_tasks

    def build_schedule(self) -> list[Task]:
        """Return all pending tasks sorted chronologically across all pets."""
        pending = self.filter_tasks(completed=False)
        return self.sort_tasks(pending)

    # Challenge 3 ─────────────────────────────────────────────────────────────

    def sort_by_priority_then_time(
        self, tasks: Optional[list[Task]] = None
    ) -> list[Task]:
        """Sort tasks: high priority first; within the same tier, by start time.

        Uses all owner tasks when no explicit list is supplied.
        """
        source = tasks if tasks is not None else self.get_all_tasks()
        return sorted(
            source,
            key=lambda t: (PRIORITY_ORDER.get(t.priority, 99), t.time),
        )

    # Challenge 1 ─────────────────────────────────────────────────────────────

    def find_next_slot(
        self,
        duration: int,
        after: str = "07:00",
        pet_name: Optional[str] = None,
    ) -> Optional[str]:
        """Find the earliest available gap of at least `duration` minutes.

        Parameters
        ----------
        duration:  required slot length in minutes.
        after:     earliest acceptable start time ('HH:MM'). Defaults to 07:00.
        pet_name:  when supplied, only considers that pet's tasks (avoids
                   double-booking a single animal). When None, considers all
                   pending tasks (useful for owner-level time blocking).

        Returns 'HH:MM' of the slot start, or None if no gap exists before
        midnight.
        """
        if pet_name:
            tasks = self.filter_tasks(pet_name=pet_name, completed=False)
        else:
            tasks = self.filter_tasks(completed=False)

        occupied = self.sort_tasks(tasks)
        cursor = self._time_to_minutes(after)

        for task in occupied:
            task_start = self._time_to_minutes(task.time)
            task_end = task_start + task.duration_minutes

            if task_start >= cursor + duration:
                # Gap before this task is large enough
                break
            if task_end > cursor:
                # Task blocks our cursor; advance past it
                cursor = task_end

        if cursor + duration <= 24 * 60:
            return f"{cursor // 60:02d}:{cursor % 60:02d}"
        return None

    # ── private helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _time_to_minutes(time_str: str) -> int:
        """Convert 'HH:MM' to total minutes since midnight."""
        h, m = map(int, time_str.split(":"))
        return h * 60 + m

    def _overlaps(self, a: Task, b: Task) -> bool:
        """Return True when the time windows of a and b intersect (strictly)."""
        a_start = self._time_to_minutes(a.time)
        a_end = a_start + a.duration_minutes
        b_start = self._time_to_minutes(b.time)
        b_end = b_start + b.duration_minutes
        return a_start < b_end and b_start < a_end


# ---------------------------------------------------------------------------
# Challenge 2 — JSON persistence (module-level helpers)
# ---------------------------------------------------------------------------

def save_to_json(owner: Owner, filepath: str = "pawpal_data.json") -> None:
    """Serialise the Owner (with all nested Pets and Tasks) to a JSON file.

    Uses dataclasses.asdict() to convert the full object graph to plain dicts
    before passing to json.dump, so no third-party serialisation library is
    needed.
    """
    Path(filepath).write_text(json.dumps(asdict(owner), indent=2))


def load_from_json(filepath: str = "pawpal_data.json") -> Owner:
    """Reconstruct an Owner from a JSON file produced by save_to_json.

    Manually rebuilds Owner → Pet → Task so that each object is a proper
    dataclass instance (not a plain dict) and task_ids are preserved.
    """
    data = json.loads(Path(filepath).read_text())
    owner = Owner(name=data["name"], email=data.get("email", ""))
    for pd in data.get("pets", []):
        pet = Pet(name=pd["name"], species=pd["species"])
        for td in pd.get("tasks", []):
            pet.add_task(
                Task(
                    title=td["title"],
                    time=td["time"],
                    duration_minutes=td["duration_minutes"],
                    priority=td["priority"],
                    pet_name=td["pet_name"],
                    frequency=td.get("frequency", "once"),
                    completed=td.get("completed", False),
                    task_id=td["task_id"],
                )
            )
        owner.add_pet(pet)
    return owner
