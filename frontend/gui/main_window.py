from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, QSize
import pyqtgraph as pg
import numpy as np
import requests


class MainWindow(QMainWindow):

    def __init__(self, controller):
        super().__init__()
        self.controller = controller

        self.setWindowTitle("GNSS SP3 Analyzer")
        self.resize(1100, 750)

        self.backend_status = "UNKNOWN"
        self.check_backend()

        self.init_ui()

    # ================= UI ================= #

    def init_ui(self):

        pg.setConfigOption('background', '#1e1e1e')
        pg.setConfigOption('foreground', '#cccccc')

        self.statusBar().showMessage(f"Backend: {self.backend_status}")

        self.create_toolbar()

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)

        main_layout.addWidget(self.create_file_panel())

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.create_plots())
        splitter.addWidget(self.create_stats())

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter)
        main_layout.addWidget(self.create_table())

    # ================= TOOLBAR ================= #

    def create_toolbar(self):

        toolbar = QToolBar()
        toolbar.setIconSize(QSize(18, 18))
        self.addToolBar(toolbar)

        btn_load = QPushButton("📂 Load")
        btn_load.clicked.connect(self.load_files)

        btn_run = QPushButton("▶ Run")
        btn_run.clicked.connect(self.on_run_clicked)

        btn_export = QPushButton("💾 Export")
        btn_export.clicked.connect(self.export_results)

        btn_history = QPushButton("🕓 History")
        btn_history.clicked.connect(self.open_history)

        toolbar.addWidget(btn_load)
        toolbar.addWidget(btn_run)
        toolbar.addWidget(btn_export)
        toolbar.addWidget(btn_history)

    # ================= FILE PANEL ================= #

    def create_file_panel(self):

        layout = QVBoxLayout()

        layout.addLayout(self.file_row("Calculated SP3:", "calc"))
        layout.addLayout(self.file_row("Reference SP3:", "ref"))
        layout.addLayout(self.file_row("CLK file:", "clk"))

        sat_layout = QHBoxLayout()
        sat_layout.addWidget(QLabel("Satellite:"))

        self.satellite_box = QComboBox()
        self.satellite_box.setMinimumWidth(150)

        sat_layout.addWidget(self.satellite_box)
        sat_layout.addStretch()

        layout.addLayout(sat_layout)

        w = QWidget()
        w.setLayout(layout)
        return w

    def file_row(self, label, attr):

        layout = QHBoxLayout()

        le = QLineEdit()
        btn = QPushButton("Browse")

        btn.clicked.connect(lambda: self.select_file(le))

        setattr(self, f"{attr}_path", le)

        layout.addWidget(QLabel(label))
        layout.addWidget(le)
        layout.addWidget(btn)

        return layout

    def select_file(self, line_edit):
        path, _ = QFileDialog.getOpenFileName(self)
        if path:
            line_edit.setText(path)

    # ================= PLOTS ================= #

    def create_plots(self):

        tabs = QTabWidget()

        self.orbit_plot = pg.PlotWidget(title="Orbit XYZ")
        self.rtn_plot = pg.PlotWidget(title="RTN")
        self.clock_plot = pg.PlotWidget(title="Clock")

        # Легенды (ОДИН раз!)
        self.orbit_plot.addLegend()
        self.rtn_plot.addLegend()

        for p in [self.orbit_plot, self.rtn_plot, self.clock_plot]:
            p.showGrid(x=True, y=True)

        tabs.addTab(self.orbit_plot, "Orbit")
        tabs.addTab(self.rtn_plot, "RTN")
        tabs.addTab(self.clock_plot, "Clock")

        return tabs

    # ================= STATS ================= #

    def create_stats(self):

        w = QWidget()
        layout = QGridLayout(w)

        names = [
            "RMS X", "RMS Y", "RMS Z", "RMS 3D",
            "RMS R", "RMS T", "RMS N",
            "Mean", "Max", "Clock RMS"
        ]

        self.stats = {}

        for i, n in enumerate(names):
            layout.addWidget(QLabel(n), i, 0)
            val = QLabel("---")
            layout.addWidget(val, i, 1)
            self.stats[n] = val

        return w

    # ================= TABLE ================= #

    def create_table(self):

        table = QTableWidget()
        table.setColumnCount(8)

        table.setHorizontalHeaderLabels([
            "t", "sat", "dx", "dy", "dz", "dR", "dT", "dN"
        ])

        return table

    # ================= LOGIC ================= #

    def check_backend(self):
        try:
            requests.get("http://localhost:8080/experiments", timeout=1)
            self.backend_status = "OK"
        except:
            self.backend_status = "FAIL"

    def on_run_clicked(self):

        self.check_backend()
        self.statusBar().showMessage(f"Backend: {self.backend_status}")

        if self.backend_status != "OK":
            QMessageBox.warning(self, "Error", "Backend not running")
            return

        self.run_analysis()

    def run_analysis(self):

        try:
            r = requests.post("http://localhost:8080/analyze")
            data = r.json()

            e = data["epochs"]

            t  = np.array([x["t"] for x in e])
            dx = np.array([x["dx"] for x in e])
            dy = np.array([x["dy"] for x in e])
            dz = np.array([x["dz"] for x in e])

            dr, dt, dn = dx, dy, dz
            clk = np.zeros_like(t)

            self.update_plots(t, dx, dy, dz, dr, dt, dn, clk)
            self.update_stats(dx, dy, dz, dr, dt, dn, clk)
            self.update_table(t, dx, dy, dz, dr, dt, dn)

        except Exception as e:
            print("Error:", e)

    # ================= UPDATE ================= #

    def update_plots(self, t, dx, dy, dz, dr, dt, dn, clk):

        self.orbit_plot.clear()
        self.rtn_plot.clear()
        self.clock_plot.clear()

        self.orbit_plot.addLegend()
        self.rtn_plot.addLegend()

        self.orbit_plot.plot(t, dx, pen='b', name="X")
        self.orbit_plot.plot(t, dy, pen='r', name="Y")
        self.orbit_plot.plot(t, dz, pen='g', name="Z")

        self.rtn_plot.plot(t, dr, pen='y', name="R")
        self.rtn_plot.plot(t, dt, pen='c', name="T")
        self.rtn_plot.plot(t, dn, pen='m', name="N")

        self.clock_plot.plot(t, clk, pen='w')

    def update_stats(self, dx, dy, dz, dr, dt, dn, clk):

        def rms(x): return np.sqrt(np.mean(x**2))

        vals = {
            "RMS X": rms(dx),
            "RMS Y": rms(dy),
            "RMS Z": rms(dz),
            "RMS 3D": rms(np.sqrt(dx**2+dy**2+dz**2)),
            "RMS R": rms(dr),
            "RMS T": rms(dt),
            "RMS N": rms(dn),
            "Mean": np.mean(dx),
            "Max": np.max(np.abs(dx)),
            "Clock RMS": rms(clk)
        }

        for k,v in vals.items():
            self.stats[k].setText(f"{v:.4f}")

    def update_table(self, t, dx, dy, dz, dr, dt, dn):

        self.table.setRowCount(len(t))

        for i in range(len(t)):
            self.table.setItem(i, 0, QTableWidgetItem(str(t[i])))
            self.table.setItem(i, 1, QTableWidgetItem("G01"))
            self.table.setItem(i, 2, QTableWidgetItem(f"{dx[i]:.4f}"))
            self.table.setItem(i, 3, QTableWidgetItem(f"{dy[i]:.4f}"))
            self.table.setItem(i, 4, QTableWidgetItem(f"{dz[i]:.4f}"))
            self.table.setItem(i, 5, QTableWidgetItem(f"{dr[i]:.4f}"))
            self.table.setItem(i, 6, QTableWidgetItem(f"{dt[i]:.4f}"))
            self.table.setItem(i, 7, QTableWidgetItem(f"{dn[i]:.4f}"))

    # ================= STUBS ================= #

    def load_files(self):
        print("Load")

    def export_results(self):
        print("Export")

    def open_history(self):
        print("History")