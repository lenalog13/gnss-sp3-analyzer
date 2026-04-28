from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, QSize
import pyqtgraph as pg
import numpy as np
import requests

class PlotHover:
    def __init__(self, plot_widget):
        self.plot = plot_widget
        self.vLine = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('#aaaaaa'))
        self.plot.addItem(self.vLine, ignoreBounds=True)

        self.label = pg.TextItem("", anchor=(0,1))
        self.plot.addItem(self.label)

        self.curves = []

        self.proxy = pg.SignalProxy(
            self.plot.scene().sigMouseMoved,
            rateLimit=60,
            slot=self.mouse_moved
        )

    def add_curve(self, curve, name):
        self.curves.append((curve, name))

    def mouse_moved(self, evt):
        pos = evt[0]
        vb = self.plot.getViewBox()

        if not self.plot.sceneBoundingRect().contains(pos):
            return

        mouse_point = vb.mapSceneToView(pos)
        x = mouse_point.x()

        self.vLine.setPos(x)

        text = f"x = {x:.2f}\n"

        for curve, name in self.curves:
            data = curve.getData()
            if data[0] is None:
                continue

            x_data, y_data = data

            if len(x_data) == 0:
                continue

            idx = (np.abs(x_data - x)).argmin()
            y = y_data[idx]

            text += f"{name}: {y:.4f}\n"

        self.label.setText(text)
        self.label.setPos(x, mouse_point.y())

class MainWindow(QMainWindow):

    def __init__(self, controller=None):
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
        splitter.addWidget(self.create_statistics_panel())

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        main_layout.addWidget(splitter)

        self.table = self.create_table()
        self.table.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )
        self.table.verticalHeader().setDefaultSectionSize(22)
        main_layout.addWidget(self.table)

        main_layout.setStretch(1, 5)  # графики
        main_layout.setStretch(2, 2)  # таблица
        main_layout.setStretch(1, 4)
        main_layout.setStretch(2, 3)

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

    def create_statistics_panel(self):

        widget = QWidget()
        layout = QGridLayout()

        stats = [
            "RMS X", "RMS Y", "RMS Z", "RMS 3D",
            "RMS R", "RMS T", "RMS N",
            "Mean", "Max", "Clock RMS"
        ]

        self.stats_labels = {}   # ← ВОТ ЭТО КЛЮЧЕВОЕ

        for i, stat in enumerate(stats):

            label_name = QLabel(stat)
            label_value = QLabel("---")

            layout.addWidget(label_name, i, 0)
            layout.addWidget(label_value, i, 1)

            self.stats_labels[stat] = label_value  # ← и это

        widget.setLayout(layout)
        return widget

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

        calc_path = self.calc_path.text()
        ref_path  = self.ref_path.text()

        if not calc_path or not ref_path:
            print("Select SP3 files first")
            return

        try:
            with open(calc_path, "rb") as f1, open(ref_path, "rb") as f2:

                files = {
                    "calc": f1,
                    "ref": f2
                }

                response = requests.post(
                    "http://localhost:8080/analyze",
                    files=files
                )

            if response.status_code != 200:
                print("API error:", response.status_code)
                return

            data = response.json()
            epochs = data.get("epochs", [])

            t  = [e["t"] for e in epochs]
            dx = [e["dx"] for e in epochs]
            dy = [e["dy"] for e in epochs]
            dz = [e["dz"] for e in epochs]
            dr = [e.get("dr", 0) for e in epochs]
            dt = [e.get("dt", 0) for e in epochs]
            dn = [e.get("dn", 0) for e in epochs]
            clk = [e.get("clk", 0) for e in epochs]

            self.update_plots(t, dx, dy, dz, dr, dt, dn, clk)
            self.update_table(t, dx, dy, dz, dr, dt, dn)
            self.update_statistics(dx, dy, dz, dr, dt, dn, clk)

        except Exception as e:
            print("Connection error:", e)

    # ================= UPDATE ================= #

    def update_plots(self, t, dx, dy, dz, dr, dt, dn, clk):

        self.orbit_plot.clear()
        self.rtn_plot.clear()
        self.clock_plot.clear()

        # ===== Orbit =====
        self.orbit_plot.addLegend()

        c1 = self.orbit_plot.plot(t, dx, pen='b', name="X")
        c2 = self.orbit_plot.plot(t, dy, pen='r', name="Y")
        c3 = self.orbit_plot.plot(t, dz, pen='g', name="Z")

        self.orbit_hover = PlotHover(self.orbit_plot)
        self.orbit_hover.add_curve(c1, "X")
        self.orbit_hover.add_curve(c2, "Y")
        self.orbit_hover.add_curve(c3, "Z")

        # ===== RTN =====
        self.rtn_plot.addLegend()

        c4 = self.rtn_plot.plot(t, dr, pen='y', name="R")
        c5 = self.rtn_plot.plot(t, dt, pen='c', name="T")
        c6 = self.rtn_plot.plot(t, dn, pen='m', name="N")

        self.rtn_hover = PlotHover(self.rtn_plot)
        self.rtn_hover.add_curve(c4, "R")
        self.rtn_hover.add_curve(c5, "T")
        self.rtn_hover.add_curve(c6, "N")

        # ===== Clock =====
        c7 = self.clock_plot.plot(t, clk, pen='w')

        self.clock_hover = PlotHover(self.clock_plot)
        self.clock_hover.add_curve(c7, "CLK")

    def update_statistics(self, dx, dy, dz, dr, dt, dn, clk):
        import numpy as np

        def rms(x):
            x = np.array(x)
            return np.sqrt(np.mean(x**2)) if len(x) else 0

        stats = {
            "RMS X": rms(dx),
            "RMS Y": rms(dy),
            "RMS Z": rms(dz),
            "RMS 3D": rms(np.sqrt(np.array(dx)**2 + np.array(dy)**2 + np.array(dz)**2)),
            "RMS R": rms(dr),
            "RMS T": rms(dt),
            "RMS N": rms(dn),
            "Mean": np.mean(dx) if len(dx) else 0,
            "Max": np.max(np.abs(dx)) if len(dx) else 0,
            "Clock RMS": rms(clk)
        }

        for key, value in stats.items():
            if key in self.stats_labels:
                self.stats_labels[key].setText(f"{value:.4f}")


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

        if not hasattr(self, "table"):
            print("Table not initialized")
            return

    # ================= STUBS ================= #

    def load_files(self):
        print("Load")

    def export_results(self):
        print("Export")

    def open_history(self):
        print("History")


    def handle_response(self, data):

        epochs = data["epochs"]

        t  = np.array([e["t"] for e in epochs])
        dx = np.array([e["dx"] for e in epochs])
        dy = np.array([e["dy"] for e in epochs])
        dz = np.array([e["dz"] for e in epochs])

        # пока RTN заглушка
        dr, dt, dn = dx, dy, dz

        clk = np.zeros_like(t)

        self.update_plots(t, dx, dy, dz, dr, dt, dn, clk)
        self.update_table(t, dx, dy, dz, dr, dt, dn)
        self.update_statistics(dx, dy, dz, dr, dt, dn, clk)