import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QComboBox, QLabel,
    QPushButton, QHBoxLayout, QMessageBox, QSizePolicy
)
from PySide6.QtGui import QFont, Qt
from src.gui.network_manipulation.rules_gui import RulesGUI
from src.gui.rule_builder_gui import RuleBuilder
from src.boolean_network_representation.storage import BooleanNetworkStorage
from src.data_processing.truth_table_from_gui_import import generate_truth_table
from src.data_processing.rule_validation import validate_rule


class ModifyRulesGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Modify Boolean Network Rules")
        self.setGeometry(200, 200, 800, 500)

        self.layout = QVBoxLayout()
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_widget.setLayout(self.layout)

        self.storage = BooleanNetworkStorage

        # title
        title_label = QLabel("Modify Boolean Network Rules")
        title_font = QFont("Segoe UI", 16, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(title_label)

        # Sub-labels styling
        sub_label_font = QFont("Segoe UI", 10, QFont.Weight.Bold)

        self.load_label = QLabel("Select Existing Network:")
        self.load_label.setFont(sub_label_font)
        self.layout.addWidget(self.load_label)

        self.network_selector = QComboBox()
        self.network_selector.setStyleSheet("""
            QComboBox {
                padding: 4px 8px;
                font-size: 11pt;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
            }
            QComboBox:hover {
                border: 1px solid #888;
                background-color: #f9f9f9;
            }
            QComboBox:focus {
                border: 1px solid #0066cc;
                background-color: #eef6ff;
            }
            QComboBox:disabled {
                color: gray;
                background-color: #f0f0f0;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 18px;
                border-left: 1px solid #aaa;
            }
        """)
        self.network_selector.addItems(self.get_saved_network_names())
        self.network_selector.currentIndexChanged.connect(self.load_selected_network)
        self.layout.addWidget(self.network_selector)

        # Rules layout
        self.rules_container = QVBoxLayout()
        self.layout.addLayout(self.rules_container)

        # Save button
        self.save_button = QPushButton("💾 Save Modified Rules")
        self.save_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.save_button.setFixedHeight(40)
        self.save_button.clicked.connect(self.save_modified_rules)

        save_button_layout = QHBoxLayout()
        save_button_layout.addWidget(self.save_button)
        self.layout.addLayout(save_button_layout)

        self.rule_inputs = []
        self.entity_names = []
        self.current_network_name = None

        if self.network_selector.count():
            self.load_selected_network(0)

    def get_saved_network_names(self):
        folder = "saved_networks"
        if not os.path.exists(folder):
            return []
        return [f.replace(".json", "") for f in os.listdir(folder) if f.endswith(".json")]

    def load_selected_network(self, index):
        network_name = self.network_selector.currentText()
        self.current_network_name = network_name
        data = self.storage.load_network(network_name + ".json")

        self.clear_layout(self.rules_container)
        self.entity_names = data["entities"]
        rules = data["rules"]

        self.rule_inputs = []
        for entity in self.entity_names:
            row_layout = QHBoxLayout()
            label = QLabel(f"Rule for {entity}' = ")
            label.setFont(QFont("Segoe UI", 10, QFont.Weight.Normal))
            row_layout.addWidget(label)

            rule_builder = RuleBuilder(self.entity_names, target_entity=entity)
            for part in rules[entity].split():
                rule_builder.add_element_by_text(part)

            row_layout.addWidget(rule_builder)
            self.rule_inputs.append(rule_builder)
            self.rules_container.addLayout(row_layout)

    def save_modified_rules(self):
        rules = {
            self.entity_names[i]: self.rule_inputs[i].get_expression()
            for i in range(len(self.entity_names))
        }

        # Reset preview boxes
        for rule_input in self.rule_inputs:
            rule_input.preview_box.setStyleSheet("")
            rule_input.preview_box.setText(rule_input.get_expression())

        errors = []
        for i, (entity, rule_expr) in enumerate(rules.items()):
            is_valid, message = validate_rule(rule_expr, self.entity_names)
            preview_box = self.rule_inputs[i].preview_box

            if is_valid:
                preview_box.setStyleSheet("background-color: #e0fbe0;")
                if not preview_box.toPlainText().strip().endswith("✓"):
                    preview_box.setText(preview_box.toPlainText().strip() + "  ✓")
            else:
                preview_box.setStyleSheet("background-color: #fddede;")
                errors.append(f"❌ {entity}: {message}")

        if errors:
            msg = QMessageBox()
            msg.setWindowTitle("Invalid Rules Detected")
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Please fix the following issues:\n\n" + "\n".join(errors))
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec()
            return

        truth_table = generate_truth_table(self.entity_names, rules, RulesGUI.format_rule_for_python)
        self.storage.save_network(self.current_network_name, self.entity_names, rules, truth_table)

        msg = QMessageBox()
        msg.setWindowTitle("Saved")
        msg.setText(f"Modified network '{self.current_network_name}' saved successfully.")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec()

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self.clear_layout(item.layout())
