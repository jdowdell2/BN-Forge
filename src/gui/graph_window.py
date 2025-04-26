
import os
import json
from datetime import datetime

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

import networkx as nx
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton,
    QTextEdit, QStackedWidget, QSizePolicy, QTableWidget, QTableWidgetItem, QLabel
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import matplotlib.patches as mpatches

from graphviz import Digraph


class GenerateGraphsWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📊 View Boolean Network Diagrams")
        self.setGeometry(150, 150, 1000, 900)

        self.wiring_shown = False
        self.attractors_shown = False
        self.current_layout = "circular"
        self.info_shown = True

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # Fonts
        header_font = QFont("Segoe UI", 16, QFont.Bold)
        label_font = QFont("Segoe UI", 10, QFont.Bold)

        # Title
        title = QLabel("📊 View Boolean Network Diagrams")
        title.setFont(header_font)
        title.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(title)

        # Top Row - Network Selection
        top_row = QHBoxLayout()
        network_label = QLabel("Select Network:")
        network_label.setFont(label_font)
        top_row.addWidget(network_label)

        self.network_dropdown = QComboBox()
        self.network_dropdown.setFixedWidth(300)
        self.network_dropdown.addItems(self.get_network_list())
        self.network_dropdown.currentIndexChanged.connect(self.load_selected_network)
        top_row.addWidget(self.network_dropdown)
        top_row.addStretch()
        self.main_layout.addLayout(top_row)


        self.toggle_info_btn = QPushButton("Hide Rules + Table")
        self.toggle_info_btn.setFont(label_font)
        self.toggle_info_btn.setFixedHeight(40)
        self.toggle_info_btn.clicked.connect(self.toggle_rule_table)
        self.main_layout.addWidget(self.toggle_info_btn)

        # Combined Rule + Table Panel
        self.rule_table_panel = QWidget()
        self.rule_table_layout = QHBoxLayout(self.rule_table_panel)

        self.rule_box = QTextEdit("Rules will be shown here.")
        self.rule_box.setFont(label_font)
        self.rule_box.setReadOnly(True)
        self.rule_box.setFont(QFont("Segoe UI", 10))
        self.rule_table_layout.addWidget(self.rule_box, 1)

        self.table_widget = QTableWidget()
        self.table_widget.setFont(QFont("Segoe UI", 10))
        self.rule_table_layout.addWidget(self.table_widget, 2)

        self.main_layout.addWidget(self.rule_table_panel)

        # Graph Buttons Row
        button_row = QHBoxLayout()
        self.attractors_btn = QPushButton("🧲 Show Attractors")
        self.state_graph_btn = QPushButton("🔁 Export State Graph")
        self.wiring_graph_btn = QPushButton("🧠 Show Wiring Diagram")
        self.layout_toggle_btn = QPushButton("↔ Switch to Spring Layout")
        self.layout_toggle_btn.setVisible(False)

        for btn in [self.attractors_btn, self.state_graph_btn, self.wiring_graph_btn, self.layout_toggle_btn]:
            btn.setFont(QFont("Segoe UI", 10))
            btn.setFixedHeight(40)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            button_row.addWidget(btn)

        self.main_layout.addLayout(button_row)

        # Graph Output Area
        self.graph_area = QStackedWidget()
        self.graph_placeholder = QTextEdit("Select a diagram to display.")
        self.graph_placeholder.setAlignment(Qt.AlignCenter)
        self.graph_placeholder.setReadOnly(True)
        self.graph_placeholder.setFont(QFont("Segoe UI", 10))
        self.graph_area.addWidget(self.graph_placeholder)

        self.wiring_canvas = FigureCanvas(Figure(figsize=(6, 6)))
        self.wiring_ax = self.wiring_canvas.figure.subplots()
        self.graph_area.addWidget(self.wiring_canvas)

        self.attractor_canvas = FigureCanvas(Figure(figsize=(6, 6)))
        self.attractor_ax = self.attractor_canvas.figure.subplots()
        self.graph_area.addWidget(self.attractor_canvas)

        self.state_shown = False
        self.state_canvas = FigureCanvas(Figure(figsize=(6, 6)))
        self.state_ax = self.state_canvas.figure.subplots()
        self.graph_area.addWidget(self.state_canvas)

        self.main_layout.addWidget(self.graph_area)

        # Connections
        self.wiring_graph_btn.clicked.connect(self.toggle_wiring_diagram)
        self.layout_toggle_btn.clicked.connect(self.switch_layout)
        self.attractors_btn.clicked.connect(self.toggle_attractors)
        self.state_graph_btn.clicked.connect(self.export_state_graph)

        # Load alphabetically first
        if self.network_dropdown.count():
            self.load_selected_network(0)

    def get_network_list(self):
        folder = "saved_networks"
        if not os.path.exists(folder):
            return []
        return [f.replace(".json", "") for f in os.listdir(folder) if f.endswith(".json")]

    def load_selected_network(self, index):
        network_name = self.network_dropdown.currentText()
        path = os.path.join("saved_networks", network_name + ".json")
        if not os.path.exists(path):
            return

        with open(path, "r") as f:
            data = json.load(f)

        rules = data.get("rules", {})
        truth_table = data.get("truth_table", {})
        entities = data.get("entities", [])

        rule_lines = [f"{k}' = {v}" for k, v in rules.items()]
        self.rule_box.setText("\n".join(rule_lines))

        self.table_widget.clear()
        self.table_widget.setRowCount(len(truth_table))
        self.table_widget.setColumnCount(len(entities) * 2)
        headers = entities + [f"{e}'" for e in entities]
        self.table_widget.setHorizontalHeaderLabels(headers)

        for row_idx, (input_str, output_list) in enumerate(truth_table.items()):
            for i, bit in enumerate(input_str):
                self.table_widget.setItem(row_idx, i, QTableWidgetItem(bit))
            for j, bit in enumerate(output_list):
                self.table_widget.setItem(row_idx, len(entities) + j, QTableWidgetItem(str(bit)))

        self.table_widget.resizeColumnsToContents()

    def toggle_rule_table(self):
        self.info_shown = not self.info_shown
        self.rule_table_panel.setVisible(self.info_shown)
        label = "Hide Rules + Table" if self.info_shown else "👁 Show Rules + Table"
        self.toggle_info_btn.setText(label)

    def toggle_wiring_diagram(self):
        if self.attractors_shown:
            self.attractors_shown = False
            self.attractors_btn.setText("🧲 Show Attractors")

        self.wiring_shown = not self.wiring_shown
        if self.wiring_shown:
            self.show_wiring_diagram()
            self.wiring_graph_btn.setText("❌ Hide Wiring Diagram")
            self.layout_toggle_btn.setVisible(True)
        else:
            self.graph_area.setCurrentWidget(self.graph_placeholder)
            self.wiring_graph_btn.setText("🧠 Show Wiring Diagram")
            self.layout_toggle_btn.setVisible(False)

    def toggle_attractors(self):
        if self.wiring_shown:
            self.wiring_shown = False
            self.wiring_graph_btn.setText("🧠 Show Wiring Diagram")
            self.layout_toggle_btn.setVisible(False)

        self.attractors_shown = not self.attractors_shown
        if self.attractors_shown:
            self.show_attractors()
            self.attractors_btn.setText("❌ Hide Attractors")
        else:
            self.graph_area.setCurrentWidget(self.graph_placeholder)
            self.attractors_btn.setText("🧲 Show Attractors")


    def switch_layout(self):
        self.current_layout = "spring" if self.current_layout == "circular" else "circular"
        label = "↺ Switch to Circular Layout" if self.current_layout == "spring" else "↔ Switch to Force-Directed Layout"
        self.layout_toggle_btn.setText(label)
        self.show_wiring_diagram()

    def show_wiring_diagram(self):
        self.wiring_ax.clear()
        network_name = self.network_dropdown.currentText()
        path = os.path.join("saved_networks", network_name + ".json")
        if not os.path.exists(path):
            return

        with open(path, "r") as f:
            data = json.load(f)

        rules = data["rules"]
        entities = data["entities"]

        G = nx.DiGraph()
        G.add_nodes_from(entities)
        for target_entity, rule in rules.items():
            for source in entities:
                if source in rule:
                    G.add_edge(source, target_entity)

        pos = nx.spring_layout(G, seed=42) if self.current_layout == "spring" else nx.circular_layout(G)
        nx.draw_networkx_nodes(G, pos, ax=self.wiring_ax, node_color="lightblue", node_size=1000)
        nx.draw_networkx_labels(G, pos, ax=self.wiring_ax)

        for src, dst in G.edges():
            rad = 0.25 if src != dst else 0.5
            arrow = mpatches.FancyArrowPatch(
                pos[src], pos[dst],
                connectionstyle=f"arc3,rad={rad}",
                arrowstyle='-|>',
                mutation_scale=20,
                color="black",
                lw=1.5,
                shrinkA=20,
                shrinkB=20
            )
            self.wiring_ax.add_patch(arrow)

        self.wiring_ax.set_title(f"Wiring Diagram ({self.current_layout.capitalize()} Layout)")
        self.wiring_ax.axis("off")
        self.wiring_canvas.draw()
        self.graph_area.setCurrentWidget(self.wiring_canvas)

    def show_attractors(self):
        self.attractor_ax.clear()

        network_name = self.network_dropdown.currentText()
        path = os.path.join("saved_networks", network_name + ".json")
        if not os.path.exists(path):
            return

        with open(path, "r") as f:
            data = json.load(f)

        truth_table = data.get("truth_table", {})
        if not truth_table:
            self.attractor_ax.text(0.5, 0.5, "No truth table found.",
                                   ha='center', va='center', fontsize=14, color='red',
                                   transform=self.attractor_ax.transAxes)
            self.attractor_canvas.draw()
            self.graph_area.setCurrentWidget(self.attractor_canvas)
            return

        visited = set()
        attractors = []

        for state in truth_table:
            if state in visited:
                continue
            path = []
            current = state
            while current not in path:
                path.append(current)
                visited.add(current)
                next_state = "".join(str(bit) for bit in truth_table[current])
                current = next_state
            cycle_start = path.index(current)
            attractor = path[cycle_start:]
            if attractor not in attractors:
                attractors.append(attractor)

        G = nx.DiGraph()
        pos = {}
        cycles_per_row = 3
        spacing_x = 6
        spacing_y = 6
        scale = 2.0

        for idx, cycle in enumerate(attractors):
            subG = nx.DiGraph()
            for i in range(len(cycle)):
                subG.add_edge(cycle[i], cycle[(i + 1) % len(cycle)])
            sub_pos = nx.circular_layout(subG, scale=scale)
            col, row = idx % cycles_per_row, idx // cycles_per_row
            offset_x, offset_y = col * spacing_x, -row * spacing_y
            for node in sub_pos:
                sub_pos[node][0] += offset_x
                sub_pos[node][1] += offset_y
            G.add_nodes_from(subG.nodes())
            G.add_edges_from(subG.edges())
            pos.update(sub_pos)

        if not G.nodes:
            self.attractor_ax.text(0.5, 0.5, "No Attractors Found",
                                   ha='center', va='center', fontsize=14, color='red',
                                   transform=self.attractor_ax.transAxes)
        else:
            nx.draw_networkx_nodes(G, pos, ax=self.attractor_ax, node_color='lightgray', node_size=1400)
            nx.draw_networkx_labels(G, pos, ax=self.attractor_ax, font_size=10)
            nx.draw_networkx_edges(G, pos, ax=self.attractor_ax, edgelist=G.edges(),
                                   edge_color='black', connectionstyle='arc3,rad=0.1',
                                   width=2, arrows=True, arrowsize=20,
                                   min_source_margin=15, min_target_margin=15)

        self.attractor_ax.set_title("Boolean Network Attractors")
        self.attractor_ax.axis("off")
        self.attractor_canvas.draw()
        self.graph_area.setCurrentWidget(self.attractor_canvas)

    def export_state_graph(self):
        network_name = self.network_dropdown.currentText()
        path = os.path.join("saved_networks", network_name + ".json")
        if not os.path.exists(path):
            return

        with open(path, "r") as f:
            data = json.load(f)

        truth_table = data.get("truth_table", {})
        if not truth_table:
            print("❌ No truth table found.")
            return

        # Export directory: graph_exports/<network_name>/ (gets created if the folder does not yet exist)
        export_dir = os.path.join("graph_exports", network_name)
        os.makedirs(export_dir, exist_ok=True)

        # Timestamped filename
        timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        filename = f"{timestamp}_state_graph"
        filepath = os.path.join(export_dir, filename)

        # manual implementation of state_graph_generator
        dot = Digraph(comment=f'State Graph for {network_name}')
        dot.attr(rankdir='LR')  # Left-to-right layout
        dot.attr(label=network_name, fontsize="20", labelloc="t", fontname="Segoe UI")
        for state, next_bits in truth_table.items():
            next_state = "".join(str(bit) for bit in next_bits)
            dot.node(state)
            dot.node(next_state)
            dot.edge(state, next_state)

        # Save and open
        output_path = dot.render(filepath, format='png', view=True)
        print(f"✅ State graph exported to: {output_path}")


