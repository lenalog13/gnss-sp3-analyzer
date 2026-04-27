import sys
import requests
from PySide6.QtWidgets import QApplication
from frontend.gui.main_window import MainWindow

def main():
    try:
        requests.get("http://localhost:8080/experiments")
        print("Backend: OK")
    except:
        print("Backend: FAIL")

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()