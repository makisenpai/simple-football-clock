from PyQt6.QtCore import QObject, QTimer, pyqtSignal


class MatchClock(QObject):
    """Football match clock.

    Emits `tick` every second with the current elapsed seconds.
    Emits `half_ended` and auto-stops when reaching 45:00 or 90:00
    for the first time.  Pressing start again resumes (injury time).
    """

    tick = pyqtSignal(int)       # current elapsed seconds
    half_ended = pyqtSignal(int) # emits the seconds value at auto-stop

    HALF_1_END = 45 * 60   # 2700
    HALF_2_END = 90 * 60   # 5400
    ET_1_END   = 105 * 60  # 6300
    ET_2_END   = 120 * 60  # 7200

    def __init__(self, parent=None):
        super().__init__(parent)
        self._seconds = 0
        self._auto_stopped = False
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)

    # ── internal ──────────────────────────────────────────────────────

    def _tick(self):
        self._seconds += 1
        self.tick.emit(self._seconds)
        if not self._auto_stopped:
            if self._seconds in (self.HALF_1_END, self.HALF_2_END,
                                 self.ET_1_END, self.ET_2_END):
                self._auto_stopped = True
                self._timer.stop()
                self.half_ended.emit(self._seconds)

    # ── public API ────────────────────────────────────────────────────

    def start(self):
        """Start or resume the clock."""
        self._auto_stopped = False
        if not self._timer.isActive():
            self._timer.start()

    def stop(self):
        """Stop the clock."""
        self._timer.stop()

    def set_time(self, seconds: int):
        """Jump to a specific time (stops the clock first)."""
        self._timer.stop()
        self._seconds = max(0, seconds)
        self._auto_stopped = False
        self.tick.emit(self._seconds)

    @property
    def seconds(self) -> int:
        return self._seconds

    @property
    def is_running(self) -> bool:
        return self._timer.isActive()
