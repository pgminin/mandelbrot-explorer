"""
Mandelbrot Explorer — Entry point principale.
Avvia l'applicazione PyQt6 per l'esplorazione del frattale di Mandelbrot.
"""
import sys
import os

# Aggiungi la root del progetto al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from gui.viewer_window import ViewerWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Mandelbrot Explorer")
    app.setApplicationVersion("1.0")

    # Antialiasing e HiDPI
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")

    window = ViewerWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
