from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QFileDialog,
    QComboBox
)


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("GNSS SP3 Ephemeris Accuracy Analyzer")
        self.setMinimumSize(1200, 800)

        self.init_ui()

    def init_ui(self):

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()

        # File selection
        file_layout = QHBoxLayout()

        self.sp3_calc_path = QLineEdit()
        self.sp3_calc_path.setPlaceholderText("Path to calculated SP3")

        btn_sp3 = QPushButton("Browse")
        btn_sp3.clicked.connect(self.select_sp3)

        file_layout.addWidget(QLabel("Calculated SP3:"))
        file_layout.addWidget(self.sp3_calc_path)
        file_layout.addWidget(btn_sp3)

        main_layout.addLayout(file_layout)

        # Reference SP3
        ref_layout = QHBoxLayout()

        self.sp3_ref_path = QLineEdit()
        self.sp3_ref_path.setPlaceholderText("Path to reference SP3")

        btn_ref = QPushButton("Browse")
        btn_ref.clicked.connect(self.select_ref)

        ref_layout.addWidget(QLabel("Reference SP3:"))
        ref_layout.addWidget(self.sp3_ref_path)
        ref_layout.addWidget(btn_ref)

        main_layout.addLayout(ref_layout)

        # CLK
        clk_layout = QHBoxLayout()

        self.clk_path = QLineEdit()
        self.clk_path.setPlaceholderText("Path to CLK file")

        btn_clk = QPushButton("Browse")
        btn_clk.clicked.connect(self.select_clk)

        clk_layout.addWidget(QLabel("CLK file:"))
        clk_layout.addWidget(self.clk_path)
        clk_layout.addWidget(btn_clk)

        main_layout.addLayout(clk_layout)

        # Satellite selector

        sat_layout = QHBoxLayout()

        self.satellite_box = QComboBox()

        self.satellite_box.addItems([
            "ALL",
            "R01","R02","R03","R04","R05",
            "R06","R07","R08","R09","R10"
        ])

        sat_layout.addWidget(QLabel("Satellite:"))
        sat_layout.addWidget(self.satellite_box)

        main_layout.addLayout(sat_layout)

        # Run analysis button

        self.run_button = QPushButton("Run Analysis")
        main_layout.addWidget(self.run_button)

        central_widget.setLayout(main_layout)

    def select_sp3(self):

        path, _ = QFileDialog.getOpenFileName(self, "Select SP3 file")

        if path:
            self.sp3_calc_path.setText(path)

    def select_ref(self):

        path, _ = QFileDialog.getOpenFileName(self, "Select reference SP3")

        if path:
            self.sp3_ref_path.setText(path)

    def select_clk(self):

        path, _ = QFileDialog.getOpenFileName(self, "Select CLK file")

        if path:
            self.clk_path.setText(path)