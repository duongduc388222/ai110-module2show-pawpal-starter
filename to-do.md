# PawPal+ — Phase Completion Log

---

## Phase 1 — System Design & UML
**Milestone:** Phase 1 | **Rubric:** UML Diagram (4 pts)

### What was done
- Designed a four-class system: `Owner`, `Pet`, `Task`, `Scheduler`.
- Generated a Mermaid.js class diagram showing attributes, methods, and relationships (embedded in `pawpal_system.py` module docstring and `README.md`).
- Created `pawpal_system.py` with `@dataclass` stubs: typed fields and method signatures, no logic yet.

### Files touched
- `pawpal_system.py` (created)

### Open questions at end of phase
- Should `Task` hold a `date` field for multi-day scheduling? (Resolved in Phase 2: no — kept as `HH:MM` string for single-day scope.)
- Should `Scheduler` hold a flat `list[Pet]` or an `Owner` reference? (Resolved: `Owner` reference, for named lookup via `get_pet()`.)

---

## Phase 2 — Core Logic & CLI Demo
**Milestone:** Phase 2 | **Rubric:** Core Implementation (4 pts), Demo Script (3 pts), Pytest Suite (3 pts)

### What was done
- Fleshed out all method bodies in `pawpal_system.py`: `Task.end_time()`, `mark_complete()`, `clone_pending()`; `Pet.add_task()`, `complete_task()`, `get_pending_tasks()`; `Owner.add_pet()`, `get_pet()` (case-insensitive); `Scheduler.get_all_tasks()`, `sort_tasks()`, `filter_tasks()`, `detect_conflicts()`, `generate_recurring()`, `build_schedule()`.
- Created `main.py` demonstrating: 1 Owner (Jordan), 2 Pets (Mochi the cat, Rex the dog), 6 Tasks, sorted schedule, pet filter, conflict detection, task completion, and recurrence generation.
- Created `test_pawpal.py` with 32 pytest cases organised in 7 test classes — all passing green.
- Added docstrings on every public class and method.

### Files touched
- `pawpal_system.py` (updated — full logic)
- `main.py` (created)
- `test_pawpal.py` (created)

---

## Phase 3 — Streamlit Integration
**Milestone:** Phase 3 | **Rubric:** Core Implementation (contributes to UI wiring)

### What was done
- Rewrote `app.py` from the thin starter stub to a full Streamlit app.
- Initialised `st.session_state.owner` and `st.session_state.scheduler` on first run; both objects persist across reruns because Streamlit mutates the in-memory dataclass in place — no data loss on button clicks.
- Sidebar handles owner name/email updates and pet registration (with duplicate-name guard).
- Three tabs: Schedule, Add Task, Tools.

### Files touched
- `app.py` (rewritten)

---

## Phase 4 — Algorithmic Layer
**Milestone:** Phase 4 | **Rubric:** Algorithmic Features (3 pts) — all operate across multiple pets

### What was done
All four algorithmic features were implemented in `pawpal_system.py` (backend) and exposed in `app.py` (UI):

| Feature | Where |
| :--- | :--- |
| **Sort** chronologically (HH:MM) | `Scheduler.sort_tasks()` + Schedule tab |
| **Filter** by pet name and/or completion status | `Scheduler.filter_tasks()` + Schedule tab dropdowns |
| **Recurrence** daily/weekly auto-regeneration | `Scheduler.generate_recurring()` + Tools tab button |
| **Conflict detection** same-pet time-window overlap | `Scheduler.detect_conflicts()` + Tools tab button |

UI shows `st.success` / `st.warning` / `st.info` for all algorithmic results.

### Files touched
- `pawpal_system.py` (algorithmic methods)
- `app.py` (Tools tab UI)

---

## Phase 5 — Testing & README
**Milestone:** Phase 5 | **Rubric:** Documentation & AI (3 pts), Pytest Suite (3 pts)

### What was done
- Expanded `test_pawpal.py` to 32 tests covering sort, filter, conflict detection, recurrence (including edge cases: adjacent non-conflicting tasks, cross-pet non-conflict, double-recurrence guard, `once`-frequency guard, multi-pet bulk recurrence).
- Rewrote `README.md` with: system description, Mermaid class diagram, features table, setup/run/test instructions, full testing section documenting what each test class covers.

### Files touched
- `test_pawpal.py` (expanded)
- `README.md` (rewritten)

---

## Phase 6 — Polish & Reflection
**Milestone:** Phase 6 | **Rubric:** Documentation & AI (3 pts)

### What was done
- Completed all five sections of `reflection.md`: initial design rationale, design changes (dropped `datetime`, split `build_schedule` and `detect_conflicts`), scheduling constraints and tradeoffs, AI collaboration account, testing confidence, and key takeaway.
- UML diagram is embedded in both `pawpal_system.py` (module docstring) and `README.md` (Mermaid code block).
- `app.py` uses `st.success`, `st.warning`, and `st.info` throughout for all algorithmic results.
- All 32 pytest cases pass (`pytest test_pawpal.py -v`).

### Files touched
- `reflection.md` (completed)
- `to-do.md` (this file — created)

### Submission checklist
- [x] `pawpal_system.py` — 4 dataclasses, full logic, docstrings, UML in module docstring
- [x] `main.py` — CLI demo: 1 owner, 2 pets, 6 tasks, all scheduler features
- [x] `test_pawpal.py` — 32 tests, all green
- [x] `app.py` — Streamlit UI with session_state, all features wired
- [x] `README.md` — Mermaid UML, features, run/test instructions, AI reflection
- [x] `reflection.md` — all 5 sections complete
- [ ] Repo pushed to GitHub (ready for your push when you review)
