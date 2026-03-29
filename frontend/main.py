import sys
from PySide6.QtWidgets import QApplication
from frontend.gui.main_window import MainWindow
from database.db_manager import DBManager
from backend.services.analysis_service import AnalysisService
from controllers.analysis_controller import AnalysisController


def main():

    app = QApplication(sys.argv)

    db = DBManager()
    service = AnalysisService(db)
    controller = AnalysisController(db, service)
    window = MainWindow(controller)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
    window.load_test_data()