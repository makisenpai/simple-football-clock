from __future__ import annotations

import os
import sys

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QGroupBox, QFrame, QLineEdit,
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
        layout.setSpacing(6)

        # ── top row: big time readout + status badge ──
        top = QHBoxLayout()
        self.time_display = QLabel("00:00")
        self.time_display.setFont(QFont("Courier New", 48, QFont.Weight.Bold))
        self.time_display.setStyleSheet("color: #ddaa00;")
        top.addWidget(self.time_display)
        top.addStretch()
        self.status_label = QLabel("Stopped")
        self.status_label.setStyleSheet("color: #666666; font-size: 16px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        top.addWidget(self.status_label)
        layout.addLayout(top)

        # ── start / stop ──
        run_row = QHBoxLayout()
        self.btn_start = QPushButton("▶  Start")
        self.btn_stop  = QPushButton("⏸  Stop")
        self.btn_start.clicked.connect(self._start)
        self.btn_stop.clicked.connect(self._stop)
        run_row.addWidget(self.btn_start)
        run_row.addWidget(self.btn_stop)
        layout.addLayout(run_row)

        # ── regular-time presets ──
        preset_row = QHBoxLayout()
        btn_set_0  = QPushButton("Set  00:00")
        btn_set_45 = QPushButton("Set  45:00")
        btn_set_0.clicked.connect(lambda: self._set_preset(0))
        btn_set_45.clicked.connect(lambda: self._set_preset(45 * 60))
        preset_row.addWidget(btn_set_0)
        preset_row.addWidget(btn_set_45)
        layout.addLayout(preset_row)

        # ── "More" toggle button ──
        self._btn_more = QPushButton("▸  More options")
        self._btn_more.setStyleSheet(
            "QPushButton { background: transparent; border: none; "
            "color: #666666; font-size: 12px; padding: 2px 0; min-height: 0; }"
            "QPushButton:hover { color: #999999; background: transparent; }"
        )
        self._btn_more.setFixedHeight(20)
        self._btn_more.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_more.clicked.connect(self._toggle_more)
        layout.addWidget(self._btn_more)

        # ── collapsible drawer ──
        self._drawer = QWidget()
        drawer_layout = QVBoxLayout(self._drawer)
        drawer_layout.setContentsMargins(0, 0, 0, 0)
        drawer_layout.setSpacing(6)

        et_row = QHBoxLayout()
        btn_set_90  = QPushButton("ET  90:00")
        btn_set_105 = QPushButton("ET  105:00")
        for btn in (btn_set_90, btn_set_105):
            btn.setFixedHeight(32)
            btn.setStyleSheet("font-size: 12px;")
        btn_set_90.clicked.connect(lambda: self._set_preset(90 * 60))
        btn_set_105.clicked.connect(lambda: self._set_preset(105 * 60))
        et_row.addWidget(btn_set_90)
        et_row.addWidget(btn_set_105)
        drawer_layout.addLayout(et_row)

        custom_row = QHBoxLayout()
        self.time_input = QLineEdit()
        self.time_input.setPlaceholderText("MM:SS")
        self.time_input.setMaximumWidth(100)
        self.time_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn_set_custom = QPushButton("Set Time")
        self.time_input.returnPressed.connect(self._set_custom_time)
        btn_set_custom.clicked.connect(self._set_custom_time)
        custom_row.addWidget(self.time_input)
        custom_row.addWidget(btn_set_custom)
        custom_row.addStretch()
        drawer_layout.addLayout(custom_row)

        self._drawer.setVisible(False)
        layout.addWidget(self._drawer)

        self._refresh_clock_buttons()
        return grp

    def _toggle_more(self):
        visible = not self._drawer.isVisible()
        self._drawer.setVisible(visible)
        self._btn_more.setText("▾  More options" if visible else "▸  More options")
        # let the window shrink/grow naturally
        self.adjustSize()

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
            title.setStyleSheet("color: #aaaaaa; font-size: 16px;")
            col.addWidget(title)

            # score +/- row
            row = QHBoxLayout()
            row.setAlignment(Qt.AlignmentFlag.AlignCenter)

            btn_minus = QPushButton("−")
            btn_minus.setFixedSize(48, 48)
            btn_minus.setStyleSheet("font-size: 26px; font-weight: bold;")

            val_lbl = QLabel("0")
            val_lbl.setFont(QFont("Courier New", 30, QFont.Weight.Bold))
            val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            val_lbl.setMinimumWidth(60)
            self._score_value_labels.append(val_lbl)

            btn_plus = QPushButton("+")
            btn_plus.setFixedSize(48, 48)
            btn_plus.setStyleSheet("font-size: 26px; font-weight: bold;")

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

    def _start(self):
        self.clock.start()
        self._refresh_clock_buttons()
        secs = self.clock.seconds
        if secs < 45 * 60:
            self.status_label.setText("▶  1st Half")
        elif secs < 90 * 60:
            self.status_label.setText("▶  2nd Half")
        elif secs < 105 * 60:
            self.status_label.setText("▶  Extra Time 1")
        else:
            self.status_label.setText("▶  Extra Time 2")

    def _set_preset(self, seconds: int):
        self.clock.set_time(seconds)
        self._refresh_clock_buttons()
        m, s = divmod(seconds, 60)
        self.status_label.setText(f"Set to {m:02d}:{s:02d}")

    def _set_custom_time(self):
        text = self.time_input.text().strip()
        try:
            if ":" in text:
                parts = text.split(":")
                seconds = int(parts[0]) * 60 + int(parts[1])
            else:
                seconds = int(text)
            self.clock.set_time(seconds)
            self._refresh_clock_buttons()
            m, s = divmod(seconds, 60)
            self.status_label.setText(f"Set to {m:02d}:{s:02d}")
            self.time_input.clear()
        except (ValueError, IndexError):
            self.time_input.setStyleSheet("border: 1px solid red;")
            self.time_input.setText(text)
            return
        self.time_input.setStyleSheet("")

    def _stop(self):
        self.clock.stop()
        self._refresh_clock_buttons()
        self.status_label.setText("⏸  Stopped")

    def _on_tick(self, seconds: int):
        m, s = divmod(seconds, 60)
        self.time_display.setText(f"{m:02d}:{s:02d}")
        self.preview.update_clock(seconds)
        self.display.update_clock(seconds)

    def _on_half_ended(self, seconds: int):
        self._refresh_clock_buttons()
        labels = {
            45 * 60:  "⏸  Half Time",
            90 * 60:  "⏸  Full Time",
            105 * 60: "⏸  Extra Time 1 Ended",
            120 * 60: "⏸  Full Time (AET)",
        }
        self.status_label.setText(labels.get(seconds, "⏸  Stopped"))

    def _refresh_clock_buttons(self):
        running = self.clock.is_running
        self.btn_start.setEnabled(not running)
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
