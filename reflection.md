# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

The initial UML defined four classes with clear, non-overlapping responsibilities:

- `Task` — atomic unit of care activity: title, start time (HH:MM), duration, priority, frequency, and completion status. It knows how to compute its own end time and clone itself for recurrence.
- `Pet` — owns a list of Tasks and is responsible for mutating that list (add, complete, query pending). A pet does not know about other pets.
- `Owner` — registers and retrieves pets. It is the top-level container; nothing else reaches up to it except the Scheduler.
- `Scheduler` — receives a reference to an Owner and performs every cross-pet algorithm: sorting, filtering, conflict detection, recurrence, and building the final schedule.

The key structural decision was that `Scheduler` holds an `Owner` reference rather than a flat list of pets. This gives it access to `owner.get_pet(name)` for named lookups, while a flat list would require the caller to pass the right subset each time.

**b. Design changes**

One significant change from the initial sketch: `Task` was originally planned to hold a `date` field (`datetime.date`) to support multi-day scheduling. This was removed in favour of a plain `time: str` (`HH:MM`), because the project scope is a single daily planning session. Using datetime objects would have added parsing complexity, timezone edge cases, and heavier test fixtures for no benefit at this scale.

A second smaller change: `Scheduler` initially had a `build_schedule()` method that also resolved conflicts (dropping the lower-priority task). This was removed after reflection — the app should surface conflicts and let the owner decide, not silently discard tasks. `build_schedule()` now simply returns sorted pending tasks, and `detect_conflicts()` is a separate advisory method.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers three main constraints:

1. **Time** — tasks are ordered by HH:MM start time. Zero-padded strings sort correctly lexicographically, so no `datetime` parsing is needed for ordering.
2. **Frequency** — tasks carry `once | daily | weekly` metadata. The scheduler uses this to regenerate pending copies when a recurring task is marked complete.
3. **Overlap** — two tasks conflict when their time windows strictly intersect (start of A < end of B and start of B < end of A). Adjacent tasks (A ends exactly when B starts) are not flagged as conflicts.

Priority (low/medium/high) is displayed and tracked but does not currently drive automated reordering — the owner decides how to act on it. This was a deliberate choice to keep the scheduler transparent rather than opaque.

**b. Tradeoffs**

The most significant tradeoff is that recurrence regenerates one copy at a time rather than pre-generating N future instances. This means the owner must complete a task before the next instance appears. The benefit is simplicity: no date arithmetic, no state explosion, and no stale future tasks accumulating if the owner skips a day. The downside is that the schedule does not show upcoming recurrences in advance.

A second tradeoff: conflict detection operates only on **pending** tasks. Completed tasks are excluded even if they historically overlapped. This is correct for a live planning tool — the owner has already handled completed tasks — but it means the history of overlaps is lost once items are marked done.

---

## 3. AI Collaboration

**a. How you used AI**

AI assistance (Cursor / Claude) was used throughout the project:

- **System design** — iterating the UML diagram: what relationships to model, whether `Scheduler` should hold `Owner` or `list[Pet]`, and where recurrence logic should live.
- **Skeleton generation** — converting the finalized UML into `@dataclass` stubs with typed fields and method signatures before any logic was written.
- **Algorithm implementation** — the overlap detection formula (`a_start < b_end and b_start < a_end`) and the recurrence deduplication guard (`already_pending` check).
- **Test coverage** — identifying edge cases to add: exactly-adjacent tasks that should not conflict, cross-pet tasks that share a time window but should not conflict, and calling `generate_recurring()` twice to verify no duplicates.

The most useful prompt pattern was providing the method signature plus a concrete example of expected input/output, then asking for an implementation and an explanation of the edge cases it handles.

**b. Judgment and verification**

The most notable override: AI suggested using `datetime.time` objects for the `Task.time` field to enable proper time arithmetic. After reviewing the suggestion, I rejected it — the project is single-day, HH:MM strings are sufficient, and `datetime` would have required parsing on every read, added timezone concerns, and made the dataclass harder to serialise later. The arithmetic was replaced with a simple minutes-since-midnight integer calculation (`h * 60 + m`), which is correct, testable, and easy to read.

The conflict detection formula was also verified manually against three cases before committing: overlapping, sequential, and exactly-adjacent tasks.

---

## 4. Testing and Verification

**a. What you tested**

The 32-test suite covers:

- `Task.end_time()` arithmetic at simple, cross-hour, and near-midnight boundaries
- `Task.mark_complete()` and `clone_pending()` (field inheritance, new task ID, completed flag reset)
- `Pet.add_task()`, `complete_task()` (found/not-found), `get_pending_tasks()` exclusion
- `Owner.get_pet()` case-insensitive lookup and not-found sentinel
- `Scheduler.sort_tasks()` with two tasks across pets, N tasks, and an external list input
- `Scheduler.filter_tasks()` by pet name, by pending/completed status, and combined
- `Scheduler.detect_conflicts()` for overlap, sequential, adjacent, cross-pet, and completed-exclusion cases
- `Scheduler.generate_recurring()` for daily, weekly, `once` guard, no-duplicate on second call, and multi-pet bulk regeneration

These behaviors were chosen because they represent every method in the public API and cover the boundaries most likely to produce silent bugs (adjacent tasks, cross-pet false positives, double-recurrence).

**b. Confidence**

Confidence in the core logic is high — all 32 tests pass and the CLI demo produces the expected output. The area of least confidence is time-window edge cases involving durations that cross midnight (e.g., a task starting at 23:30 for 90 minutes). `end_time()` returns `"25:00"` rather than `"01:00"` the next day; this is acceptable for single-day use but would break in a multi-day context. If given more time, I would add a normalisation step and test tasks that span midnight.

---

## 5. Reflection

**a. What went well**

The UML-first workflow was the most satisfying part of the project. Writing the diagram before any code forced explicit decisions about ownership and responsibility that would otherwise have emerged messily during implementation. The resulting class design is clean and the Streamlit integration was straightforward because the backend API had no surprises.

**b. What you would improve**

The biggest thing to redesign would be time representation: moving from bare `HH:MM` strings to `datetime.time` (or a thin wrapper) would enable proper multi-day scheduling, recurrence calendaring, and timezone awareness. JSON persistence (saving and loading the owner/pet/task graph) would also be a high-value addition for a real app — the current in-memory state is wiped on every Streamlit restart.

**c. Key takeaway**

Designing the system on paper first — even a rough Mermaid class diagram — dramatically reduces the cost of AI-assisted coding. When the AI has a clear spec (class names, attributes, relationships, method signatures), it generates accurate code on the first attempt rather than requiring multiple correction rounds. The AI works best as an *implementer of a design you own*, not as an autonomous architect.
