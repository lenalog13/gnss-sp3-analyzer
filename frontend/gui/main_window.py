import sys
import os
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
import pyqtgraph as pg
import numpy as np
import requests

# Добавляем пути для импорта
sys.path.append(os.path.join(os.path.dirname(__file__), '../../database'))
sys.path.append(os.path.dirname(__file__))

from db_manager import DBManager
from frontend.gui.history_window import HistoryWindow


# ================= HOVER ================= #

class PlotHover:
    def __init__(self, plot_widget):
        self.plot = plot_widget
        self.curves = []

        # Создаем вертикальную линию
        self.vLine = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('#aaaaaa'))
        self.plot.addItem(self.vLine, ignoreBounds=True)
        self.vLine.hide()  # Сначала скрываем

        # Создаем текстовую метку (без setBorder и setFill)
        self.label = pg.TextItem("", anchor=(0, 1))
        self.label.setColor('#ffffff')
        # Добавляем фон через html
        self.label.setHtml('<div style="background-color: #222222; padding: 5px; border: 1px solid #333333;">&nbsp;</div>')
        self.plot.addItem(self.label)
        self.label.hide()  # Сначала скрываем

        # Подключаем сигнал движения мыши
        self.proxy = pg.SignalProxy(
            self.plot.scene().sigMouseMoved,
            rateLimit=60,
            slot=self.mouse_moved
        )

    def add_curve(self, curve, name):
        """Add a curve to track for hover"""
        self.curves.append((curve, name))

    def mouse_moved(self, evt):
        """Handle mouse movement"""
        pos = evt[0]
        vb = self.plot.getViewBox()
        
        # Проверяем, что мышь внутри графика
        if not self.plot.sceneBoundingRect().contains(pos):
            self.vLine.hide()
            self.label.hide()
            return
        
        self.vLine.show()
        self.label.show()
        
        # Получаем координаты мыши в системе координат графика
        mouse_point = vb.mapSceneToView(pos)
        x = mouse_point.x()
        
        # Перемещаем вертикальную линию
        self.vLine.setPos(x)
        
        # Формируем текст для отображения
        text = f'<div style="background-color: #222222; padding: 5px; border: 1px solid #555555; border-radius: 3px;">'
        text += f'<b>Time: {x:.2f}</b><br>'
        
        for curve, name in self.curves:
            try:
                x_data, y_data = curve.getData()
                
                if x_data is None or len(x_data) == 0:
                    continue
                
                # Находим ближайшую точку
                x_data = np.array(x_data)
                y_data = np.array(y_data)
                
                idx = (np.abs(x_data - x)).argmin()
                y = y_data[idx]
                
                # Цвет для разных кривых
                color_map = {
                    "X": "#3399ff",
                    "Y": "#ff3333", 
                    "Z": "#33ff33",
                    "R": "#ffff33",
                    "T": "#33ffff",
                    "N": "#ff33ff",
                    "Clock": "#ffffff"
                }
                color = color_map.get(name, "#ffffff")
                text += f'<span style="color: {color};">{name}</span>: {y:.6f}<br>'
            except Exception as e:
                print(f"Error getting curve data: {e}")
                continue
        
        text += '</div>'
        
        # Обновляем текст метки
        self.label.setHtml(text)
        
        # Позиционируем метку (немного смещаем, чтобы не перекрывать линию)
        self.label.setPos(x + 10, mouse_point.y())


# ================= MAIN WINDOW ================= #

class MainWindow(QMainWindow):

    def __init__(self, controller=None):
        super().__init__()

        self.controller = controller
        # Убираем self.db = DBManager() - теперь используем контекстный менеджер
        self.current_experiment_id = None
        self.current_epochs_data = None
        self.current_satellite = None
        self.history_window = None

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
        self.table.setMinimumHeight(250)
        main_layout.addWidget(self.table)

        main_layout.setStretch(1, 5)
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
        
        # Используем QGridLayout для выравнивания
        grid_layout = QGridLayout()
        
        # Row 0: Calculated SP3
        grid_layout.addWidget(QLabel("Calculated SP3:"), 0, 0)
        self.calc_path = QLineEdit()
        btn_calc = QPushButton("Browse")
        btn_calc.clicked.connect(lambda: self.select_file(self.calc_path))
        grid_layout.addWidget(self.calc_path, 0, 1)
        grid_layout.addWidget(btn_calc, 0, 2)
        
        # Row 1: Reference SP3
        grid_layout.addWidget(QLabel("Reference SP3:"), 1, 0)
        self.ref_path = QLineEdit()
        btn_ref = QPushButton("Browse")
        btn_ref.clicked.connect(lambda: self.select_file(self.ref_path))
        grid_layout.addWidget(self.ref_path, 1, 1)
        grid_layout.addWidget(btn_ref, 1, 2)
        
        # Row 2: CLK file
        grid_layout.addWidget(QLabel("CLK file:"), 2, 0)
        self.clk_path = QLineEdit()
        btn_clk = QPushButton("Browse")
        btn_clk.clicked.connect(lambda: self.select_file(self.clk_path))
        grid_layout.addWidget(self.clk_path, 2, 1)
        grid_layout.addWidget(btn_clk, 2, 2)
        
        layout.addLayout(grid_layout)
        
        # Satellite selection panel
        sat_layout = QHBoxLayout()
        sat_layout.addWidget(QLabel("Satellite:"))
        
        self.satellite_box = QComboBox()
        self.satellite_box.currentTextChanged.connect(self.on_satellite_changed)
        sat_layout.addWidget(self.satellite_box)
        
        # Улучшенная кнопка обновления
        refresh_btn = QPushButton("↻")
        refresh_btn.setFixedSize(28, 28)
        refresh_btn.setToolTip("Refresh satellite list")
        
        # Стилизация кнопки с скругленными углами
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #3c3c3c;
                border: none;
                border-radius: 14px;
                font-size: 16px;
                font-weight: bold;
                color: #ffffff;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
            }
            QPushButton:pressed {
                background-color: #2a2a2a;
            }
        """)
        
        refresh_btn.clicked.connect(self.refresh_satellite_list)
        sat_layout.addWidget(refresh_btn)
        
        sat_layout.addStretch()
        
        layout.addLayout(sat_layout)
        
        w = QWidget()
        w.setLayout(layout)
        return w

    def select_file(self, line_edit):
        """Open file dialog and set selected file path"""
        path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select File",
            "",
            "SP3 files (*.sp3);;CLK files (*.clk);;All files (*.*)"
        )
        if path:
            line_edit.setText(path)

    # ================= PLOTS ================= #

    def create_plots(self):

        tabs = QTabWidget()

        self.orbit_plot = pg.PlotWidget(title="Orbit XYZ")
        self.rtn_plot = pg.PlotWidget(title="RTN")
        self.clock_plot = pg.PlotWidget(title="Clock")

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

        self.stats_labels = {}

        for i, stat in enumerate(stats):
            label_name = QLabel(stat)
            label_value = QLabel("---")

            layout.addWidget(label_name, i, 0)
            layout.addWidget(label_value, i, 1)

            self.stats_labels[stat] = label_value

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

    # ================= BACKEND ================= #

    def check_backend(self):
        try:
            response = requests.get("http://localhost:8080/experiments", timeout=2)
            if response.status_code == 200:
                self.backend_status = "OK"
            else:
                self.backend_status = "FAIL"
        except:
            self.backend_status = "FAIL"

    def on_run_clicked(self):

        self.check_backend()
        self.statusBar().showMessage(f"Backend: {self.backend_status}")

        if self.backend_status != "OK":
            QMessageBox.warning(self, "Error", "Backend not running at http://localhost:8080")
            return

        self.run_analysis()

    def run_analysis(self):

        calc_path = self.calc_path.text()
        ref_path = self.ref_path.text()
        clk_path = self.clk_path.text()

        if not calc_path or not ref_path:
            QMessageBox.warning(self, "Error", "Select SP3 files first")
            return

        try:
            # Prepare files for upload
            files = {
                "calc": (os.path.basename(calc_path), open(calc_path, "rb")),
                "ref": (os.path.basename(ref_path), open(ref_path, "rb"))
            }
            
            if clk_path and os.path.exists(clk_path):
                files["clk"] = (os.path.basename(clk_path), open(clk_path, "rb"))

            # Send request to backend
            response = requests.post(
                "http://localhost:8080/analyze",
                files=files
            )
            
            # Close all file handles
            for f in files.values():
                f[1].close()

            if response.status_code != 200:
                QMessageBox.critical(self, "Error", f"Backend error: {response.status_code}")
                return

            data = response.json()
            epochs = data.get("epochs", [])

            if not epochs:
                QMessageBox.warning(self, "Warning", "No data from backend")
                return

            # Process and validate epochs
            for i, epoch in enumerate(epochs):
                # Ensure satellite field exists
                if "sat" not in epoch or not epoch["sat"]:
                    epoch["sat"] = f"G{(i % 32) + 1:02d}"
                
                # Convert time to float if it's string
                if isinstance(epoch.get("t"), str):
                    try:
                        epoch["t"] = float(epoch["t"])
                    except:
                        epoch["t"] = float(i)
                
                # Ensure numeric values
                for key in ["dx", "dy", "dz", "dr", "dt", "dn", "clk"]:
                    if key in epoch and epoch[key] is not None:
                        try:
                            epoch[key] = float(epoch[key])
                        except:
                            epoch[key] = None

            # Save to database using context manager
            experiment_name = f"Analysis_{os.path.basename(calc_path)}_{os.path.basename(ref_path)}"
            experiment_data = {"name": experiment_name}
            
            with DBManager() as db:
                experiment_id = db.save_experiment(experiment_data)
                self.current_experiment_id = experiment_id
                db.save_epochs(experiment_id, epochs)
            
            # Get unique satellites and update dropdown
            self.refresh_satellite_list()
            
            # If there are satellites, load the first one
            if self.satellite_box.count() > 0 and self.satellite_box.currentText() != "No satellites found":
                first_satellite = self.satellite_box.currentText()
                self.load_and_plot_data(experiment_id, first_satellite)
                
            QMessageBox.information(self, "Success", f"Experiment saved with ID: {experiment_id}")

        except requests.exceptions.ConnectionError:
            QMessageBox.critical(self, "Error", "Cannot connect to backend. Make sure server is running on port 8080")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Analysis failed: {str(e)}")

    def refresh_satellite_list(self):
        """Refresh the satellite dropdown list"""
        if self.current_experiment_id:
            try:
                with DBManager() as db:
                    satellites = db.get_satellites(self.current_experiment_id)
                
                self.satellite_box.clear()
                if satellites:
                    self.satellite_box.addItems(satellites)
                else:
                    self.satellite_box.addItem("No satellites found")
            except Exception as e:
                print(f"Error refreshing satellites: {e}")
                self.satellite_box.clear()
                self.satellite_box.addItem("Error loading satellites")

    def on_satellite_changed(self, satellite):
        """Handle satellite selection change"""
        if satellite and self.current_experiment_id and satellite not in ["No satellites found", "Error loading satellites"]:
            self.current_satellite = satellite
            self.load_and_plot_data(self.current_experiment_id, satellite)

    def load_and_plot_data(self, experiment_id, satellite):
        """Load data for specific satellite and update plots"""
        try:
            # Get filtered data for selected satellite using context manager
            with DBManager() as db:
                data = db.get_epochs(experiment_id, satellite=satellite)
            
            if not data or len(data["t"]) == 0:
                QMessageBox.warning(self, "Warning", f"No data found for satellite {satellite}")
                return
            
            # Diagnostic output
            print(f"\n=== Data Diagnostic for {satellite} ===")
            print(f"Number of epochs: {len(data['t'])}")
            print(f"Time range: {min(data['t'])} to {max(data['t'])}")
            if len(data['t']) > 1:
                print(f"Time step (avg): {(max(data['t']) - min(data['t'])) / (len(data['t']) - 1)}")
            print(f"First epoch: t={data['t'][0]}, dx={data['dx'][0]}, dy={data['dy'][0]}, dz={data['dz'][0]}")
            
            self.current_epochs_data = data
            
            # Update plots with filtered data
            self.update_plots(
                data["t"], 
                data["dx"], 
                data["dy"], 
                data["dz"],
                data["dr"], 
                data["dt"], 
                data["dn"], 
                data["clk"]
            )
            
            # Update table
            self.update_table(
                data["t"], 
                data["dx"], 
                data["dy"], 
                data["dz"],
                data["dr"], 
                data["dt"], 
                data["dn"], 
                satellite
            )
            
            # Update statistics
            self.update_statistics(
                data["dx"], 
                data["dy"], 
                data["dz"],
                data["dr"], 
                data["dt"], 
                data["dn"], 
                data["clk"]
            )
            
            self.statusBar().showMessage(f"Loaded satellite {satellite} with {len(data['t'])} epochs")
            
            # Тестируем hover
            print("Hover should be active now. Move mouse over the plots!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load data: {str(e)}")

    # ================= UPDATE ================= #

    def update_plots(self, t, dx, dy, dz, dr, dt, dn, clk):

        if len(t) == 0:
            return

        self.orbit_plot.clear()
        self.rtn_plot.clear()
        self.clock_plot.clear()
        
        # Конвертируем в numpy массивы
        t_array = np.array(t, dtype=float)
        
        # Если все времена одинаковые, используем индекс как время
        if len(t_array) > 1 and np.all(t_array == t_array[0]):
            print("WARNING: All time values are identical! Using indices as time.")
            t_array = np.arange(len(t), dtype=float)
        
        dx_array = np.array(dx, dtype=float)
        dy_array = np.array(dy, dtype=float)
        dz_array = np.array(dz, dtype=float)
        
        # Сортируем по времени
        sort_indices = np.argsort(t_array)
        t_sorted = t_array[sort_indices]
        dx_sorted = dx_array[sort_indices]
        dy_sorted = dy_array[sort_indices]
        dz_sorted = dz_array[sort_indices]
        
        # Orbit plot
        c1 = self.orbit_plot.plot(t_sorted, dx_sorted, pen=pg.mkPen(color='b', width=2), name="X")
        c2 = self.orbit_plot.plot(t_sorted, dy_sorted, pen=pg.mkPen(color='r', width=2), name="Y")
        c3 = self.orbit_plot.plot(t_sorted, dz_sorted, pen=pg.mkPen(color='g', width=2), name="Z")
        
        # Добавляем hover для орбит (только один объект на график)
        self.orbit_hover = PlotHover(self.orbit_plot)
        self.orbit_hover.add_curve(c1, "X")
        self.orbit_hover.add_curve(c2, "Y")
        self.orbit_hover.add_curve(c3, "Z")
        
        # Включаем автоматическое масштабирование
        self.orbit_plot.autoRange()
        
        # RTN plot
        valid_indices = [i for i in range(len(t_sorted)) 
                        if i < len(dr) and dr[i] is not None and dt[i] is not None and dn[i] is not None]
        
        if valid_indices:
            t_valid = [t_sorted[i] for i in valid_indices]
            dr_valid = [dr[i] for i in valid_indices]
            dt_valid = [dt[i] for i in valid_indices]
            dn_valid = [dn[i] for i in valid_indices]
            
            # Сортируем
            combined = sorted(zip(t_valid, dr_valid, dt_valid, dn_valid))
            if combined:
                t_rtn, dr_sorted, dt_sorted, dn_sorted = zip(*combined)
                t_rtn = np.array(t_rtn)
                dr_sorted = np.array(dr_sorted, dtype=float)
                dt_sorted = np.array(dt_sorted, dtype=float)
                dn_sorted = np.array(dn_sorted, dtype=float)
                
                c4 = self.rtn_plot.plot(t_rtn, dr_sorted, pen=pg.mkPen(color='y', width=2), name="R")
                c5 = self.rtn_plot.plot(t_rtn, dt_sorted, pen=pg.mkPen(color='c', width=2), name="T")
                c6 = self.rtn_plot.plot(t_rtn, dn_sorted, pen=pg.mkPen(color='m', width=2), name="N")
                
                # Добавляем hover для RTN
                self.rtn_hover = PlotHover(self.rtn_plot)
                self.rtn_hover.add_curve(c4, "R")
                self.rtn_hover.add_curve(c5, "T")
                self.rtn_hover.add_curve(c6, "N")
                
                self.rtn_plot.autoRange()
        
        # Clock plot
        valid_clk = [i for i in range(len(t_sorted)) 
                    if i < len(clk) and clk[i] is not None]
        
        if valid_clk:
            t_clk_valid = [t_sorted[i] for i in valid_clk]
            clk_valid = [clk[i] for i in valid_clk]
            
            # Сортируем
            combined_clk = sorted(zip(t_clk_valid, clk_valid))
            if combined_clk:
                t_clk_sorted, clk_sorted = zip(*combined_clk)
                t_clk_sorted = np.array(t_clk_sorted)
                clk_sorted = np.array(clk_sorted, dtype=float)
                
                c7 = self.clock_plot.plot(t_clk_sorted, clk_sorted, pen=pg.mkPen(color='w', width=2), name="Clock")
                
                # Добавляем hover для часов
                self.clock_hover = PlotHover(self.clock_plot)
                self.clock_hover.add_curve(c7, "Clock")
                
                self.clock_plot.autoRange()

    def update_statistics(self, dx, dy, dz, dr, dt, dn, clk):

        def rms(x):
            x_filtered = [val for val in x if val is not None and val != 0]
            if len(x_filtered) == 0:
                return 0
            x_array = np.array(x_filtered)
            return np.sqrt(np.mean(x_array**2))

        # Filter out None values for 3D calculation
        valid_3d = []
        for i in range(len(dx)):
            if dx[i] is not None and dy[i] is not None and dz[i] is not None:
                if dx[i] != 0 or dy[i] != 0 or dz[i] != 0:
                    valid_3d.append(np.sqrt(dx[i]**2 + dy[i]**2 + dz[i]**2))
        
        rms_3d = np.sqrt(np.mean(np.array(valid_3d)**2)) if valid_3d else 0

        stats = {
            "RMS X": rms(dx),
            "RMS Y": rms(dy),
            "RMS Z": rms(dz),
            "RMS 3D": rms_3d,
            "RMS R": rms(dr),
            "RMS T": rms(dt),
            "RMS N": rms(dn),
            "Mean": np.mean([x for x in dx if x is not None]) if dx else 0,
            "Max": np.max(np.abs([x for x in dx if x is not None])) if dx else 0,
            "Clock RMS": rms(clk)
        }

        for key, value in stats.items():
            if key in self.stats_labels:
                self.stats_labels[key].setText(f"{value:.6f}")

    def update_table(self, t, dx, dy, dz, dr, dt, dn, satellite="G01"):

        self.table.setRowCount(len(t))

        for i in range(len(t)):
            self.table.setItem(i, 0, QTableWidgetItem(f"{t[i]:.3f}" if t[i] else "---"))
            self.table.setItem(i, 1, QTableWidgetItem(satellite))
            self.table.setItem(i, 2, QTableWidgetItem(f"{dx[i]:.6f}" if dx[i] is not None else "---"))
            self.table.setItem(i, 3, QTableWidgetItem(f"{dy[i]:.6f}" if dy[i] is not None else "---"))
            self.table.setItem(i, 4, QTableWidgetItem(f"{dz[i]:.6f}" if dz[i] is not None else "---"))
            self.table.setItem(i, 5, QTableWidgetItem(f"{dr[i]:.6f}" if dr[i] is not None else "---"))
            self.table.setItem(i, 6, QTableWidgetItem(f"{dt[i]:.6f}" if dt[i] is not None else "---"))
            self.table.setItem(i, 7, QTableWidgetItem(f"{dn[i]:.6f}" if dn[i] is not None else "---"))

    # ================= LOAD & HISTORY ================= #

    def load_files(self):
        """Load existing experiment from database"""
        if not self.history_window:
            # Убираем передачу self.db, HistoryWindow сам создаёт соединение
            self.history_window = HistoryWindow()
            self.history_window.experiment_selected.connect(self.on_experiment_selected)
        
        self.history_window.show()
        self.history_window.raise_()
        self.history_window.activateWindow()

    def on_experiment_selected(self, experiment_id):
        """Handle experiment selection from history window"""
        self.current_experiment_id = experiment_id
        self.refresh_satellite_list()
        
        if self.satellite_box.count() > 0:
            first_satellite = self.satellite_box.currentText()
            if first_satellite and first_satellite not in ["No satellites found", "Error loading satellites"]:
                self.load_and_plot_data(experiment_id, first_satellite)
                self.statusBar().showMessage(f"Loaded experiment ID: {experiment_id}")

    def export_results(self):
        """Export current results to CSV"""
        if not self.current_epochs_data:
            QMessageBox.warning(self, "Warning", "No data to export")
            return
        
        path, _ = QFileDialog.getSaveFileName(self, "Export CSV", "", "CSV Files (*.csv)")
        if path:
            import csv
            data = self.current_epochs_data
            with open(path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['t', 'dx', 'dy', 'dz', 'dr', 'dt', 'dn', 'clk'])
                for i in range(len(data['t'])):
                    writer.writerow([
                        data['t'][i], data['dx'][i], data['dy'][i], 
                        data['dz'][i], data['dr'][i], data['dt'][i], 
                        data['dn'][i], data['clk'][i]
                    ])
            QMessageBox.information(self, "Success", f"Exported to {path}")

    def open_history(self):
        """Open history window"""
        self.load_files()