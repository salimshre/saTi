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


def test_pause_freezes_remaining_time():
    timer = timer_module.Timer(label="Focus", duration=100)
    timer.remaining = 80
    timer.resume(10.0)

    timer.pause(25.0)

    assert timer.status == "paused"
    assert timer.remaining == 65
    assert timer.last_started_at is None
