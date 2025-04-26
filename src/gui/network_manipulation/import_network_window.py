
import os
import pandas as pd
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog,
    QLineEdit, QHBoxLayout, QTableWidget, QTableWidgetItem, QMessageBox
)
from PySide6.QtCore import Qt
from src.boolean_network_representation.rules import TruthTableToRules
from src.boolean_network_representation.storage import BooleanNetworkStorage


class ImportNetworkWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Import Boolean Network from CSV")
        self.setGeometry(150, 150, 900, 600)

        self.layout = QVBoxLayout()
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_widget.setLayout(self.layout)

        # Title
        title = QLabel("📥 Import Boolean Network from CSV")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18pt; font-weight: bold; margin-bottom: 15px;")
        self.layout.addWidget(title)

        # File picker/drag and drop
        self.instructions = QLabel("Drag a CSV/XLSX file here or use the button below.")
        self.instructions.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.instructions)

        self.upload_button = QPushButton("📂 Select File to Import")
        self.upload_button.setFixedHeight(40)
        self.upload_button.clicked.connect(self.select_file)
        self.layout.addWidget(self.upload_button, alignment=Qt.AlignHCenter)

        # File drop support
        self.setAcceptDrops(True)

        # Network name
        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("Network Name:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. Imported Network 40")
        self.name_input.setFixedWidth(300)
        name_row.addWidget(self.name_input)
        name_row.addStretch()
        self.layout.addLayout(name_row)

        # Table preview
        self.preview_table = QTableWidget()
        self.layout.addWidget(self.preview_table)

        # Save button
        self.save_button = QPushButton("💾 Import and Save Network")
        self.save_button.setFixedHeight(40)
        self.save_button.clicked.connect(self.process_imported_data)
        self.layout.addWidget(self.save_button)

        # Template download buttons
        template_row = QHBoxLayout()
        csv_button = QPushButton("📄 Open CSV Template")
        xlsx_button = QPushButton("📊 Open Excel Template")

        base_dir = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.join(base_dir, "..", "example_import_files", "example_csv_template.csv")
        xlsx_path = os.path.join(base_dir, "..", "example_import_files", "example_excel_template.xlsx")
        csv_button.clicked.connect(lambda: os.startfile(os.path.normpath(csv_path)))
        xlsx_button.clicked.connect(lambda: os.startfile(os.path.normpath(xlsx_path)))
        template_row.addStretch()
        template_row.addWidget(csv_button)
        template_row.addWidget(xlsx_button)
        template_row.addStretch()
        self.layout.addLayout(template_row)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            self.load_file(path)

    def select_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "CSV or Excel Files (*.csv *.xlsx)")
        if path:
            self.load_file(path)

    def load_file(self, path):
        try:
            if path.endswith(".csv"):
                df = pd.read_csv(path)
            elif path.endswith(".xlsx"):
                df = pd.read_excel(path)
            else:
                raise ValueError("Unsupported file format.")

            self.df = df
            self.display_table(df)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load file:\n{e}")

    def display_table(self, df):
        self.preview_table.clear()
        self.preview_table.setRowCount(len(df))
        self.preview_table.setColumnCount(len(df.columns))
        self.preview_table.setHorizontalHeaderLabels(list(df.columns))

        for i in range(len(df)):
            for j in range(len(df.columns)):
                item = QTableWidgetItem(str(df.iat[i, j]))
                self.preview_table.setItem(i, j, item)

        self.preview_table.resizeColumnsToContents()

    def process_imported_data(self):
        if not hasattr(self, 'df'):
            QMessageBox.warning(self, "No File", "Please import a CSV or Excel file first.")
            return

        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Missing Name", "Please provide a name for the network.")
            return

        # Check for duplicate
        existing_files = os.listdir("saved_networks")
        if f"{name}.json" in existing_files:
            QMessageBox.warning(self, "Duplicate Name", f"A network named '{name}' already exists.")
            return

        df = self.df.copy()
        input_cols = df.columns[:len(df.columns) // 2]
        output_cols = df.columns[len(df.columns) // 2:]
        entities = [col.replace("'", "") for col in output_cols]

        # Validate
        errors = []
        for col in input_cols:
            if not df[col].isin([0, 1]).all():
                errors.append(f"Non-binary values found in column '{col}'.")

        for col in output_cols:
            if not df[col].isin([0, 1]).all():
                errors.append(f"Non-binary values found in column '{col}'.")

        if errors:
            QMessageBox.critical(self, "Invalid Data", "\n".join(errors))
            return

        # Build truth table
        truth_table = {
            "".join(map(str, df.loc[i, input_cols].astype(int))): list(df.loc[i, output_cols])
            for i in range(len(df))
        }

        # Infer rules
        try:
            rules = TruthTableToRules.convert(truth_table, entities, minimise=True, readable=True)
        except Exception as e:
            QMessageBox.critical(self, "Rule Inference Failed", f"An error occurred:\n{e}")
            return

        # Save
        BooleanNetworkStorage.save_network(name, entities, rules, truth_table)

        # Success popup
        rules_text = "\n".join([f"{k}' = {v}" for k, v in rules.items()])
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Network Saved")
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setText(f"Network '{name}' saved successfully.\n\nGenerated Rules:\n{rules_text}")
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec()
