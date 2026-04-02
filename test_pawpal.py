"""Pytest suite for PawPal+ — covers Task, Pet, Owner, and Scheduler behaviors."""

import pytest
from pawpal_system import Owner, Pet, Task, Scheduler


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def owner():
    o = Owner(name="Test Owner")
    o.add_pet(Pet("Mochi", "cat"))
    o.add_pet(Pet("Rex", "dog"))
    return o


@pytest.fixture
def scheduler(owner):
    return Scheduler(owner=owner)


# ── Task ──────────────────────────────────────────────────────────────────────

class TestTask:
    def test_end_time_simple(self):
        t = Task("Walk", "08:00", 30, "high", "Rex")
        assert t.end_time() == "08:30"

    def test_end_time_crosses_hour(self):
        t = Task("Walk", "08:45", 30, "high", "Rex")
        assert t.end_time() == "09:15"

    def test_end_time_midnight_boundary(self):
        t = Task("Night meds", "23:30", 45, "high", "Mochi")
        assert t.end_time() == "24:15"

    def test_mark_complete_flips_flag(self):
        t = Task("Feed", "07:00", 10, "high", "Mochi")
        assert not t.completed
        t.mark_complete()
        assert t.completed

    def test_clone_pending_is_not_completed(self):
        t = Task("Feed", "07:00", 10, "high", "Mochi", "daily")
        t.mark_complete()
        clone = t.clone_pending()
        assert not clone.completed

    def test_clone_pending_inherits_fields(self):
        t = Task("Feed", "07:00", 10, "high", "Mochi", "daily")
        clone = t.clone_pending()
        assert clone.title == t.title
        assert clone.time == t.time
        assert clone.frequency == t.frequency

    def test_clone_gets_new_id(self):
        t = Task("Feed", "07:00", 10, "high", "Mochi", "daily")
        clone = t.clone_pending()
        assert clone.task_id != t.task_id

    def test_unique_task_ids(self):
        tasks = [Task(f"Task{i}", "08:00", 10, "low", "Rex") for i in range(5)]
        ids = {t.task_id for t in tasks}
        assert len(ids) == 5


# ── Pet ───────────────────────────────────────────────────────────────────────

class TestPet:
    def test_add_and_get_tasks(self):
        pet = Pet("Mochi", "cat")
        pet.add_task(Task("Play", "10:00", 20, "medium", "Mochi"))
        assert len(pet.get_tasks()) == 1

    def test_complete_task_returns_true(self):
        pet = Pet("Mochi", "cat")
        t = Task("Play", "10:00", 20, "medium", "Mochi")
        pet.add_task(t)
        assert pet.complete_task(t.task_id) is True
        assert pet.tasks[0].completed

    def test_complete_task_not_found_returns_false(self):
        pet = Pet("Mochi", "cat")
        assert pet.complete_task("nonexistent") is False

    def test_get_pending_excludes_done(self):
        pet = Pet("Mochi", "cat")
        t1 = Task("Feed", "07:00", 10, "high",   "Mochi")
        t2 = Task("Play", "10:00", 20, "medium", "Mochi")
        pet.add_task(t1)
        pet.add_task(t2)
        pet.complete_task(t1.task_id)
        pending = pet.get_pending_tasks()
        assert len(pending) == 1
        assert pending[0].title == "Play"


# ── Owner ─────────────────────────────────────────────────────────────────────

class TestOwner:
    def test_add_and_count_pets(self):
        o = Owner("Jordan")
        o.add_pet(Pet("Mochi", "cat"))
        assert len(o.get_pets()) == 1

    def test_get_pet_case_insensitive(self, owner):
        assert owner.get_pet("mochi") is not None
        assert owner.get_pet("MOCHI").name == "Mochi"

    def test_get_pet_not_found_returns_none(self, owner):
        assert owner.get_pet("Ghost") is None


# ── Scheduler: sort ───────────────────────────────────────────────────────────

class TestSchedulerSort:
    def test_two_tasks_across_pets_sorted(self, owner, scheduler):
        owner.get_pet("Rex").add_task(Task("Walk", "08:00", 30, "high",   "Rex"))
        owner.get_pet("Mochi").add_task(Task("Feed", "07:00", 10, "high", "Mochi"))
        result = scheduler.sort_tasks()
        assert result[0].time == "07:00"
        assert result[1].time == "08:00"

    def test_sort_preserves_all_tasks(self, owner, scheduler):
        times = ["10:00", "07:30", "09:00", "08:15"]
        for i, ts in enumerate(times):
            owner.get_pet("Rex").add_task(Task(f"Task{i}", ts, 10, "low", "Rex"))
        result_times = [t.time for t in scheduler.sort_tasks()]
        assert result_times == sorted(result_times)

    def test_sort_accepts_external_list(self, scheduler):
        t_list = [
            Task("B", "09:00", 10, "low", "Rex"),
            Task("A", "07:00", 10, "low", "Rex"),
        ]
        assert scheduler.sort_tasks(t_list)[0].title == "A"


# ── Scheduler: filter ─────────────────────────────────────────────────────────

class TestSchedulerFilter:
    def test_filter_by_pet_name(self, owner, scheduler):
        owner.get_pet("Rex").add_task(Task("Walk", "08:00", 30, "high",   "Rex"))
        owner.get_pet("Mochi").add_task(Task("Feed", "07:00", 10, "high", "Mochi"))
        rex_tasks = scheduler.filter_tasks(pet_name="Rex")
        assert len(rex_tasks) == 1
        assert all(t.pet_name == "Rex" for t in rex_tasks)

    def test_filter_pending_only(self, owner, scheduler):
        pet = owner.get_pet("Mochi")
        t1 = Task("Feed", "07:00", 10, "high",   "Mochi")
        t2 = Task("Play", "10:00", 20, "medium", "Mochi")
        pet.add_task(t1)
        pet.add_task(t2)
        pet.complete_task(t1.task_id)
        pending = scheduler.filter_tasks(completed=False)
        assert len(pending) == 1
        assert not pending[0].completed

    def test_filter_completed_only(self, owner, scheduler):
        pet = owner.get_pet("Rex")
        t = Task("Walk", "08:00", 30, "high", "Rex")
        pet.add_task(t)
        pet.complete_task(t.task_id)
        completed = scheduler.filter_tasks(completed=True)
        assert len(completed) == 1
        assert completed[0].completed

    def test_filter_combined_pet_and_status(self, owner, scheduler):
        pet = owner.get_pet("Mochi")
        pet.add_task(Task("Feed", "07:00", 10, "high", "Mochi"))
        result = scheduler.filter_tasks(pet_name="Mochi", completed=False)
        assert len(result) == 1


# ── Scheduler: conflict detection ────────────────────────────────────────────

class TestSchedulerConflicts:
    def test_detects_same_pet_overlap(self, owner, scheduler):
        mochi = owner.get_pet("Mochi")
        mochi.add_task(Task("Playtime",    "10:00", 30, "medium", "Mochi"))
        mochi.add_task(Task("Vet checkup", "10:15", 60, "high",   "Mochi"))
        assert len(scheduler.detect_conflicts()) == 1

    def test_no_conflict_sequential_tasks(self, owner, scheduler):
        rex = owner.get_pet("Rex")
        rex.add_task(Task("Walk",     "08:00", 30, "high",   "Rex"))
        rex.add_task(Task("Grooming", "09:00", 45, "medium", "Rex"))
        assert scheduler.detect_conflicts() == []

    def test_no_conflict_exactly_adjacent(self, owner, scheduler):
        # task A ends at 07:30, task B starts at 07:30 — touching but not overlapping
        mochi = owner.get_pet("Mochi")
        mochi.add_task(Task("Feed", "07:00", 30, "high",   "Mochi"))
        mochi.add_task(Task("Play", "07:30", 20, "medium", "Mochi"))
        assert scheduler.detect_conflicts() == []

    def test_cross_pet_overlap_is_not_a_conflict(self, owner, scheduler):
        owner.get_pet("Mochi").add_task(Task("Feed", "08:00", 30, "high", "Mochi"))
        owner.get_pet("Rex").add_task(Task("Walk",   "08:00", 30, "high", "Rex"))
        assert scheduler.detect_conflicts() == []

    def test_completed_tasks_excluded_from_conflicts(self, owner, scheduler):
        mochi = owner.get_pet("Mochi")
        t1 = Task("Playtime",    "10:00", 30, "medium", "Mochi")
        t2 = Task("Vet checkup", "10:15", 60, "high",   "Mochi")
        mochi.add_task(t1)
        mochi.add_task(t2)
        mochi.complete_task(t1.task_id)
        assert scheduler.detect_conflicts() == []


# ── Scheduler: recurrence ─────────────────────────────────────────────────────

class TestSchedulerRecurrence:
    def test_daily_task_regenerates_after_completion(self, owner, scheduler):
        mochi = owner.get_pet("Mochi")
        t = Task("Morning feed", "07:00", 10, "high", "Mochi", "daily")
        mochi.add_task(t)
        mochi.complete_task(t.task_id)
        new_tasks = scheduler.generate_recurring()
        assert len(new_tasks) == 1
        assert not new_tasks[0].completed
        assert new_tasks[0].title == t.title

    def test_weekly_task_regenerates(self, owner, scheduler):
        rex = owner.get_pet("Rex")
        t = Task("Grooming", "09:00", 45, "medium", "Rex", "weekly")
        rex.add_task(t)
        rex.complete_task(t.task_id)
        assert len(scheduler.generate_recurring()) == 1

    def test_once_frequency_does_not_regenerate(self, owner, scheduler):
        mochi = owner.get_pet("Mochi")
        t = Task("Vet visit", "14:00", 60, "high", "Mochi", "once")
        mochi.add_task(t)
        mochi.complete_task(t.task_id)
        assert scheduler.generate_recurring() == []

    def test_no_duplicate_on_second_call(self, owner, scheduler):
        mochi = owner.get_pet("Mochi")
        t = Task("Morning feed", "07:00", 10, "high", "Mochi", "daily")
        mochi.add_task(t)
        mochi.complete_task(t.task_id)
        scheduler.generate_recurring()           # creates one clone
        second_run = scheduler.generate_recurring()  # clone already pending
        assert len(second_run) == 0

    def test_recurring_across_multiple_pets(self, owner, scheduler):
        mochi = owner.get_pet("Mochi")
        rex = owner.get_pet("Rex")
        t1 = Task("Morning feed", "07:00", 10, "high", "Mochi", "daily")
        t2 = Task("Morning walk", "07:30", 30, "high", "Rex",   "daily")
        mochi.add_task(t1)
        rex.add_task(t2)
        mochi.complete_task(t1.task_id)
        rex.complete_task(t2.task_id)
        new_tasks = scheduler.generate_recurring()
        assert len(new_tasks) == 2
