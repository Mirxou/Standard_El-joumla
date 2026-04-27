#!/usr/bin/env python3
import sys
from PySide6.QtWidgets import QApplication
try:
    from src.ui.windows.main_window import MainWindow
except Exception:
    MainWindow = None

def main():
    app = QApplication(sys.argv)
    if MainWindow is None:
        # Fallback simple message if UI not importable
        print("MainWindow not available; desktop launcher cannot start UI.")
        sys.exit(0)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
