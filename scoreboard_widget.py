from __future__ import annotations

from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QSizePolicy
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QFont

# Norwegian: H = Hjemmelag (Home), B = Bortelag (Away)
_PLACEHOLDER = ["H", "B"]


class ScoreboardWidget(QWidget):
    """Reusable scoreboard display.

    dynamic=True  — fills all available space, fonts scale on resize.
                    Used by the full-screen display window.
    dynamic=False — fixed scale layout used for the control panel preview.
    """

    _BASE_SCORE_FS: int = 72
    _BASE_CLOCK_FS: int = 36
    _BASE_LOGO_SZ:  int = 140
    _BASE_MARGIN:   int = 20
    _BASE_SPACING:  int = 16

    def __init__(self, scale: float = 1.0, dynamic: bool = False, parent=None):
        super().__init__(parent)
        self._scale = scale
        self._dynamic = dynamic
        self._score: list[int] = [0, 0]
        self._logo_paths: list[str | None] = [None, None]
        self._build_ui()

    # ── helpers ───────────────────────────────────────────────────────

    def _s(self, value: int) -> int:
        return max(1, round(value * self._scale))

    # ── construction ──────────────────────────────────────────────────

    def _build_ui(self):
        self.setStyleSheet("background-color: #000000;")

        outer = QVBoxLayout(self)

        if self._dynamic:
            outer.setContentsMargins(0, 0, 0, 0)
            outer.setSpacing(0)
        else:
            outer.setAlignment(Qt.AlignmentFlag.AlignCenter)
            outer.setContentsMargins(
                self._s(self._BASE_MARGIN), self._s(self._BASE_MARGIN),
                self._s(self._BASE_MARGIN), self._s(self._BASE_MARGIN),
            )

        # ── logos row (top) ──
        logo_row = QHBoxLayout()
        logo_row.setSpacing(self._s(self._BASE_SPACING) if not self._dynamic else 0)
        if not self._dynamic:
            logo_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.logo_labels: list[QLabel] = []
        for i in range(2):
            lbl = QLabel(_PLACEHOLDER[i])
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("color: #555555; background: transparent; border: none;")
            if self._dynamic:
                lbl.setSizePolicy(
                    QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
                )
            else:
                logo_sz = self._s(self._BASE_LOGO_SZ)
                lbl.setFixedSize(logo_sz, logo_sz)
                lbl.setFont(QFont("Courier New", max(6, logo_sz // 3), QFont.Weight.Bold))
            self.logo_labels.append(lbl)
            logo_row.addWidget(lbl, 1)

        # ── score (bottom, full width) ──
        self.score_label = QLabel("0 - 0")
        self.score_label.setFont(
            QFont("Courier New", self._s(self._BASE_SCORE_FS), QFont.Weight.Bold)
        )
        self.score_label.setStyleSheet("color: #ffffff; background: transparent;")
        self.score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if self._dynamic:
            self.score_label.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
            )

        # ── clock (below score, full width) ──
        self.clock_label = QLabel("00:00")
        self.clock_label.setFont(
            QFont("Courier New", self._s(self._BASE_CLOCK_FS), QFont.Weight.Bold)
        )
        self.clock_label.setStyleSheet("color: #ffffff; background: transparent;")
        self.clock_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if self._dynamic:
            self.clock_label.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
            )

        if self._dynamic:
            outer.addLayout(logo_row, 3)
            outer.addWidget(self.score_label, 2)
            outer.addWidget(self.clock_label, 1)
        else:
            outer.addLayout(logo_row)
            outer.addWidget(self.score_label)
            outer.addWidget(self.clock_label)

    # ── dynamic resize ────────────────────────────────────────────────

    def showEvent(self, event):
        super().showEvent(event)
        if self._dynamic:
            QTimer.singleShot(0, self._apply_dynamic_sizes)

    def resizeEvent(self, event):
        if self._dynamic:
            self._apply_dynamic_sizes()
        super().resizeEvent(event)

    def _apply_dynamic_sizes(self, w: int = 0, h: int = 0):
        if not w or not h:
            w, h = self.width(), self.height()
        if h <= 0 or w <= 0:
            return

        # logos fill the top portion, split side by side
        logo_sz  = min(w // 2, int(h * 0.50))
        logo_fs  = max(12, int(logo_sz * 0.55))

        # score and clock: use pixel size to avoid DPI point confusion
        score_px = max(10, int(h * 0.30))
        clock_px = max(8,  int(h * 0.16))

        score_font = QFont("Courier New")
        score_font.setPixelSize(score_px)
        score_font.setBold(True)
        self.score_label.setFont(score_font)

        clock_font = QFont("Courier New")
        clock_font.setPixelSize(clock_px)
        clock_font.setBold(True)
        self.clock_label.setFont(clock_font)

        for i, lbl in enumerate(self.logo_labels):
            if self._logo_paths[i]:
                px = QPixmap(self._logo_paths[i]).scaled(
                    logo_sz, logo_sz,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                lbl.setPixmap(px)
            else:
                f = QFont("Courier New")
                f.setPixelSize(max(12, logo_fs))
                f.setBold(True)
                lbl.setFont(f)

    # ── public update API ─────────────────────────────────────────────

    def update_clock(self, seconds: int):
        m, s = divmod(seconds, 60)
        self.clock_label.setText(f"{m:02d}:{s:02d}")

    def update_score(self, s1: int, s2: int):
        self._score = [s1, s2]
        self.score_label.setText(f"{s1} - {s2}")

    def update_logo(self, team_idx: int, path: str | None):
        self._logo_paths[team_idx] = path
        lbl = self.logo_labels[team_idx]

        if path:
            if self._dynamic:
                logo_sz = min(self.width() // 2, int(self.height() * 0.50))
            else:
                logo_sz = self._s(self._BASE_LOGO_SZ)
            px = QPixmap(path).scaled(
                logo_sz, logo_sz,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            lbl.setPixmap(px)
            lbl.setText("")
            lbl.setStyleSheet("background: transparent; border: none;")
        else:
            lbl.setPixmap(QPixmap())
            lbl.setText(_PLACEHOLDER[team_idx])
            lbl.setStyleSheet("color: #555555; background: transparent; border: none;")
            if not self._dynamic:
                logo_sz = self._s(self._BASE_LOGO_SZ)
                lbl.setFont(QFont("Courier New", max(6, logo_sz // 3), QFont.Weight.Bold))
