from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QComboBox, QPushButton, QLabel, QTextEdit, QVBoxLayout
)
from PySide6.QtGui import QFont
from src.data_processing.rule_validation import validate_rule


class RuleBuilder(QWidget):
    """Individual RuleBuilder for one rule"""
    def __init__(self, entity_names, target_entity=None):
        super().__init__()
        self.entity_names = entity_names
        self.target_entity = target_entity
        self.expression = []

        # Main layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Top row: label and live preview
        top_row = QHBoxLayout()
        if target_entity:
            label = QLabel(f"Rule for {target_entity}' = ")
            label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            top_row.addWidget(label)

        self.preview_box = QTextEdit()
        self.preview_box.setReadOnly(True)
        self.preview_box.setFixedHeight(30)
        top_row.addWidget(self.preview_box)
        main_layout.addLayout(top_row)

        # Dropdown area
        self.dropdown_row = QHBoxLayout()

        main_layout.addLayout(self.dropdown_row)

        # Control buttons
        controls = QHBoxLayout()
        self.add_button = QPushButton("➕ Add")
        self.add_button.clicked.connect(self.add_element)
        controls.addWidget(self.add_button)

        self.undo_button = QPushButton("↩️ Undo")
        self.undo_button.clicked.connect(self.undo_last_element)
        controls.addWidget(self.undo_button)

        self.clear_button = QPushButton("🗑️ Clear")
        self.clear_button.clicked.connect(self.clear_expression)
        controls.addWidget(self.clear_button)

        main_layout.addLayout(controls)
        self.update_expression()

    def add_element(self):
        """Adds a new element to the Boolean expression with validation."""
        valid_choices = self.get_valid_next_choices()
        if not valid_choices:
            return

        # Lock existing dropdowns
        for dropdown in self.expression:
            dropdown.setDisabled(True)
            dropdown.setStyleSheet("QComboBox:disabled { color: gray; }")

        dropdown = QComboBox()
        dropdown.addItems(valid_choices)
        dropdown.setStyleSheet("""
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
        dropdown.currentIndexChanged.connect(self.update_expression)

        dropdown.setMinimumWidth(80)
        self.dropdown_row.addWidget(dropdown)
        self.expression.append(dropdown)
        self.update_expression()

    def undo_last_element(self):
        """Removes the last added dropdown and re-enables the previous one."""
        if self.expression:
            last = self.expression.pop()
            self.dropdown_row.removeWidget(last)
            last.deleteLater()

            # Re-enable the new last one, if any
            if self.expression:
                previous = self.expression[-1]
                previous.setDisabled(False)
                previous.setStyleSheet("")  # Restore normal color

            self.update_expression()

    def clear_expression(self):
        for dropdown in self.expression:
            self.dropdown_row.removeWidget(dropdown)
            dropdown.deleteLater()
        self.expression.clear()
        self.preview_box.setText("")
        self.preview_box.setStyleSheet("")
        self.update_expression()

    def get_valid_next_choices(self):
        """Context-aware validation for next token. - same rules as in rule_validation file"""
        if not self.expression:
            return ["(", "NOT"] + self.entity_names

        last = self.expression[-1].currentText()
        if last in self.entity_names:
            return [")", "AND", "OR", "XOR"]
        if last == "NOT":
            return ["("] + self.entity_names
        if last in ["AND", "OR", "XOR"]:
            return ["(", "NOT"] + self.entity_names
        if last == "(":
            return ["(", "NOT"] + self.entity_names
        if last == ")":
            return [")", "AND", "OR", "XOR"]
        return []

    def update_expression(self):
        expression = " ".join([e.currentText() for e in self.expression])
        self.preview_box.setText(expression)

        valid, _ = validate_rule(expression, self.entity_names)
        if valid:
            self.preview_box.setStyleSheet("background-color: #e0fbe0;")
            if not expression.strip().endswith("✓"):
                self.preview_box.setText(expression + "  ✓")
        else:
            self.preview_box.setStyleSheet("background-color: #fddede;")

    def get_expression(self):
        return " ".join([e.currentText() for e in self.expression])

    def add_element_by_text(self, text):
        """Used when loading saved rules."""
        dropdown = QComboBox()
        all_tokens = ["AND", "OR", "XOR", "NOT", "(", ")"] + self.entity_names
        dropdown.addItems(all_tokens)
        dropdown.setStyleSheet("""
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

        if text in all_tokens:
            dropdown.setCurrentText(text)
        else:
            dropdown.addItem(text)

        dropdown.currentIndexChanged.connect(self.update_expression)
        dropdown.currentIndexChanged.connect(self.mark_as_edited)

        self.dropdown_row.addWidget(dropdown)
        self.expression.append(dropdown)
        self.update_expression()

    def mark_as_edited(self):
        self.preview_box.setStyleSheet("background-color: #fff8dc;")
