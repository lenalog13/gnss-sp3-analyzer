from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton
)
from PySide6.QtCore import Signal


class HistoryWindow(QWidget):

    experiment_selected = Signal(int)  # передаём ID

    def __init__(self, db):
        super().__init__()

        self.db = db

        self.setWindowTitle("Experiment History")
        self.resize(600, 400)

        self.init_ui()
        self.load_data()

    def init_ui(self):

        layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels([
            "ID", "Name", "Created"
        ])

        self.btn_load = QPushButton("Load Experiment")

        layout.addWidget(self.table)
        layout.addWidget(self.btn_load)

        self.setLayout(layout)
        self.btn_load.clicked.connect(self.load_selected)

    def load_data(self):

        data = self.db.get_experiments()

        self.table.setRowCount(len(data))

        for i, row in enumerate(data):
            for j, value in enumerate(row):
                self.table.setItem(i, j, QTableWidgetItem(str(value)))

    def load_selected(self):

        row = self.table.currentRow()

        if row < 0:
            return

        exp_id_item = self.table.item(row, 0)

        if not exp_id_item:
            return

        exp_id = int(exp_id_item.text())

        self.experiment_selected.emit(exp_id)