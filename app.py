"""PawPal+ – Streamlit interface for the pet care scheduling system."""

import os

import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler, save_to_json, load_from_json

_DATA_FILE = "pawpal_data.json"

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")

# ── Session state initialisation ──────────────────────────────────────────────
# Owner and Scheduler are kept in session_state so mutations made via UI
# buttons (add_pet, add_task, complete_task, etc.) persist across Streamlit
# reruns without resetting the in-memory object graph.

if "owner" not in st.session_state:
    if os.path.exists(_DATA_FILE):
        st.session_state.owner = load_from_json(_DATA_FILE)
    else:
        st.session_state.owner = Owner(name="Jordan", email="")
    st.session_state.scheduler = Scheduler(owner=st.session_state.owner)

owner: Owner = st.session_state.owner
scheduler: Scheduler = st.session_state.scheduler

PRIORITY_ICON: dict[str, str] = {"high": "🔴", "medium": "🟡", "low": "🟢"}
FREQ_ICON: dict[str, str] = {"daily": "🔁", "weekly": "📅", "once": "1️⃣"}

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("🐾 PawPal+")
    st.caption("Smart pet care scheduling")
    st.divider()

    # Owner card
    st.subheader("Owner")
    new_name = st.text_input("Name", value=owner.name, key="owner_name_input")
    new_email = st.text_input("Email (optional)", value=owner.email, key="owner_email_input")
    if st.button("Update Owner", use_container_width=True):
        owner.name = new_name.strip() or owner.name
        owner.email = new_email.strip()
        st.success("Owner updated.")

    st.divider()
    st.subheader("Persistence")
    if st.button("💾 Save to JSON", use_container_width=True):
        save_to_json(owner, _DATA_FILE)
        st.success(f"Saved to `{_DATA_FILE}`.")
    if os.path.exists(_DATA_FILE):
        st.caption(f"Auto-loads `{_DATA_FILE}` on next startup.")

    st.divider()

    # Add pet
    st.subheader("Add Pet")
    pet_name_in = st.text_input("Pet name", key="new_pet_name")
    species_in = st.selectbox(
        "Species", ["dog", "cat", "rabbit", "bird", "fish", "other"], key="new_pet_species"
    )
    if st.button("Add Pet", use_container_width=True):
        name = pet_name_in.strip()
        if not name:
            st.warning("Please enter a pet name.")
        elif owner.get_pet(name):
            st.error(f"'{name}' is already registered.")
        else:
            owner.add_pet(Pet(name=name, species=species_in))
            st.success(f"Added {name} ({species_in})")

    # Pet roster
    if owner.pets:
        st.divider()
        st.subheader("Registered Pets")
        for pet in owner.pets:
            done = sum(1 for t in pet.tasks if t.completed)
            total = len(pet.tasks)
            st.markdown(
                f"**{pet.name}** _{pet.species}_  \n"
                f"{done}/{total} tasks done"
            )

# ── Main page ─────────────────────────────────────────────────────────────────

st.title(f"🐾 {owner.name}'s PawPal+")

if not owner.pets:
    st.info("Add a pet in the sidebar to get started.")
    st.stop()

tab_schedule, tab_add, tab_tools = st.tabs(["📅 Schedule", "➕ Add Task", "🔧 Tools"])

# ── Tab: Add Task ─────────────────────────────────────────────────────────────

with tab_add:
    st.subheader("Add a New Task")
    pet_names = [p.name for p in owner.pets]

    col_a, col_b = st.columns(2)

    with col_a:
        task_pet = st.selectbox("For pet", pet_names, key="task_pet_select")
        task_title = st.text_input("Task title", value="Morning walk", key="task_title_in")
        task_time = st.text_input("Start time (HH:MM)", value="08:00", key="task_time_in")

    with col_b:
        task_dur = st.number_input(
            "Duration (minutes)", min_value=1, max_value=480, value=30, key="task_dur_in"
        )
        task_priority = st.selectbox(
            "Priority", ["low", "medium", "high"], index=2, key="task_priority_in"
        )
        task_freq = st.selectbox(
            "Frequency", ["once", "daily", "weekly"], key="task_freq_in"
        )

    if st.button("Add Task", type="primary", use_container_width=True):
        title = task_title.strip()
        pet = owner.get_pet(task_pet)
        if not title:
            st.warning("Please enter a task title.")
        elif pet is None:
            st.error("Selected pet not found.")
        else:
            try:
                parts = task_time.strip().split(":")
                h, m = int(parts[0]), int(parts[1])
                if not (0 <= h <= 23 and 0 <= m <= 59):
                    raise ValueError
                task = Task(
                    title=title,
                    time=f"{h:02d}:{m:02d}",
                    duration_minutes=int(task_dur),
                    priority=task_priority,
                    pet_name=task_pet,
                    frequency=task_freq,
                )
                pet.add_task(task)
                st.success(
                    f"Task '{task.title}' added for **{task_pet}** "
                    f"at {task.time} ({task_priority} priority, {task_freq})."
                )
            except (ValueError, IndexError):
                st.error("Invalid time. Use HH:MM format, e.g. 08:30.")

# ── Tab: Schedule ─────────────────────────────────────────────────────────────

with tab_schedule:
    st.subheader("Daily Schedule")

    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        filter_pet = st.selectbox(
            "Filter by pet", ["All"] + [p.name for p in owner.pets], key="filter_pet_sel"
        )
    with col_f2:
        filter_status = st.selectbox(
            "Filter by status", ["All", "Pending", "Completed"], key="filter_status_sel"
        )
    with col_f3:
        sort_mode = st.selectbox(
            "Sort by", ["Time", "Priority then Time"], key="sort_mode_sel"
        )

    pet_filter: str | None = None if filter_pet == "All" else filter_pet
    completed_filter: bool | None = None
    if filter_status == "Pending":
        completed_filter = False
    elif filter_status == "Completed":
        completed_filter = True

    filtered = scheduler.filter_tasks(pet_name=pet_filter, completed=completed_filter)
    if sort_mode == "Priority then Time":
        sorted_tasks = scheduler.sort_by_priority_then_time(filtered)
    else:
        sorted_tasks = scheduler.sort_tasks(filtered)

    if not sorted_tasks:
        st.info("No tasks match the current filters.")
    else:
        rows = [
            {
                "Status": "✅" if t.completed else "⏳",
                "Time": f"{t.time} → {t.end_time()}",
                "Task": t.title,
                "Pet": t.pet_name,
                "Priority": f"{PRIORITY_ICON.get(t.priority, '')} {t.priority}",
                "Frequency": f"{FREQ_ICON.get(t.frequency, '')} {t.frequency}",
                "ID": t.task_id,
            }
            for t in sorted_tasks
        ]
        st.dataframe(rows, use_container_width=True, hide_index=True)

    # Mark complete
    st.divider()
    st.subheader("Mark Task Complete")
    all_pending = scheduler.filter_tasks(completed=False)
    if all_pending:
        options = {
            f"{t.time} — {t.title} ({t.pet_name})": t
            for t in scheduler.sort_tasks(all_pending)
        }
        selected_label = st.selectbox("Select task", list(options.keys()), key="complete_sel")
        if st.button("Mark as Complete ✅", type="primary"):
            selected = options[selected_label]
            pet = owner.get_pet(selected.pet_name)
            if pet:
                pet.complete_task(selected.task_id)
                st.success(f"'{selected.title}' marked as complete.")
    else:
        st.success("All tasks are complete!")

# ── Tab: Tools ────────────────────────────────────────────────────────────────

with tab_tools:
    col_l, col_r = st.columns(2)

    with col_l:
        st.subheader("Conflict Detection")
        st.caption(
            "Flags overlapping time windows for pending tasks belonging to the same pet. "
            "Tasks for different pets can legitimately overlap — only same-pet conflicts matter."
        )
        if st.button("Check for Conflicts 🔍", use_container_width=True):
            conflicts = scheduler.detect_conflicts()
            if conflicts:
                for a, b in conflicts:
                    st.warning(
                        f"**{a.pet_name}** — "
                        f"'{a.title}' ({a.time}–{a.end_time()}) overlaps "
                        f"'{b.title}' ({b.time}–{b.end_time()})"
                    )
            else:
                st.success("No scheduling conflicts detected.")

    with col_r:
        st.subheader("Generate Recurring Tasks")
        st.caption(
            "For every completed daily or weekly task, a fresh pending copy is added. "
            "One-off tasks ('once') are not regenerated."
        )
        if st.button("Generate Recurring 🔁", use_container_width=True):
            new_tasks = scheduler.generate_recurring()
            if new_tasks:
                for t in new_tasks:
                    st.success(
                        f"Recurring task created: '{t.title}' for **{t.pet_name}** at {t.time}"
                    )
            else:
                st.info("No new recurring tasks to generate.")

    st.divider()
    st.subheader("Next Available Slot")
    st.caption("Find the earliest free gap in the schedule for a new task (Challenge 1).")
    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        slot_pet = st.selectbox("For pet (or all)", ["All pets"] + [p.name for p in owner.pets], key="slot_pet")
    with col_s2:
        slot_dur = st.number_input("Duration needed (min)", min_value=5, max_value=480, value=30, key="slot_dur")
    with col_s3:
        slot_after = st.text_input("Search from (HH:MM)", value="07:00", key="slot_after")
    if st.button("Find Next Slot 🔍", use_container_width=True):
        pet_arg = None if slot_pet == "All pets" else slot_pet
        try:
            h, m = map(int, slot_after.split(":"))
            assert 0 <= h <= 23 and 0 <= m <= 59
            result = scheduler.find_next_slot(
                duration=int(slot_dur), after=slot_after, pet_name=pet_arg
            )
            if result:
                st.success(f"Next available {slot_dur}-min slot: **{result}**")
            else:
                st.warning("No available slot found before midnight.")
        except (ValueError, AssertionError):
            st.error("Invalid time format. Use HH:MM.")
