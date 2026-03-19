from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QFileDialog,
    QComboBox, QTableWidget, QTableWidgetItem,
    QTabWidget, QToolBar, QSplitter
)
from PySide6.QtCore import Qt
import pyqtgraph as pg
from controllers.analysis_controller import AnalysisController


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("GNSS SP3 Analyzer")
        self.setMinimumSize(1100, 750)
        self.resize(1200, 800)

        self.controller = AnalysisController()

        self.init_ui()

    # ---------------- UI ---------------- #

    def init_ui(self):

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
        main_layout.addWidget(self.table)

        central_widget.setLayout(main_layout)

    # ---------------- Toolbar ---------------- #

    def create_toolbar(self):

        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)

        btn_load = QPushButton("Load")
        btn_run = QPushButton("Run")
        btn_run.clicked.connect(self.run_analysis)
        btn_export = QPushButton("Export")

        toolbar.addWidget(btn_load)
        toolbar.addWidget(btn_run)
        toolbar.addWidget(btn_export)

    # ---------------- File Panel ---------------- #

    def create_file_panel(self):

        layout = QVBoxLayout()

        layout.addLayout(self.create_file_row("Calculated SP3:", "calc"))
        layout.addLayout(self.create_file_row("Reference SP3:", "ref"))
        layout.addLayout(self.create_file_row("CLK file:", "clk"))

        # Satellite selector
        sat_layout = QHBoxLayout()
        sat_layout.setSpacing(8)

        label = QLabel("Satellite:")
        label.setMinimumWidth(130)

        self.satellite_box = QComboBox()
        self.satellite_box.setFixedWidth(200)

        sat_layout.addWidget(label)
        sat_layout.addWidget(self.satellite_box)
        sat_layout.addStretch()

        layout.addLayout(sat_layout)

        container = QWidget()
        container.setLayout(layout)
        container.setMinimumHeight(140)

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
        line_edit.setMinimumHeight(34)

        button = QPushButton("Browse")
        button.setMinimumHeight(34)
        button.setFixedWidth(90)

        button.clicked.connect(lambda: self.select_file(line_edit))

        setattr(self, f"{file_type}_path", line_edit)

        layout.addWidget(label)
        layout.addWidget(line_edit)
        layout.addWidget(button)

        return layout

    def select_file(self, line_edit):

        path, _ = QFileDialog.getOpenFileName(self, "Select file")

        if path:
            line_edit.setText(path)

    # ---------------- Plot Area ---------------- #

    def create_plot_tabs(self):

        tabs = QTabWidget()

        self.orbit_plot = pg.PlotWidget(title="Orbit Errors (XYZ)")
        self.rtn_plot = pg.PlotWidget(title="RTN Errors")
        self.clock_plot = pg.PlotWidget(title="Clock Bias")

        self.orbit_plot.setContentsMargins(5, 5, 5, 5)
        self.rtn_plot.setContentsMargins(5, 5, 5, 5)
        self.clock_plot.setContentsMargins(5, 5, 5, 5)

        tabs.addTab(self.orbit_plot, "Orbit")
        tabs.addTab(self.rtn_plot, "RTN")
        tabs.addTab(self.clock_plot, "Clock")

        return tabs

    # ---------------- Statistics ---------------- #

    def create_statistics_panel(self):

        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)

        self.stats_labels = {}

        stats = [
            "RMS X", "RMS Y", "RMS Z", "RMS 3D",
            "RMS R", "RMS T", "RMS N",
            "Mean", "Max", "Clock RMS"
        ]

        for stat in stats:
            label = QLabel(f"{stat}: ---")
            label.setMinimumHeight(20)
            self.stats_labels[stat] = label
            layout.addWidget(label)

        layout.addStretch()  # ← ВАЖНО

        widget.setLayout(layout)
        widget.setMinimumWidth(200)

        return widget

    # ---------------- Table ---------------- #

    def create_table(self):

        table = QTableWidget()
        table.setColumnCount(8)

        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setDefaultSectionSize(100)
        table.setAlternatingRowColors(True)

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


    def update_statistics(self, dx, dy, dz, dr, dt, dn, clk):

        import numpy as np

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
            self.stats_labels[key].setText(f"{key}: {value:.4f}")

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