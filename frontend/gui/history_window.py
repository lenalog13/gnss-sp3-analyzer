from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QHeaderView
)
from PySide6.QtCore import Signal


class HistoryWindow(QWidget):

    experiment_selected = Signal(int)  # передаём ID

    def __init__(self, db):
        super().__init__()

        self.db = db

        self.setWindowTitle("Experiment History")
        self.resize(700, 500)

        self.init_ui()
        self.load_history()

    def init_ui(self):

        layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(4)  # Добавляем колонку для спутников
        self.table.setHorizontalHeaderLabels([
            "ID", "Name", "Created", "Satellites"
        ])

        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)

        self.btn_load = QPushButton("Load Experiment")

        layout.addWidget(self.table)
        layout.addWidget(self.btn_load)

        self.setLayout(layout)
        self.btn_load.clicked.connect(self.load_selected)

    def load_history(self):
        """Load real data from database"""
        try:
            data = self.db.get_experiments()
            
            if not data:
                # Show message if no data
                self.table.setRowCount(1)
                self.table.setItem(0, 0, QTableWidgetItem("No experiments found"))
                return
            
            self.table.setRowCount(len(data))
            
            for i, row in enumerate(data):
                # row format: (id, name, created_at)
                exp_id = row[0]
                name = row[1]
                created_at = row[2]
                
                # Get satellites for this experiment
                satellites = self.db.get_satellites(exp_id)
                satellites_str = ', '.join(satellites) if satellites else "No satellites"
                
                # Add to table
                self.table.setItem(i, 0, QTableWidgetItem(str(exp_id)))
                self.table.setItem(i, 1, QTableWidgetItem(str(name)))
                self.table.setItem(i, 2, QTableWidgetItem(str(created_at)))
                self.table.setItem(i, 3, QTableWidgetItem(satellites_str))
                    
            # Auto-resize columns
            self.table.resizeColumnsToContents()
            
        except Exception as e:
            print(f"Error loading history: {e}")
            self.table.setRowCount(1)
            self.table.setItem(0, 0, QTableWidgetItem(f"Error: {str(e)}"))

    def load_selected(self):
        """Emit signal with selected experiment ID"""
        row = self.table.currentRow()
        
        if row < 0:
            return
            
        exp_id_item = self.table.item(row, 0)
        
        if not exp_id_item or exp_id_item.text() == "No experiments found":
            return
            
        try:
            exp_id = int(exp_id_item.text())
            self.experiment_selected.emit(exp_id)
            self.close()  # Close window after selection
        except ValueError:
            print("Invalid experiment ID")