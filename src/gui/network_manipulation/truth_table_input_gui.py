import itertools

from PySide6.QtWidgets import (
    QMainWindow, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QTableWidget,
    QTableWidgetItem, QSpinBox, QLineEdit, QMessageBox, QStyledItemDelegate, QSizePolicy, QFrame, QHeaderView
)
from PySide6.QtGui import QFont, QValidator
from PySide6.QtCore import Qt


from src.boolean_network_representation.rules import TruthTableToRules
from src.data_processing.truth_table_validation import validate_truth_table_inputs
from src.boolean_network_representation.storage import BooleanNetworkStorage


class BinaryCharValidator(QValidator):
    def validate(self, input_str, pos):
        if input_str in ("0", "1", ""):
            return QValidator.Acceptable, input_str, pos
        return QValidator.Invalid, input_str, pos

class BinaryOnlyDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.setMaxLength(1)
        editor.setValidator(BinaryCharValidator())
        return editor


class TruthTableInputGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Input Truth Table")
        self.setGeometry(150, 150, 1000, 700)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        main_layout = QVBoxLayout(self.central_widget)

        # Title
        title_label = QLabel("Input Truth Table")
        title_font = QFont("Segoe UI", 16, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)


        label_font = QFont("Segoe UI", 10, QFont.Weight.Bold)
        input_layout = QHBoxLayout()

        # Network Name
        name_label = QLabel("Network Name:")
        name_label.setFont(label_font)
        self.network_name_input = QLineEdit()
        self.network_name_input.setPlaceholderText("e.g., MyNetwork")
        self.network_name_input.setFixedWidth(250)

        # Entity Count
        entity_label = QLabel("Number of Entities:")
        entity_label.setFont(label_font)
        self.entity_count_selector = QSpinBox()
        self.entity_count_selector.setRange(2, 10)
        self.entity_count_selector.setValue(3)
        self.entity_count_selector.setFixedWidth(60)
        self.entity_count_selector.valueChanged.connect(self.generate_truth_table)

        # Add widgets to layout
        input_layout.addWidget(name_label)
        input_layout.addWidget(self.network_name_input)
        input_layout.addSpacing(40)
        input_layout.addWidget(entity_label)
        input_layout.addWidget(self.entity_count_selector)
        input_layout.addStretch()

        main_layout.addLayout(input_layout)

        # Spacer line
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line)

        # Truth Table Widget
        self.truth_table = QTableWidget()
        self.truth_table.setSizeAdjustPolicy(QTableWidget.AdjustToContents)
        main_layout.addWidget(self.truth_table)

        # Save Button
        self.save_button = QPushButton("💾 Save Network")
        self.save_button.setFixedHeight(40)
        self.save_button.setFixedWidth(900)
        self.save_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.save_button.clicked.connect(self.save_and_process_truth_table)

        # Center Save Button
        button_container = QWidget()
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addStretch()
        button_container.setLayout(button_layout)
        main_layout.addWidget(button_container)

        self.generate_truth_table()

    def generate_truth_table(self):
        entity_count = self.entity_count_selector.value()
        entities = [chr(65 + i) for i in range(entity_count)]
        states = list(itertools.product([0, 1], repeat=entity_count))

        self.truth_table.setRowCount(len(states))
        self.truth_table.setColumnCount(2 * entity_count + 1)

        headers = entities + [" "] + [f"{e}'" for e in entities]
        self.truth_table.setHorizontalHeaderLabels(headers)

        # Dynamic scaling
        scale = max(0.85, min(1.2, 6 / entity_count))
        font = QFont("Segoe UI", int(11 * scale))

        for row, state in enumerate(states):
            for col, val in enumerate(state):
                item = QTableWidgetItem(str(val))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                item.setFont(font)
                self.truth_table.setItem(row, col, item)

            # Spacer
            spacer = QTableWidgetItem("")
            spacer.setFlags(Qt.NoItemFlags)
            self.truth_table.setItem(row, entity_count, spacer)

            for col in range(entity_count + 1, 2 * entity_count + 1):
                item = QTableWidgetItem("")
                item.setFont(font)
                self.truth_table.setItem(row, col, item)

        self.truth_table.setFont(font)
        self.truth_table.verticalHeader().setDefaultSectionSize(int(30 * scale))

        # 🌐 Responsive column resizing
        self.truth_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Binary validator
        for col in range(entity_count + 1, 2 * entity_count + 1):
            self.truth_table.setItemDelegateForColumn(col, BinaryOnlyDelegate(self.truth_table))

    def save_and_process_truth_table(self):

        entity_count = self.entity_count_selector.value()
        entities = [chr(65 + i) for i in range(entity_count)]
        network_name = self.network_name_input.text().strip()
        filename = network_name if network_name.endswith(".json") else network_name + ".json"

        # Build truth table (string values)
        truth_table = {}
        for row in range(self.truth_table.rowCount()):
            input_state = "".join(self.truth_table.item(row, col).text().strip() for col in range(entity_count))
            output_bits = []
            for col in range(entity_count + 1, 2 * entity_count + 1):
                item = self.truth_table.item(row, col)
                value = item.text().strip() if item else ""
                item.setBackground(Qt.white)  # Clear old highlights
                output_bits.append(value)
            truth_table[input_state] = output_bits


        is_valid, message = validate_truth_table_inputs(network_name, truth_table, entity_count)
        if not is_valid:
            # If validation fails, highlight first invalid celle
            if "Row" in message and "column" in message:
                import re
                match = re.search(r"Row (\d+).*column '([A-Z]')", message)
                if match:
                    row_idx = int(match.group(1)) - 1
                    col_label = match.group(2)
                    # Get actual column index from header label
                    for col in range(self.truth_table.columnCount()):
                        if self.truth_table.horizontalHeaderItem(col).text() == col_label:
                            self.truth_table.item(row_idx, col).setBackground(Qt.red)
                            break

            QMessageBox.warning(self, "Validation Failed", message)
            return


        cleaned_table = {
            k: [int(v) for v in v_list]
            for k, v_list in truth_table.items()
        }


        try:
            rules = TruthTableToRules.convert(cleaned_table, entities, minimise=True, readable=True)
        except Exception as e:
            QMessageBox.critical(self, "Rule Conversion Failed", f"An error occurred:\n{e}")
            return


        BooleanNetworkStorage.save_network(filename, entities, rules, cleaned_table)
        rules_text = "\n".join([f"{k}' = {v}" for k, v in rules.items()])
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Network Saved")
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setText(f"Network '{filename}' saved successfully.\n\nGenerated Rules:\n{rules_text}")
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec()


