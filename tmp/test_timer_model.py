import models.timer as timer_module


def test_running_timer_restores_remaining_after_elapsed_time():
    timer = timer_module.Timer.from_dict(
        {
            "id": "timer-1",
            "label": "Tea",
            "duration": 120,
            "remaining": 90,
            "status": "running",
            "last_started_at": 1_000.0,
        }
    )

    timer.sync_state(1_030.0)

    assert timer.status == "running"
    assert timer.current_remaining(1_030.0) == 60


def test_timer_from_dict_does_not_sync_against_wall_clock():
    timer = timer_module.Timer.from_dict(
        {
            "id": "timer-restore",
            "label": "Restore",
            "duration": 120,
            "remaining": 90,
            "status": "running",
            "last_started_at": 1_000.0,
        }
    )

    assert timer.status == "running"
    assert timer.remaining == 90
    assert timer.last_started_at == 1_000.0
    assert timer.completed_at is None


def test_running_timer_completes_when_elapsed_time_exhausts_remaining():
    timer = timer_module.Timer.from_dict(
        {
            "id": "timer-2",
            "label": "Break",
            "duration": 30,
            "remaining": 5,
            "status": "running",
            "last_started_at": 200.0,
        }
    )

    timer.sync_state(210.0)

    assert timer.status == "completed"
    assert timer.remaining == 0
    assert timer.last_started_at is None
    assert timer.completed_at == 205.0


def test_restored_overdue_timer_uses_actual_due_time():
    timer = timer_module.Timer.from_dict(
        {
            "id": "timer-overdue",
            "label": "Overdue",
            "duration": 60,
            "remaining": 15,
            "status": "running",
            "last_started_at": 100.0,
        }
    )

    timer.sync_state(150.0)

    assert timer.status == "completed"
    assert timer.completed_at == 115.0
    assert timer.overdue_elapsed(150.0) == 35.0


def test_pause_freezes_remaining_time():
    timer = timer_module.Timer(label="Focus", duration=100)
    timer.remaining = 80
    timer.resume(10.0)

    timer.pause(25.0)

    assert timer.status == "paused"
    assert timer.remaining == 65
    assert timer.last_started_at is None
    assert timer.completed_at is None


def test_completed_timer_persists_completed_at():
    timer = timer_module.Timer.from_dict(
        {
            "id": "timer-3",
            "label": "Stretch",
            "duration": 60,
            "remaining": 0,
            "status": "completed",
            "completed_at": 500.0,
        }
    )

    assert timer.status == "completed"
    assert timer.completed_at == 500.0
    assert timer.overdue_elapsed(545.0) == 45.0
    assert timer.to_dict()["completed_at"] == 500.0


def test_reset_clears_completion_state():
    timer = timer_module.Timer(label="Reset me", duration=10)
    timer.remaining = 0
    timer.status = "completed"
    timer.completed_at = 100.0

    timer.reset()

    assert timer.status == "stopped"
    assert timer.remaining == 10
    assert timer.completed_at is None


def test_completed_timer_can_ring_again_after_reset_and_restart():
    timer = timer_module.Timer(label="Repeat", duration=5)
    timer.resume(10.0)
    timer.sync_state(15.0)
    first_completed_at = timer.completed_at

    timer.reset()
    timer.resume(20.0)
    timer.sync_state(25.0)

    assert first_completed_at == 15.0
    assert timer.status == "completed"
    assert timer.completed_at == 25.0
