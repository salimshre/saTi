from models.stopwatch import Stopwatch


def test_stopwatch_elapsed_uses_running_start_time():
    stopwatch = Stopwatch(label="Sprint")
    stopwatch.start_or_resume(100.0)

    assert round(stopwatch.elapsed(105.5), 2) == 5.5


def test_stopwatch_pause_accumulates_elapsed_time():
    stopwatch = Stopwatch(label="Workout")
    stopwatch.start_or_resume(50.0)
    stopwatch.pause(65.0)
    stopwatch.start_or_resume(80.0)
    stopwatch.pause(90.0)

    assert stopwatch.status == "paused"
    assert stopwatch.elapsed_paused == 25.0


def test_stopwatch_add_lap_returns_none_when_stopped():
    stopwatch = Stopwatch(label="Idle")

    assert stopwatch.add_lap(10.0) is None
    assert stopwatch.lap_times == []
