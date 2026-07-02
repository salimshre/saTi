"""
tests/test_dock_manager.py – Unit tests for the floating-window docking
logic (DockGroup / DockManager).

These tests never open a real Tk display. FakeWindow/FakeToplevel stand in
for FloatingWindow/tk.Toplevel, exposing just the handful of methods
dock_manager.py actually calls (winfo_x, winfo_y, winfo_width,
winfo_height, geometry, update_idletasks). That's enough to exercise the
real snapping/grouping/undocking math directly and cheaply, without a
windowing system or any GUI event loop.
"""

import pytest

from ui.floating.dock_manager import DockManager, DockGroup


# ----------------------------------------------------------------------
# Fakes
# ----------------------------------------------------------------------
class FakeToplevel:
    """Stands in for tk.Toplevel. Geometry is applied immediately (no
    async redraw lag), which is fine here: we're testing the docking
    math, not Tk's event loop timing."""

    def __init__(self, x, y, w, h):
        self._x, self._y, self._w, self._h = x, y, w, h

    def winfo_x(self):
        return self._x

    def winfo_y(self):
        return self._y

    def winfo_width(self):
        return self._w

    def winfo_height(self):
        return self._h

    def geometry(self, spec=None):
        if spec is None:
            return f"{self._w}x{self._h}+{self._x}+{self._y}"
        # Only "+x+y" moves are used by dock_manager.py
        assert spec.startswith("+")
        x_str, y_str = spec[1:].split("+")
        self._x, self._y = int(x_str), int(y_str)

    def update_idletasks(self):
        pass  # no-op: FakeToplevel never lags


class FakeWindow:
    """Stands in for FloatingWindow."""

    _all_windows = []  # mirrors FloatingWindow._all_windows

    def __init__(self, name, x, y, w=160, h=160):
        self.title_text = name
        self.top = FakeToplevel(x, y, w, h)
        self.group = None
        self.group_leader = None
        FakeWindow._all_windows.append(self)

    def __repr__(self):
        return f"<FakeWindow {self.title_text}>"


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------
@pytest.fixture
def manager():
    """A clean DockManager for each test.

    DockManager is a singleton (via __new__), so we reuse the same
    instance across tests but reset its mutable state -- this avoids
    leaking groups from one test into the next without fighting the
    singleton pattern.
    """
    dm = DockManager()
    dm.groups = []
    yield dm
    dm.groups = []


@pytest.fixture(autouse=True)
def reset_all_windows():
    """FakeWindow._all_windows is a class-level list (mirroring
    FloatingWindow._all_windows) -- clear it between tests so windows
    from one test can't be "seen" by another."""
    FakeWindow._all_windows = []
    yield
    FakeWindow._all_windows = []


# ----------------------------------------------------------------------
# Threshold / gap detection
# ----------------------------------------------------------------------
def test_finds_neighbor_within_dock_threshold(manager):
    a = FakeWindow("a", x=0, y=0, w=160, h=160)
    b = FakeWindow("b", x=180, y=0, w=160, h=160)  # 20px gap, < 30 threshold

    target, new_pos = manager.find_best_snap(a, [b])

    assert target is b
    # a should land with its right edge flush against b's left edge
    assert new_pos == (b.top.winfo_x() - a.top.winfo_width(), 0)


def test_ignores_neighbor_beyond_dock_threshold(manager):
    a = FakeWindow("a", x=0, y=0, w=160, h=160)
    b = FakeWindow("b", x=250, y=0, w=160, h=160)  # 90px gap, > 30 threshold

    target, new_pos = manager.find_best_snap(a, [b])

    assert target is None
    assert new_pos is None


def test_exact_flush_gap_still_counts_as_adjacent(manager):
    """Regression test: gap == 0 (windows already touching) must still be
    detected as a valid dock candidate, not silently excluded."""
    a = FakeWindow("a", x=0, y=0, w=160, h=160)
    b = FakeWindow("b", x=160, y=0, w=160, h=160)  # touching exactly, gap=0

    target, new_pos = manager.find_best_snap(a, [b])

    assert target is b
    assert new_pos == (0, 0)  # a is already exactly where it should be


def test_skips_meaningfully_overlapping_windows(manager):
    a = FakeWindow("a", x=0, y=0, w=160, h=160)
    b = FakeWindow("b", x=100, y=0, w=160, h=160)  # deep overlap

    target, new_pos = manager.find_best_snap(a, [b])

    assert target is None


def test_picks_closest_of_multiple_candidates(manager):
    a = FakeWindow("a", x=0, y=0, w=160, h=160)
    near = FakeWindow("near", x=170, y=0, w=160, h=160)   # 10px gap
    far = FakeWindow("far", x=0, y=185, w=160, h=160)     # 25px gap

    target, _ = manager.find_best_snap(a, [near, far])

    assert target is near


# ----------------------------------------------------------------------
# Docking / grouping
# ----------------------------------------------------------------------
def test_try_dock_creates_a_two_member_group(manager):
    a = FakeWindow("a", x=0, y=0)
    b = FakeWindow("b", x=180, y=0)

    docked = manager.try_dock(a)

    assert docked is True
    assert a.group is not None
    assert a.group is b.group
    assert len(a.group) == 2
    assert a.group.contains(a) and a.group.contains(b)


def test_try_dock_snaps_the_window_flush(manager):
    a = FakeWindow("a", x=0, y=0, w=160, h=160)
    b = FakeWindow("b", x=180, y=0, w=160, h=160)

    manager.try_dock(a)

    # a's right edge should now be flush against b's left edge
    assert a.top.winfo_x() + a.top.winfo_width() == b.top.winfo_x()


def test_try_dock_can_extend_an_existing_group_past_two():
    """Regression test for the main bug fixed this session: docking a
    window that already belongs to a 2+ member group must still be able
    to pull in a *new*, third window. This used to be silently blocked
    outright regardless of proximity.

    Note: proximity is judged from whichever window instance try_dock is
    called with (mirroring release-events coming from whichever window
    the user actually dragged) -- so we dock via `b`, the member that's
    actually sitting next to `c`, not `a`.
    """
    manager = DockManager()
    manager.groups = []

    a = FakeWindow("a", x=0, y=0, w=160, h=160)
    b = FakeWindow("b", x=180, y=0, w=160, h=160)
    c = FakeWindow("c", x=360, y=0, w=160, h=160)

    assert manager.try_dock(a) is True          # a + b become a group
    assert len(a.group) == 2

    docked_third = manager.try_dock(b)          # b is the member near c
    assert docked_third is True
    assert len(a.group) == 3
    assert a.group is b.group is c.group


def test_try_dock_does_not_redock_within_the_same_group(manager):
    a = FakeWindow("a", x=0, y=0)
    b = FakeWindow("b", x=180, y=0)
    manager.try_dock(a)

    # Nudging a right next to its own group member shouldn't do anything
    # weird -- there's nothing else to dock to.
    docked_again = manager.try_dock(a)
    assert docked_again is False
    assert len(a.group) == 2


# ----------------------------------------------------------------------
# Undocking / leader reassignment
# ----------------------------------------------------------------------
def test_undock_dissolves_a_two_member_group(manager):
    a = FakeWindow("a", x=0, y=0)
    b = FakeWindow("b", x=180, y=0)
    manager.try_dock(a)

    manager.undock(b)

    assert b.group is None
    assert b.group_leader is None
    assert a.group is None  # a two-member group dissolves entirely
    assert a.group_leader is None


def test_undocking_the_leader_promotes_a_new_leader():
    """Regression test: if the *leader* of a 3+ member group leaves,
    the group must promote a new leader rather than keep a dangling
    reference to a window that's no longer part of it."""
    manager = DockManager()
    manager.groups = []

    a = FakeWindow("a", x=0, y=0, w=160, h=160)
    b = FakeWindow("b", x=180, y=0, w=160, h=160)
    c = FakeWindow("c", x=360, y=0, w=160, h=160)
    manager.try_dock(a)  # a + b
    manager.try_dock(b)  # b (adjacent to c) pulls c in -> a, b, c grouped

    leader = a.group_leader
    assert leader is a

    manager.undock(a)

    assert a.group is None
    # The group must still exist with a *new* leader from the remaining
    # members -- not a stale reference to `a`.
    remaining_group = b.group
    assert remaining_group is not None
    assert remaining_group is c.group
    assert remaining_group.leader in (b, c)
    assert remaining_group.leader is not a
    assert b.group_leader is remaining_group.leader
    assert c.group_leader is remaining_group.leader


def test_group_move_by_keeps_relative_offsets(manager):
    a = FakeWindow("a", x=0, y=0, w=160, h=160)
    b = FakeWindow("b", x=160, y=0, w=160, h=160)
    manager.try_dock(a)

    offset_before = (
        b.top.winfo_x() - a.top.winfo_x(),
        b.top.winfo_y() - a.top.winfo_y(),
    )

    a.group.move_by(50, 30)

    offset_after = (
        b.top.winfo_x() - a.top.winfo_x(),
        b.top.winfo_y() - a.top.winfo_y(),
    )
    assert offset_before == offset_after


# ----------------------------------------------------------------------
# Preview (non-mutating) lookup
# ----------------------------------------------------------------------
def test_preview_snap_target_does_not_move_or_dock_anything(manager):
    a = FakeWindow("a", x=0, y=0, w=160, h=160)
    b = FakeWindow("b", x=180, y=0, w=160, h=160)

    target = manager.preview_snap_target(a, [b])

    assert target is b
    assert a.group is None  # preview must not actually dock
    assert a.top.winfo_x() == 0  # and must not move anything