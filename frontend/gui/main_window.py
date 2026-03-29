from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QFileDialog, QGridLayout,
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QTabWidget, QToolBar, QSplitter, QStyle, QApplication
)
from PySide6.QtCore import ( Qt, QSize )
import pyqtgraph as pg
import numpy as np
from database.db_manager import DBManager
from backend.services.analysis_service import AnalysisService
from controllers.analysis_controller import AnalysisController
from gui.history_window import HistoryWindow


class MainWindow(QMainWindow):

    def __init__(self, controller):
        super().__init__()
        self.controller = controller

        self.setWindowTitle("GNSS SP3 Analyzer")
        self.setMinimumSize(1000, 700)
        self.resize(1050, 750)

        self.init_ui()

    # ---------------- UI ---------------- #

    def init_ui(self):
        self.setStyleSheet("""
        QWidget {
            font-size: 12px;
        }

        QLineEdit {
            background-color: #2b2b2b;
            border: 1px solid #444;
            border-radius: 4px;
            padding: 4px;
        }

        QPushButton {
            background-color: #3a3a3a;
            border: 1px solid #555;
            border-radius: 5px;
            padding: 4px 8px;
        }

        QPushButton:hover {
            background-color: #4a4a4a;
        }

        QComboBox {
            background-color: #2b2b2b;
            border: 1px solid #444;
            border-radius: 4px;
            padding: 3px;
        }
        """)

        self.create_toolbar()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Верхняя панель (пути)
        main_layout.addWidget(self.create_file_panel())

        # Центральная область
        splitter = QSplitter(Qt.Horizontal)

        splitter.addWidget(self.create_plot_tabs())
        splitter.addWidget(self.create_statistics_panel())

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter)

        main_layout.setStretch(1, 5)  # графики
        main_layout.setStretch(2, 2)  # таблица

        # Таблица
        self.table = self.create_table()
        self.table.setMaximumHeight(200)
        main_layout.addWidget(self.table)

        central_widget.setLayout(main_layout)

    # ---------------- Toolbar ---------------- #

    def create_toolbar(self):

        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        toolbar.setIconSize(QSize(18, 18))

        btn_load = QPushButton("📂 Load")

        btn_run = QPushButton("▶ Run")
        btn_run.clicked.connect(self.load_test_data)

        btn_export = QPushButton("💾 Export")

        btn_history = QPushButton("🕓 History")
        btn_history.clicked.connect(self.open_history)


        toolbar.addWidget(btn_load)
        toolbar.addWidget(btn_run)
        toolbar.addWidget(btn_export)
        toolbar.addWidget(btn_history)

    # ---------------- File Panel ---------------- #

    def create_file_panel(self):

        layout = QVBoxLayout()

        layout.addLayout(self.create_file_row("Calculated SP3:", "calc"))
        layout.addLayout(self.create_file_row("Reference SP3:", "ref"))
        layout.addLayout(self.create_file_row("CLK file:", "clk"))

        # Satellite selector
        layout.addSpacing(10)
        sat_layout = QHBoxLayout()
        sat_layout.setSpacing(8)

        label = QLabel("Satellite:")
        label.setMinimumWidth(130)

        self.satellite_box = QComboBox()
        self.satellite_box.setMinimumWidth(200)
        self.satellite_box.setMaximumWidth(250)

        sat_layout.addWidget(label)
        sat_layout.addWidget(self.satellite_box)
        sat_layout.addStretch()

        layout.addLayout(sat_layout)

        container = QWidget()
        container.setLayout(layout)
        container.setMinimumHeight(140)
        container.setMaximumHeight(120)

        return container


    def create_file_row(self, label_text, file_type):

        layout = QHBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        label = QLabel(label_text)
        label.setMinimumWidth(130)
        label.setAlignment(Qt.AlignVCenter)

        line_edit = QLineEdit()
        line_edit.setMinimumHeight(26)

        button = QPushButton("Browse")
        button.setMinimumHeight(26)
        button.setFixedWidth(90)

        button.clicked.connect(lambda: self.select_file(line_edit))

        setattr(self, f"{file_type}_path", line_edit)

        layout.addWidget(label)
        layout.addWidget(line_edit)
        layout.addWidget(button)
        layout.setContentsMargins(0, 2, 0, 2)

        return layout

    def select_file(self, line_edit):

        path, _ = QFileDialog.getOpenFileName(self, "Select file")

        if path:
            line_edit.setText(path)

    # ---------------- Plot Area ---------------- #

    def create_plot_tabs(self):

        tabs = QTabWidget()

        self.orbit_plot = pg.PlotWidget(title="Orbit Errors (XYZ)")
        legend = self.orbit_plot.addLegend(offset=(10, 10))
        legend.setBrush((30, 30, 30, 200))   
        legend.setPen((200, 200, 200))       
        self.orbit_plot.addLegend()

        self.rtn_plot = pg.PlotWidget(title="RTN Errors")
        legend = self.rtn_plot.addLegend(offset=(10, 10))
        legend.setBrush((30, 30, 30, 200))   
        legend.setPen((200, 200, 200)) 
        self.rtn_plot.addLegend()

        self.clock_plot = pg.PlotWidget(title="Clock Bias")

        pg.setConfigOption('background', '#1e1e1e')
        pg.setConfigOption('foreground', '#cccccc')

        self.orbit_plot.setContentsMargins(5, 5, 5, 5)
        self.rtn_plot.setContentsMargins(5, 5, 5, 5)
        self.clock_plot.setContentsMargins(5, 5, 5, 5)

        tabs.addTab(self.orbit_plot, "Orbit")
        tabs.addTab(self.rtn_plot, "RTN")
        tabs.addTab(self.clock_plot, "Clock")

        for plot in [self.orbit_plot, self.rtn_plot, self.clock_plot]:
            plot.showGrid(x=True, y=True, alpha=0.3)

        return tabs

    # ---------------- Statistics ---------------- #

    def create_statistics_panel(self):

        widget = QWidget()
        layout = QGridLayout()

        stats = [
            "RMS X", "RMS Y", "RMS Z", "RMS 3D",
            "RMS R", "RMS T", "RMS N",
            "Mean", "Max", "Clock RMS"
        ]

        self.stats_labels = {}

        for i, stat in enumerate(stats):

            label_name = QLabel(stat)
            label_value = QLabel("---")

            label_name.setStyleSheet("color: #aaaaaa;")
            label_value.setStyleSheet("font-family: menlo;")

            label_name.setAlignment(Qt.AlignLeft)
            label_value.setAlignment(Qt.AlignRight)

            layout.addWidget(label_name, i, 0)
            layout.addWidget(label_value, i, 1)

            self.stats_labels[stat] = label_value

        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)

        widget.setLayout(layout)
        return widget

    # ---------------- Table ---------------- #

    def create_table(self):

        table = QTableWidget()
        table.setColumnCount(8)

        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        table.setShowGrid(False)

        table.setHorizontalHeaderLabels([
            "Epoch", "Sat", "dX", "dY", "dZ",
            "dR", "dT", "dN"
        ])

        return table

    # ---------------- TEST DATA ---------------- #

    def run_analysis(self):

        sp3_calc = self.calc_path.text()
        sp3_ref = self.ref_path.text()
        clk = self.clk_path.text()
        sat = self.satellite_box.currentText()

        data = self.controller.run_analysis(
            sp3_calc,
            sp3_ref,
            clk,
            sat
        )

        self.update_plots(data)
        self.update_statistics(
            data["dx"], data["dy"], data["dz"],
            data["dr"], data["dt"], data["dn"],
            data["clk"]
        )
        self.update_table(
            data["t"],
            data["dx"], data["dy"], data["dz"],
            data["dr"], data["dt"], data["dn"]
        )

        exp_id = self.db.create_experiment("Test run")


    def update_statistics(self, dx, dy, dz, dr, dt, dn, clk):

        def rms(x):
            return np.sqrt(np.mean(x**2))

        stats = {
            "RMS X": rms(dx),
            "RMS Y": rms(dy),
            "RMS Z": rms(dz),
            "RMS 3D": rms(np.sqrt(dx**2 + dy**2 + dz**2)),
            "RMS R": rms(dr),
            "RMS T": rms(dt),
            "RMS N": rms(dn),
            "Mean": np.mean(dx),
            "Max": np.max(np.abs(dx)),
            "Clock RMS": rms(clk)
        }

        for key, value in stats.items():
            self.stats_labels[key].setText(f"{value:.4f}")


    def update_table(self, t, dx, dy, dz, dr, dt, dn):

        self.table.setRowCount(len(t))

        for i in range(len(t)):
            self.table.setItem(i, 0, QTableWidgetItem(f"{t[i]:.2f}"))
            self.table.setItem(i, 1, QTableWidgetItem("R12"))
            self.table.setItem(i, 2, QTableWidgetItem(f"{dx[i]:.4f}"))
            self.table.setItem(i, 3, QTableWidgetItem(f"{dy[i]:.4f}"))
            self.table.setItem(i, 4, QTableWidgetItem(f"{dz[i]:.4f}"))
            self.table.setItem(i, 5, QTableWidgetItem(f"{dr[i]:.4f}"))
            self.table.setItem(i, 6, QTableWidgetItem(f"{dt[i]:.4f}"))
            self.table.setItem(i, 7, QTableWidgetItem(f"{dn[i]:.4f}"))


    def update_plots(self, data):

        self.orbit_plot.clear()
        self.rtn_plot.clear()
        self.clock_plot.clear()

        t = data["t"]

        self.orbit_plot.plot(t, data["dx"], pen='b')
        self.orbit_plot.plot(t, data["dy"], pen='r')
        self.orbit_plot.plot(t, data["dz"], pen='g')

        self.rtn_plot.plot(t, data["dr"], pen='y')
        self.rtn_plot.plot(t, data["dt"], pen='c')
        self.rtn_plot.plot(t, data["dn"], pen='m')

        self.clock_plot.plot(t, data["clk"], pen='w')


    def open_history(self):

        self.history_window = HistoryWindow(self.controller.db)
        self.history_window.experiment_selected.connect(self.load_experiment)
        self.history_window.show()


    def load_experiment(self, experiment_id):

        data = self.controller.load_experiment(experiment_id)

        self.update_plots(data)
        self.update_statistics(
            data["dx"], data["dy"], data["dz"],
            data["dr"], data["dt"], data["dn"],
            data["clk"]
        )
        self.update_table(
            data["t"],
            data["dx"], data["dy"], data["dz"],
            data["dr"], data["dt"], data["dn"]
        )

    def load_test_data(self):

        self.orbit_plot.clear()
        self.rtn_plot.clear()
        self.clock_plot.clear()

        t = np.linspace(0, 24, 200)

        dx = 0.1 * np.sin(t)
        dy = 0.1 * np.cos(t)
        dz = 0.05 * np.sin(2 * t)

        dr = 0.05 * np.sin(t)
        dt = 0.08 * np.cos(t)
        dn = 0.03 * np.sin(2 * t)

        clk = np.random.normal(0, 5, len(t))

        self.update_plots({
            "t": t, "dx": dx, "dy": dy, "dz": dz,
            "dr": dr, "dt": dt, "dn": dn, "clk": clk
        })

        self.orbit_plot.plot(t, dx, pen='b', name="dX")
        self.orbit_plot.plot(t, dy, pen='r', name="dY")
        self.orbit_plot.plot(t, dz, pen='g', name="dZ")

        self.orbit_plot.setTitle("Orbit Errors (XYZ)", color="#cccccc", size="11pt")

        self.rtn_plot.plot(t, dr, pen='y', name="R")
        self.rtn_plot.plot(t, dt, pen='c', name="T")
        self.rtn_plot.plot(t, dn, pen='m', name="N")

        legend = self.orbit_plot.addLegend()
        legend.setOffset((10, 10))

        self.update_statistics(dx, dy, dz, dr, dt, dn, clk)
        self.update_table(t, dx, dy, dz, dr, dt, dn)