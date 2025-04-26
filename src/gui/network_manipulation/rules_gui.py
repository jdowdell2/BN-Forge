import itertools
from PySide6.QtWidgets import (
    QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget, QSpinBox, QHBoxLayout, QLineEdit, QMessageBox, QSizePolicy
)
from PySide6.QtGui import QFont, Qt

from src.gui.rule_builder_gui import RuleBuilder
from src.boolean_network_representation.storage import BooleanNetworkStorage
from src.data_processing.truth_table_from_gui_import import generate_truth_table
from src.data_processing.rule_validation import validate_rule



class RulesGUI(QMainWindow):
    """Not to be confused with RuleBuilder, this is the Rules Window"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Define Boolean Network Rules")
        self.setGeometry(150, 150, 900, 600)

        self.layout = QVBoxLayout()
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_widget.setLayout(self.layout)

        # Title
        title_label = QLabel("Define Boolean Network Rules")
        title_font = QFont("Segoe UI", 16, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(title_label)

        sub_label_font = QFont("Segoe UI", 10, QFont.Weight.Bold)

        # Network name
        self.name_label = QLabel("Enter Network Name:")
        self.name_label.setFont(sub_label_font)
        self.layout.addWidget(self.name_label)

        self.network_name_input = QLineEdit()
        self.network_name_input.setPlaceholderText("Network")
        self.layout.addWidget(self.network_name_input)

        # Entity count selector
        self.label = QLabel("Select Number of Entities (2-10):")
        self.label.setFont(sub_label_font)
        self.layout.addWidget(self.label)

        self.entity_count_selector = QSpinBox()
        self.entity_count_selector.setMinimum(2)
        self.entity_count_selector.setMaximum(10)
        self.entity_count_selector.setValue(3)
        self.entity_count_selector.valueChanged.connect(self.generate_rule_inputs)
        self.layout.addWidget(self.entity_count_selector)


        self.rules_container = QVBoxLayout()
        self.layout.addLayout(self.rules_container)

        # Save network button
        self.save_button = QPushButton("💾 Save Network")
        self.save_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.save_button.setFixedHeight(40)
        save_button_layout = QHBoxLayout()
        save_button_layout.addWidget(self.save_button)
        self.layout.addLayout(save_button_layout)
        self.save_button.clicked.connect(self.save_rules)
        self.layout.addWidget(self.save_button)

        self.generate_rule_inputs()

    def clear_layout(self, layout):
        """Removes all widgets from a layout to prevent stacking issues."""
        while layout.count():
            item = layout.takeAt(0)  # Take the first item from the layout
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self.clear_layout(item.layout())  # Recursively clear sub-layouts

    def generate_rule_inputs(self):
        self.clear_layout(self.rules_container)

        entity_count = self.entity_count_selector.value()
        self.entity_names = [chr(65 + i) for i in range(entity_count)]  # Name alphabetically

        self.rule_inputs = []
        for i in range(entity_count):
            row_layout = QHBoxLayout()
            label = QLabel(f"Rule for {self.entity_names[i]}' = ")
            row_layout.addWidget(label)

            # Create RuleBuilder box
            rule_builder = RuleBuilder(self.entity_names, self.entity_names[i])
            row_layout.addWidget(rule_builder)

            self.rule_inputs.append(rule_builder)
            self.rules_container.addLayout(row_layout)

    def get_network_name(self):
        name = self.network_name_input.text().strip()
        return name if name else "user_defined_network"


    @staticmethod
    def format_rule_for_python(rule_expression):
        """
        Converts GUI-generated Boolean expressions into Python-compatible format.
        'AND' -> 'and', 'OR' -> 'or', 'NOT' -> 'not', 'XOR' -> '^'.
        """
        if not isinstance(rule_expression, str):
            return rule_expression

        # Normalise spacing
        rule_expression = rule_expression.replace("(", " ( ").replace(")", " ) ")

        # tokenise
        tokens = rule_expression.split()
        translated = []

        for token in tokens:
            if token == "AND":
                translated.append("and")
            elif token == "OR":
                translated.append("or")
            elif token == "NOT":
                translated.append("not")
            elif token == "XOR":
                translated.append("^")
            else:
                translated.append(token)
        return " ".join(translated)

    def generate_truth_table(self, entities, rules):
        entity_count = len(entities)
        states = list(itertools.product([0, 1], repeat=entity_count))
        truth_table = {}

        for state in states:
            inputs = {entities[i]: state[i] for i in range(entity_count)}
            next_state = []

            for entity in entities:
                raw_expr = rules[entity]
                python_expr = RulesGUI.format_rule_for_python(raw_expr)
                try:
                    next_state_value = eval(python_expr, {}, inputs)
                    next_state.append(int(next_state_value))
                except Exception as e:
                    print(f"Error evaluating rule for {entity}: {e} | Rule: {python_expr}")
                    next_state.append(0)

            truth_table["".join(map(str, state))] = next_state

        return truth_table


    def save_rules(self):
        network_name = self.network_name_input.text().strip()
        errors = []

        if not network_name:
            errors.append("⚠️ Network name is required.")

        rules = {
            self.entity_names[i]: self.rule_inputs[i].get_expression()
            for i in range(len(self.entity_names))
        }

        entities = self.entity_names

        for rule_input in self.rule_inputs:
            rule_input.preview_box.setStyleSheet("")
            rule_input.preview_box.setText(rule_input.get_expression())

        for i, (entity, rule_expr) in enumerate(rules.items()):
            is_valid, message = validate_rule(rule_expr, entities)

            rule_input_widget = self.rule_inputs[i]
            preview_box = rule_input_widget.preview_box

            if is_valid:
                preview_box.setStyleSheet("background-color: #e0fbe0;")
                current_text = preview_box.toPlainText().strip()
                if not current_text.endswith("✓"):
                    preview_box.setText(current_text + "  ✓")
            else:
                preview_box.setStyleSheet("background-color: #fddede;")
                errors.append(f"❌ {entity}: {message}")

        if errors:
            msg = QMessageBox()
            msg.setWindowTitle("Invalid Input")
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Please fix the following issues:\n\n" + "\n".join(errors))
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec()
            return

        # All rules valid — generate truth table and save
        truth_table = generate_truth_table(entities, rules, RulesGUI.format_rule_for_python)
        BooleanNetworkStorage.save_network(network_name, entities, rules, truth_table)

        msg = QMessageBox()
        msg.setWindowTitle("Rules Saved Successfully")
        msg.setText(f"Network '{network_name}' saved successfully.")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec()







