

from PySide6.QtWidgets import (
    QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel,
    QHBoxLayout, QGroupBox
)
from PySide6.QtCore import Qt, QPropertyAnimation, QSequentialAnimationGroup, QEasingCurve, QRect

from PySide6.QtGui import QIcon

from src.gui.inference.live_evolution_window import LiveEvolutionWindow
from src.gui.network_manipulation.import_network_window import ImportNetworkWindow
from src.gui.graph_window import GenerateGraphsWindow
from src.gui.network_manipulation.modify_network_window import ModifyRulesGUI
from src.gui.network_manipulation.rules_gui import RulesGUI
from src.gui.network_manipulation.truth_table_input_gui import TruthTableInputGUI
from src.gui.inference.experiments_window import ExperimentWindow


class MainMenu(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon("gui/assets/BN_Forge_Icon.png"))

        self.setWindowTitle("BN Forge- Boolean Network Evolution Studio")
        self.setGeometry(100, 100, 950, 650)
        self.setContentsMargins(10, 10, 10, 10)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)

        self.title_label = QLabel("BN Forge")
        self.title_label.setStyleSheet("font-size: 38px; font-weight: bold; margin-top: 10px;")
        self.layout.addWidget(self.title_label, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.subtitle_label = QLabel("Boolean Network Evolution & Visualisation Studio")
        self.subtitle_label.setStyleSheet("font-size: 15px; color: gray; font-style: italic; margin-bottom: 15px;")
        self.layout.addWidget(self.subtitle_label, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.how_to_button = self.make_button("📘 How To Use This Tool", 325, 45)
        self.layout.addWidget(self.how_to_button, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.main_area = QHBoxLayout()
        self.layout.addLayout(self.main_area)

        self.left_panel = QWidget()
        self.right_panel = QWidget()
        self.build_left_panel()
        self.build_right_panel()

        self.main_area.addWidget(self.left_panel)
        self.main_area.addWidget(self.right_panel)

        self.exit_button = self.make_button("🚪 Exit", 650, 45)
        self.exit_button.clicked.connect(self.close)
        self.layout.addWidget(self.exit_button, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.animate_panels()

    def make_button(self, text, width=320, height=80, tooltip=""):
        btn = QPushButton(text)
        btn.setFixedSize(width, height)
        btn.setStyleSheet(self.hover_style())
        btn.setToolTip(tooltip)
        btn.clicked.connect(lambda: self.bounce(btn))
        return btn

    def hover_style(self):
        return '''
            QPushButton {
                background-color: #f0f0f0;
                font-size: 16px;
                border: 2px solid #ccc;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #dce9ff;
                font-size: 16px;
                border: 2px solid #88b;
            }
        '''

    def bounce(self, button):
        anim = QPropertyAnimation(button, b"geometry")
        anim.setDuration(200)
        start = button.geometry()
        bounce_up = QRect(start.x(), start.y() - 5, start.width(), start.height())
        anim.setKeyValueAt(0.0, start)
        anim.setKeyValueAt(0.5, bounce_up)
        anim.setKeyValueAt(1.0, start)
        anim.setEasingCurve(QEasingCurve.OutBounce)
        anim.start()
        self.anim = anim  # Keep a reference

    def build_left_panel(self):
        left_layout = QVBoxLayout()
        left_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Import / Define
        import_box = QGroupBox("📥 Define or Import Network")
        import_layout = QVBoxLayout()
        import_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        btn_csv = self.make_button("Import from CSV", tooltip="Load a Boolean Network from a .csv file (truth table format - see How-To section).")
        btn_csv.clicked.connect(self.open_import_window)
        import_layout.addWidget(btn_csv)

        btn_define_rules = self.make_button("Define from Next-State Rules", tooltip="Build a Boolean Network by defining the Boolean next-state rules for each entity")
        btn_define_rules.clicked.connect(self.open_define_rules_window)
        import_layout.addWidget(btn_define_rules)

        btn_define_truth = self.make_button("Define from Truth Table Trace", 320, 80, tooltip="Enter observed truth table data to build a Boolean Network.")
        btn_define_truth.clicked.connect(self.open_truth_table_window)
        import_layout.addWidget(btn_define_truth)

        import_box.setLayout(import_layout)

        # Edit
        edit_box = QGroupBox("✏️ Edit Existing Network")
        edit_layout = QVBoxLayout()
        edit_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        modify_btn = self.make_button("Modify Existing Network", 320, 80, tooltip="Change the Boolean next-state rules of a saved Boolean Network.")
        modify_btn.clicked.connect(self.open_modify_window)
        edit_layout.addWidget(modify_btn)

        edit_box.setLayout(edit_layout)

        left_layout.addWidget(import_box)
        left_layout.addWidget(edit_box)
        self.left_panel.setLayout(left_layout)
        self.left_panel.setWindowOpacity(0)

    def build_right_panel(self):
        right_layout = QVBoxLayout()
        right_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        visualise_box = QGroupBox("👁️ Visualise Network")
        vis_layout = QVBoxLayout()
        vis_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        live_btn = self.make_button("Live Evolution Viewer", tooltip="Evolve a random Boolean Network towards a saved Boolean Network trace using Genetic Algorithm or Simulated Annealing metaheuristics.")
        live_btn.clicked.connect(self.open_live_window)
        vis_layout.addWidget(live_btn)

        view_btn = self.make_button("View Network Diagrams", tooltip="Visualise a saved Boolean Network's dynamics and structure through its state graph and entity wiring diagram.")
        view_btn.clicked.connect(self.open_graphs_window)
        vis_layout.addWidget(view_btn)

        exp_btn = self.make_button("Run Experiments",
                                   tooltip="Batch run a saved Boolean Network against a target using metaheuristic search. Logs and final statistics are saved.")
        exp_btn.clicked.connect(self.open_experiment_window)
        vis_layout.addWidget(exp_btn)

        visualise_box.setLayout(vis_layout)
        right_layout.addWidget(visualise_box)

        self.right_panel.setLayout(right_layout)
        self.right_panel.setWindowOpacity(0)

    def animate_panels(self):
        anim1 = QPropertyAnimation(self.left_panel, b"windowOpacity")
        anim1.setDuration(600)
        anim1.setStartValue(0)
        anim1.setEndValue(1)

        anim2 = QPropertyAnimation(self.right_panel, b"windowOpacity")
        anim2.setDuration(600)
        anim2.setStartValue(0)
        anim2.setEndValue(1)

        sequence = QSequentialAnimationGroup()
        sequence.addAnimation(anim1)
        sequence.addAnimation(anim2)
        sequence.start()

    # --------------------
    # Window Launchers
    # --------------------
    def open_import_window(self):
        self.import_window = ImportNetworkWindow()
        self.import_window.show()

    def open_define_rules_window(self):
        self.rules_window = RulesGUI()
        self.rules_window.show()


    def open_truth_table_window(self):
        self.truth_window = TruthTableInputGUI()
        self.truth_window.show()

    def open_modify_window(self):
        self.modify_window = ModifyRulesGUI()
        self.modify_window.show()

    def open_live_window(self):
        if not hasattr(self, 'live_window') or not self.live_window.isVisible():
            self.live_window = LiveEvolutionWindow()
            self.live_window.show()
        else:
            self.live_window.activateWindow()
            self.live_window.raise_()

    def open_graphs_window(self):
        self.graphs_window = GenerateGraphsWindow()
        self.graphs_window.show()

    def open_experiment_window(self):
        self.experiment_window = ExperimentWindow(self)
        self.experiment_window.show()

