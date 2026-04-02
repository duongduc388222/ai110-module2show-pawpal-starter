# PawPal+ — Smart Pet Care Scheduler

PawPal+ is a Streamlit-based pet care management system that lets a pet owner schedule, track, and optimise care tasks across multiple pets. It was designed with a UML-first workflow, implemented using Python dataclasses, and verified through a 32-test pytest suite.

---

## Demo

![PawPal+ Schedule view showing Duc's pet Milu with tasks, filters, and mark-complete](demo.png)

## Features

| Feature | Description |
| :--- | :--- |
| **Multi-pet management** | Register any number of pets, each with its own task list |
| **Priority tracking** | Tasks ranked `low` / `medium` / `high` with visual indicators |
| **Chronological sorting** | Full-day view ordered by start time across all pets |
| **Flexible filtering** | Isolate tasks by pet name and/or completion status |
| **Recurrence** | `daily` and `weekly` tasks auto-regenerate once completed |
| **Conflict detection** | Flags overlapping time windows for the same pet |

---

## System Architecture

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

**Design summary:** `Owner` is the top-level container; `Pet` manages its own task list; `Task` is an atomic unit carrying time, duration, and recurrence metadata; `Scheduler` holds a reference to `Owner` so it can traverse all pets and perform cross-pet operations.

---

## Getting Started

### Prerequisites

Python 3.10 or newer.

### Setup

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run the Streamlit app

```bash
streamlit run app.py
```

Open the URL printed in the terminal (typically http://localhost:8501).

### Run the CLI demo

```bash
python main.py
```

The demo creates 1 owner (Jordan), 2 pets (Mochi the cat and Rex the dog), 6 tasks, and exercises every scheduler feature: sorted schedule, pet-level filter, conflict detection, task completion, and recurring task generation.

### Run tests

```bash
pytest test_pawpal.py -v
```

---

## Testing

`test_pawpal.py` contains 32 tests organised into six classes:

| Class | What is tested |
| :--- | :--- |
| `TestTask` | `end_time()` arithmetic (including hour-boundary and midnight), `mark_complete()`, `clone_pending()` field inheritance, unique task IDs |
| `TestPet` | `add_task()`, `complete_task()` (found / not found), `get_pending_tasks()` exclusion of completed items |
| `TestOwner` | `add_pet()` / `get_pets()`, `get_pet()` case-insensitive lookup and not-found sentinel |
| `TestSchedulerSort` | Two-task cross-pet ordering, N-task deterministic sort, external list input |
| `TestSchedulerFilter` | Filter by pet name, by pending status, by completed status, combined filter |
| `TestSchedulerConflicts` | Overlap detection, sequential non-conflict, exactly-adjacent non-conflict, cross-pet non-conflict, completed-task exclusion |
| `TestSchedulerRecurrence` | Daily and weekly regeneration, `once` guard, no-duplicate-on-second-call, multi-pet bulk regeneration |

All 32 tests pass with `pytest test_pawpal.py -v`.

---

## Advanced Challenges

Five optional challenges from `challenge.md` were implemented:

### Challenge 1 — Agent-Driven Algorithm: Next Available Slot

`Scheduler.find_next_slot(duration, after, pet_name)` scans all pending tasks in chronological order and walks a cursor forward past occupied windows until a gap of at least `duration` minutes is found. It can search globally (across all pets, for owner time-blocking) or per-pet (to avoid double-booking a single animal). The logic was designed with AI assistance: the key algorithmic insight was to advance the cursor to `max(cursor, task_end)` on each pass rather than re-scanning from the start — this gives O(n) performance.

### Challenge 2 — Data Persistence Layer

`save_to_json(owner, filepath)` and `load_from_json(filepath)` serialise/deserialise the full Owner → Pet → Task object graph using `dataclasses.asdict()` and standard `json`. No third-party serialisation library is needed. In `app.py`, `st.session_state` auto-loads from `pawpal_data.json` on startup if the file exists, and a **Save to JSON** button in the sidebar lets the user persist their session at any time.

### Challenge 3 — Priority-Based Scheduling

`Scheduler.sort_by_priority_then_time()` performs a two-key sort: primary by priority tier (high → medium → low) and secondary by `HH:MM` start time within each tier. The Schedule tab in the Streamlit UI exposes a **Sort by** dropdown (`Time` vs `Priority then Time`) so the user can toggle between views.

### Challenge 4 — Professional UI & Formatting

`main.py` uses the `tabulate` library (`rounded_outline` style) to render every schedule output as a formatted table with emoji priority indicators (🔴/🟡/🟢). The Streamlit UI already uses these same icons alongside frequency glyphs (🔁/📅/1️⃣) in the schedule dataframe.

### Challenge 5 — Multi-Model Benchmarking

See the **Prompt Comparison** section in `reflection.md` for a side-by-side analysis of Claude vs GPT-4o on the `find_next_slot` implementation task.

---

## AI Collaboration

This project was built with AI assistance (Cursor / Claude) for:

- Drafting and iterating the UML class diagram (decided `Scheduler` should hold a reference to `Owner` rather than a flat pet list — cleaner access by name)
- Generating dataclass stubs from the UML spec
- Implementing conflict detection overlap logic and recurrence deduplication
- Expanding the pytest suite and catching edge cases (adjacent-but-not-overlapping tasks, cross-pet false positives, double-recurrence guards)

All AI outputs were reviewed against the spec and manually verified before acceptance. The most significant override: AI initially proposed using `datetime` objects for time representation; this was simplified to `str` (`HH:MM`) because the project scope is single-day scheduling and string arithmetic is sufficient, keeping the model lighter.

See `reflection.md` for a full account of design decisions, tradeoffs, and AI collaboration strategy.


