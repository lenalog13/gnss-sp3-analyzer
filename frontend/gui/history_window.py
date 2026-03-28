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
        self.load_history()

    def init_ui(self):

        layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels([
            "ID", "Name", "Created"
        ])

        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)

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


    def load_history(self):

        fake_data = [
            (1, "2026-03-28 12:00", "calc1.sp3", "ref1.sp3"),
            (2, "2026-03-28 13:00", "calc2.sp3", "ref2.sp3"),
            (3, "2026-03-28 14:00", "calc3.sp3", "ref3.sp3"),
        ]

        self.table.setRowCount(len(fake_data))

        for i, row in enumerate(fake_data):
            for j, value in enumerate(row):
                self.table.setItem(i, j, QTableWidgetItem(str(value)))