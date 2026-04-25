from __future__ import annotations

import os
import sys

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QGroupBox, QFrame,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from scoreboard_widget import ScoreboardWidget
from clock import MatchClock


class ControlWindow(QMainWindow):
    """Control panel window – lives on the primary monitor.

    Manages the MatchClock, scores, and logo paths.
    Propagates all changes to both the mini preview and the DisplayWindow.
    """

    def __init__(self, display_window, parent=None):
        super().__init__(parent)
        self.display = display_window
        self.setWindowTitle("Sports Clock — Control Panel")
        self.setMinimumWidth(540)

        self._score: list[int] = [0, 0]
        self._logo_paths: list[str | None] = [None, None]

        self.clock = MatchClock(self)
        self.clock.tick.connect(self._on_tick)
        self.clock.half_ended.connect(self._on_half_ended)

        self._build_ui()

    # ── UI construction ───────────────────────────────────────────────

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        layout.addWidget(self._make_preview_group())
        layout.addWidget(self._make_clock_group())
        layout.addWidget(self._make_score_group())
        layout.addWidget(self._make_display_group())

    # ── group builders ────────────────────────────────────────────────

    def _make_preview_group(self) -> QGroupBox:
        grp = QGroupBox("Preview")
        inner = QVBoxLayout(grp)
        inner.setContentsMargins(6, 6, 6, 6)
        self.preview = ScoreboardWidget(scale=0.36)
        inner.addWidget(self.preview)
        return grp

    def _make_clock_group(self) -> QGroupBox:
        grp = QGroupBox("Clock")
        layout = QVBoxLayout(grp)
        layout.setSpacing(8)

        # ── top row: big time readout + status badge ──
        top = QHBoxLayout()
        self.time_display = QLabel("00:00")
        self.time_display.setFont(QFont("Courier New", 34, QFont.Weight.Bold))
        self.time_display.setStyleSheet("color: #ddaa00;")
        top.addWidget(self.time_display)
        top.addStretch()
        self.status_label = QLabel("Stopped")
        self.status_label.setStyleSheet("color: #666666; font-size: 13px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        top.addWidget(self.status_label)
        layout.addLayout(top)

        # ── half-start buttons ──
        half_row = QHBoxLayout()
        self.btn_1st = QPushButton("▶  Start 1st Half  (00:00)")
        self.btn_2nd = QPushButton("▶  Start 2nd Half  (45:00)")
        self.btn_1st.clicked.connect(lambda: self._start_half(0))
        self.btn_2nd.clicked.connect(lambda: self._start_half(45 * 60))
        half_row.addWidget(self.btn_1st)
        half_row.addWidget(self.btn_2nd)
        layout.addLayout(half_row)

        # ── resume / stop / reset ──
        ctrl_row = QHBoxLayout()
        self.btn_resume = QPushButton("▶  Resume")
        self.btn_stop   = QPushButton("⏸  Stop")
        self.btn_reset  = QPushButton("↺  Reset to 00:00")
        self.btn_resume.clicked.connect(self._resume)
        self.btn_stop.clicked.connect(self._stop)
        self.btn_reset.clicked.connect(self._reset)
        ctrl_row.addWidget(self.btn_resume)
        ctrl_row.addWidget(self.btn_stop)
        ctrl_row.addWidget(self.btn_reset)
        layout.addLayout(ctrl_row)

        self._refresh_clock_buttons()
        return grp

    def _make_score_group(self) -> QGroupBox:
        grp = QGroupBox("Score & Teams")
        layout = QHBoxLayout(grp)
        layout.setSpacing(20)

        self._score_value_labels: list[QLabel] = []

        for i in range(2):
            col = QVBoxLayout()
            col.setAlignment(Qt.AlignmentFlag.AlignTop)
            col.setSpacing(6)

            title = QLabel(f"Team {i + 1}")
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            title.setStyleSheet("color: #aaaaaa; font-size: 13px;")
            col.addWidget(title)

            # score +/- row
            row = QHBoxLayout()
            row.setAlignment(Qt.AlignmentFlag.AlignCenter)

            btn_minus = QPushButton("−")
            btn_minus.setFixedSize(36, 36)
            btn_minus.setStyleSheet("font-size: 20px; font-weight: bold;")

            val_lbl = QLabel("0")
            val_lbl.setFont(QFont("Courier New", 22, QFont.Weight.Bold))
            val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            val_lbl.setMinimumWidth(46)
            self._score_value_labels.append(val_lbl)

            btn_plus = QPushButton("+")
            btn_plus.setFixedSize(36, 36)
            btn_plus.setStyleSheet("font-size: 20px; font-weight: bold;")

            btn_minus.clicked.connect(lambda checked, idx=i: self._change_score(idx, -1))
            btn_plus.clicked.connect(lambda checked, idx=i: self._change_score(idx, +1))

            row.addWidget(btn_minus)
            row.addWidget(val_lbl)
            row.addWidget(btn_plus)
            col.addLayout(row)

            # logo button
            btn_logo = QPushButton("Change Logo…")
            btn_logo.clicked.connect(lambda checked, idx=i: self._change_logo(idx))
            col.addWidget(btn_logo)

            layout.addLayout(col)

            # vertical divider between the two teams
            if i == 0:
                sep = QFrame()
                sep.setFrameShape(QFrame.Shape.VLine)
                sep.setStyleSheet("color: #333333;")
                layout.addWidget(sep)

        return grp

    def _make_display_group(self) -> QGroupBox:
        """Small group with a button to bring back the display window."""
        grp = QGroupBox("Display Window")
        row = QHBoxLayout(grp)
        btn_show = QPushButton("Show Display Window")
        btn_show.clicked.connect(self._show_display)
        row.addWidget(btn_show)
        row.addStretch()
        return grp

    # ── clock event handlers ──────────────────────────────────────────

    def _start_half(self, from_seconds: int):
        self.clock.set_time(from_seconds)
        self.clock.start()
        self._refresh_clock_buttons()
        half = "1st Half" if from_seconds == 0 else "2nd Half"
        self.status_label.setText(f"▶  {half}")

    def _resume(self):
        self.clock.start()
        self._refresh_clock_buttons()
        secs = self.clock.seconds
        if secs < 45 * 60:
            self.status_label.setText("▶  1st Half")
        elif secs < 90 * 60:
            self.status_label.setText("▶  2nd Half")
        else:
            self.status_label.setText("▶  Extra Time")

    def _stop(self):
        self.clock.stop()
        self._refresh_clock_buttons()
        self.status_label.setText("⏸  Stopped")

    def _reset(self):
        self.clock.set_time(0)
        self._refresh_clock_buttons()
        self.status_label.setText("Stopped")

    def _on_tick(self, seconds: int):
        m, s = divmod(seconds, 60)
        self.time_display.setText(f"{m:02d}:{s:02d}")
        self.preview.update_clock(seconds)
        self.display.update_clock(seconds)

    def _on_half_ended(self, seconds: int):
        self._refresh_clock_buttons()
        if seconds == 45 * 60:
            self.status_label.setText("⏸  Half Time")
        else:
            self.status_label.setText("⏸  Full Time")

    def _refresh_clock_buttons(self):
        running = self.clock.is_running
        self.btn_resume.setEnabled(not running)
        self.btn_stop.setEnabled(running)

    # ── score & logo handlers ─────────────────────────────────────────

    def _change_score(self, team_idx: int, delta: int):
        self._score[team_idx] = max(0, self._score[team_idx] + delta)
        self._score_value_labels[team_idx].setText(str(self._score[team_idx]))
        self.preview.update_score(*self._score)
        self.display.update_score(*self._score)

    @staticmethod
    def _logos_dir() -> str:
        """Return the logos folder path.

        When running as a frozen PyInstaller bundle, prefer a 'logos'
        folder sitting next to the .exe so users can drop images there
        without touching the _internal bundle.  Fall back to the bundled
        folder (or the source-tree folder when running from source).
        """
        if getattr(sys, 'frozen', False):
            # next to the .exe
            ext = os.path.join(os.path.dirname(sys.executable), "logos")
            if os.path.isdir(ext):
                return ext
            # fallback: bundled copy inside _internal
            return os.path.join(sys._MEIPASS, "logos")  # type: ignore[attr-defined]
        # running from source
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "logos")

    def _change_logo(self, team_idx: int):
        logos_dir = self._logos_dir()
        os.makedirs(logos_dir, exist_ok=True)
        path, _ = QFileDialog.getOpenFileName(
            self,
            f"Select Logo for Team {team_idx + 1}",
            logos_dir,
            "Images (*.png *.jpg *.jpeg *.bmp *.ico)",
        )
        if path:
            self._logo_paths[team_idx] = path
            self.preview.update_logo(team_idx, path)
            self.display.update_logo(team_idx, path)

    # ── display window helper ─────────────────────────────────────────

    def _show_display(self):
        self.display.show()
        self.display.raise_()
