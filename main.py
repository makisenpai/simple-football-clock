import os
import sys

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from display_window import DisplayWindow
from control_window import ControlWindow

# ── Dark theme applied to the control panel ───────────────────────────────────
DARK_THEME = """
QWidget {
    background-color: #1a1a1a;
    color: #cccccc;
    font-family: 'Segoe UI', sans-serif;
    font-size: 15px;
}
QPushButton {
    background-color: #2a2a2a;
    color: #cccccc;
    border: 1px solid #444444;
    padding: 10px 18px;
    border-radius: 3px;
    min-height: 36px;
}
QPushButton:hover    { background-color: #383838; }
QPushButton:pressed  { background-color: #505050; }
QPushButton:disabled { color: #444444; border-color: #333333; }
QGroupBox {
    color: #777777;
    border: 1px solid #383838;
    border-radius: 4px;
    margin-top: 12px;
    padding: 10px;
    font-size: 13px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 8px;
    padding: 0 4px;
}
QLabel  { color: #cccccc; background: transparent; }
QFrame[frameShape="4"] { color: #333333; }  /* VLine */
"""


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")           # consistent look across Windows versions
    app.setStyleSheet(DARK_THEME)

    # ── App icon (taskbar + title bar) ────────────────────────────────
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS  # type: ignore[attr-defined]
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(base, "assets", "icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    screens = app.screens()
    primary   = screens[0]
    secondary = screens[1] if len(screens) > 1 else screens[0]

    # ── Display window on secondary screen ────────────────────────────
    display = DisplayWindow()
    display.setGeometry(secondary.geometry())
    display.show()

    # Reassign to the correct screen after the native handle is created
    handle = display.windowHandle()
    if handle:
        handle.setScreen(secondary)
        display.setGeometry(secondary.geometry())

    # ── Control panel on primary screen ──────────────────────────────
    control = ControlWindow(display)
    pg = primary.availableGeometry()
    control.move(pg.x() + 40, pg.y() + 40)
    control.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
