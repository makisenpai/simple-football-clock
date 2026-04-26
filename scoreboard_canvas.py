from __future__ import annotations

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QRect, QTimer
from PyQt6.QtGui import QPainter, QFont, QColor, QPixmap, QFontMetrics


class ScoreboardCanvas(QWidget):
    """Paints the scoreboard directly onto the widget surface.
    No layouts, no QLabels — pure QPainter so font sizes are guaranteed."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)
        self._score = [0, 0]
        self._clock_text = "00:00"
        self._logo_paths: list[str | None] = [None, None]
        self._logos: list[QPixmap | None] = [None, None]
        self._mode: str = "normal"   # "normal" | "black" | "logo"
        self._solo_idx: int = 0      # which logo to show in "logo" mode

    # ── public update API ─────────────────────────────────────────────

    def update_clock(self, seconds: int):
        m, s = divmod(seconds, 60)
        self._clock_text = f"{m:02d}:{s:02d}"
        self.update()

    def update_score(self, s1: int, s2: int):
        self._score = [s1, s2]
        self.update()

    def update_logo(self, team_idx: int, path: str | None):
        self._logo_paths[team_idx] = path
        if path:
            self._logos[team_idx] = QPixmap(path)
        else:
            self._logos[team_idx] = None
        self.update()

    def set_mode(self, mode: str, solo_idx: int = 0):
        """Switch display mode.
        mode: 'normal' | 'black' | 'logo'
        solo_idx: team index (0 or 1) when mode == 'logo'
        """
        self._mode = mode
        self._solo_idx = solo_idx
        self.update()

    # ── painting ──────────────────────────────────────────────────────

    def paintEvent(self, event):
        w = self.width()
        h = self.height()
        if w <= 0 or h <= 0:
            return

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # ── black screen mode ────────────────────────────────────────
        if self._mode == "black":
            p.fillRect(0, 0, w, h, QColor(0, 0, 0))
            p.end()
            return

        # ── single logo mode ─────────────────────────────────────────
        if self._mode == "logo":
            p.fillRect(0, 0, w, h, QColor(0, 0, 0))
            pm = self._logos[self._solo_idx]
            if pm and not pm.isNull():
                max_size = int(min(w, h) * 0.85)
                scaled = pm.scaled(
                    max_size, max_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                px = (w - scaled.width()) // 2
                py = (h - scaled.height()) // 2
                p.drawPixmap(px, py, scaled)
            else:
                label = "H" if self._solo_idx == 0 else "B"
                font = QFont("Courier New")
                font.setPixelSize(int(min(w, h) * 0.5))
                font.setBold(True)
                p.setFont(font)
                p.setPen(QColor(80, 80, 80))
                p.drawText(QRect(0, 0, w, h), Qt.AlignmentFlag.AlignCenter, label)
            p.end()
            return

        # background
        p.fillRect(0, 0, w, h, QColor(0, 0, 0))

        # ── zone heights ─────────────────────────────────────────────
        # logos: top 40% | score: next 30% | clock: bottom 30%
        logo_h  = int(h * 0.40)
        score_h = int(h * 0.30)
        clock_h = h - logo_h - score_h

        score_y = logo_h
        clock_y = logo_h + score_h

        # ── logos ────────────────────────────────────────────────────
        half_w = w // 2
        logo_max = min(half_w - 20, logo_h - 20)

        placeholder_font = QFont("Courier New")
        placeholder_font.setPixelSize(max(20, int(logo_max * 0.7)))
        placeholder_font.setBold(True)

        for i in range(2):
            x_centre = half_w // 2 + i * half_w
            y_centre = logo_h // 2

            if self._logos[i] and not self._logos[i].isNull():
                pm = self._logos[i].scaled(
                    logo_max, logo_max,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                px = x_centre - pm.width() // 2
                py = y_centre - pm.height() // 2
                p.drawPixmap(px, py, pm)
            else:
                label = "H" if i == 0 else "B"
                p.setFont(placeholder_font)
                p.setPen(QColor(80, 80, 80))
                r = QRect(i * half_w, 0, half_w, logo_h)
                p.drawText(r, Qt.AlignmentFlag.AlignCenter, label)

        # ── score ────────────────────────────────────────────────────
        score_text = f"{self._score[0]}  -  {self._score[1]}"
        score_font = QFont("Courier New")
        score_font.setPixelSize(int(score_h * 0.82))
        score_font.setBold(True)
        p.setFont(score_font)
        p.setPen(QColor(255, 255, 255))
        score_rect = QRect(0, score_y, w, score_h)
        p.drawText(score_rect, Qt.AlignmentFlag.AlignCenter, score_text)

        # ── clock ────────────────────────────────────────────────────
        clock_font = QFont("Courier New")
        clock_font.setPixelSize(int(clock_h * 0.80))
        clock_font.setBold(True)
        p.setFont(clock_font)
        p.setPen(QColor(255, 255, 255))
        clock_rect = QRect(0, clock_y, w, clock_h)
        p.drawText(clock_rect, Qt.AlignmentFlag.AlignCenter, self._clock_text)

        p.end()
