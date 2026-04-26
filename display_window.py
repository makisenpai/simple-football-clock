from __future__ import annotations

from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt
from scoreboard_canvas import ScoreboardCanvas


class DisplayWindow(QMainWindow):
    """Full-screen scoreboard shown on the secondary monitor.
    Press Escape to hide."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Match Display")
        self.setWindowFlags(
            Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint
        )

        self.canvas = ScoreboardCanvas()
        container = QWidget()
        container.setStyleSheet("background-color: #000000;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.canvas)
        self.setCentralWidget(container)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(event)

    def update_clock(self, seconds: int):
        self.canvas.update_clock(seconds)

    def update_score(self, s1: int, s2: int):
        self.canvas.update_score(s1, s2)

    def update_logo(self, team_idx: int, path: str | None):
        self.canvas.update_logo(team_idx, path)

    def set_mode(self, mode: str, solo_idx: int = 0):
        self.canvas.set_mode(mode, solo_idx)
