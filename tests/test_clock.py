"""Tests for MatchClock logic.

Uses QCoreApplication (no display needed) so these run fine in headless CI.
We drive the clock by calling _tick() directly instead of waiting for a real timer.
"""
import pytest
from PyQt6.QtCore import QCoreApplication

from clock import MatchClock


@pytest.fixture(scope="session")
def qcore():
    app = QCoreApplication.instance() or QCoreApplication([])
    yield app


# ── initial state ──────────────────────────────────────────────────────────────

def test_initial_seconds(qcore):
    clock = MatchClock()
    assert clock.seconds == 0


def test_initial_not_running(qcore):
    clock = MatchClock()
    assert not clock.is_running


# ── set_time ──────────────────────────────────────────────────────────────────

def test_set_time_updates_seconds(qcore):
    clock = MatchClock()
    clock.set_time(300)
    assert clock.seconds == 300


def test_set_time_stops_clock(qcore):
    clock = MatchClock()
    clock.start()
    clock.set_time(100)
    assert not clock.is_running


def test_set_time_negative_clamps_to_zero(qcore):
    clock = MatchClock()
    clock.set_time(-99)
    assert clock.seconds == 0


def test_set_time_emits_tick(qcore):
    clock = MatchClock()
    received = []
    clock.tick.connect(received.append)
    clock.set_time(42)
    assert received == [42]


# ── start / stop ──────────────────────────────────────────────────────────────

def test_start_makes_running(qcore):
    clock = MatchClock()
    clock.start()
    assert clock.is_running
    clock.stop()


def test_stop_makes_not_running(qcore):
    clock = MatchClock()
    clock.start()
    clock.stop()
    assert not clock.is_running


def test_start_is_idempotent(qcore):
    clock = MatchClock()
    clock.start()
    clock.start()
    assert clock.is_running
    clock.stop()


# ── tick increments ───────────────────────────────────────────────────────────

def test_tick_increments_seconds(qcore):
    clock = MatchClock()
    clock.set_time(0)
    clock.start()
    clock._tick()
    assert clock.seconds == 1
    clock.stop()


def test_tick_emits_signal(qcore):
    clock = MatchClock()
    clock.set_time(0)
    clock.start()
    received = []
    clock.tick.connect(received.append)
    clock._tick()
    assert received == [1]
    clock.stop()


# ── auto-stop at boundaries ───────────────────────────────────────────────────

@pytest.mark.parametrize("stop_at", [
    MatchClock.HALF_1_END,
    MatchClock.HALF_2_END,
    MatchClock.ET_1_END,
    MatchClock.ET_2_END,
])
def test_auto_stop_at_boundary(qcore, stop_at):
    clock = MatchClock()
    clock.set_time(stop_at - 1)
    clock.start()

    emitted = []
    clock.half_ended.connect(emitted.append)
    clock._tick()  # crosses the boundary

    assert not clock.is_running, f"clock should have stopped at {stop_at}"
    assert emitted == [stop_at], f"half_ended should emit {stop_at}"


def test_no_auto_stop_before_boundary(qcore):
    clock = MatchClock()
    clock.set_time(MatchClock.HALF_1_END - 2)
    clock.start()
    clock._tick()  # one tick before boundary
    assert clock.is_running
    clock.stop()


# ── resume after auto-stop ────────────────────────────────────────────────────

def test_resume_after_auto_stop(qcore):
    clock = MatchClock()
    clock.set_time(MatchClock.HALF_1_END - 1)
    clock.start()
    clock._tick()  # auto-stops
    assert not clock.is_running

    clock.start()  # resume for injury time
    assert clock.is_running
    clock.stop()


def test_resume_does_not_re_trigger_same_boundary(qcore):
    """After resuming past 45:00, a further tick should NOT re-stop."""
    clock = MatchClock()
    clock.set_time(MatchClock.HALF_1_END - 1)
    clock.start()
    clock._tick()  # stops at 2700

    emitted = []
    clock.start()
    clock.half_ended.connect(emitted.append)
    clock._tick()  # now at 2701 — should keep running
    assert clock.is_running
    assert emitted == []
    clock.stop()
