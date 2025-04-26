import os
import json
import re
import tempfile
import networkx as nx
import yaml

from src.gui.inference.cost_plot_window import CostPlotWindow
from src.gui.utils.backend_runner import BackendRunner
from src.experiments.run_experiment import main as run_backend
from src.gui.visualisation.wiring_diagram_window import WiringDiagramWindow

from PySide6.QtWidgets import (
    QMainWindow, QApplication, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel,
    QMessageBox, QComboBox, QLineEdit, QRadioButton, QButtonGroup, QGroupBox, QSpacerItem,
    QSizePolicy, QGridLayout
)
from PySide6.QtCore import QTimer, QThread, Qt


def convert_gui_to_legacy(input_path, output_path):
    with open(input_path, "r") as f:
        data = json.load(f)

    if "truth_table" not in data:
        print("Error: 'truth_table' not found in file.")
        return

    # take the truth table and save it directly
    flat = {
        k: v if isinstance(v, list) else list(v)
        for k, v in data["truth_table"].items()
    }

    with open(output_path, "w") as out:
        json.dump(flat, out, indent=2)

    print(f"✅ Converted to legacy format and saved to: {output_path}")


def draw_wiring_overlay_arrows(current_rules, target_rules, ax):
    def extract_edges(rules):
        edges = set()
        for node, expr in rules.items():
            tokens = re.split(r"[()\s]+", expr)
            for token in tokens:
                token = token.strip()
                if token and token != node and token.isalnum():
                    edges.add((token, node))
        return edges

    edges_current = extract_edges(current_rules)
    edges_target = extract_edges(target_rules)

    shared_edges = edges_current & edges_target
    extra_edges = edges_current - edges_target
    missing_edges = edges_target - edges_current

    all_nodes = set()
    for e in shared_edges | extra_edges | missing_edges:
        all_nodes.update(e)

    G = nx.DiGraph()
    G.add_nodes_from(all_nodes)
    pos = nx.shell_layout(G)

    ax.clear()
    nx.draw_networkx_nodes(G, pos, ax=ax, node_color='lightblue', node_size=1500)
    nx.draw_networkx_labels(G, pos, ax=ax, font_size=10)

    arrow_params = dict(
        arrows=True,
        arrowstyle='-|>',
        arrowsize=20,
        connectionstyle='arc3,rad=0.2',
        min_source_margin=15,
        min_target_margin=15
    )

    nx.draw_networkx_edges(G, pos, edgelist=list(shared_edges), ax=ax,
                           edge_color='green', style='solid', width=2, **arrow_params)
    nx.draw_networkx_edges(G, pos, edgelist=list(extra_edges), ax=ax,
                           edge_color='red', style='dotted', width=2, **arrow_params)
    nx.draw_networkx_edges(G, pos, edgelist=list(missing_edges), ax=ax,
                           edge_color='blue', style='dashed', width=2, **arrow_params)

    ax.set_title("Boolean Network Wiring (Live Overlay)")
    ax.axis("off")

    total_target = len(edges_target)
    mismatches = len(extra_edges | missing_edges)
    return 1 - (mismatches / total_target) if total_target > 0 else 1.0


class LiveEvolutionWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Live Boolean Network Evolution")
        self.setGeometry(200, 200, 1000, 800)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        self.setStyleSheet("""
                QLabel { font-size: 14px; }
                QPushButton { padding: 12px; font-weight: bold; min-height: 60px; }
                QPushButton:checked {
                    background-color: #007acc;
                    color: white;
                    border: 1px solid #005999;
                }
                QGroupBox {
                    border: 1px solid #ccc;
                    border-radius: 5px;
                    margin-top: 10px;
                    padding: 10px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    font-weight: bold;
                }
            """)

        self.title_label = QLabel("Live Boolean Network Evolution Viewer")
        self.title_label.setStyleSheet("font-size: 26px; font-weight: bold; margin-top: 10px;")
        self.main_layout.addWidget(self.title_label, alignment=Qt.AlignmentFlag.AlignHCenter)

        content_layout = QHBoxLayout()
        self.main_layout.addLayout(content_layout)

        # Left Panel: Metaheuristic parameters
        param_box = QGroupBox("Metaheuristic Settings")
        param_layout = QVBoxLayout()
        param_box.setLayout(param_layout)

        label_target = QLabel("Target Network:")
        label_target.setStyleSheet("font-weight: bold; font-size: 14px;")
        param_layout.addWidget(label_target)
        self.file_selector = QComboBox()
        self.populate_file_selector()
        param_layout.addWidget(self.file_selector)

        label_meta = QLabel("Metaheuristic:")
        label_meta.setStyleSheet("font-weight: bold; font-size: 14px;")
        param_layout.addWidget(label_meta)
        self.meta_selector = QComboBox()
        self.meta_selector.addItems(["Genetic Algorithm", "Simulated Annealing"])
        self.meta_selector.currentIndexChanged.connect(self.update_params_fields)
        param_layout.addWidget(self.meta_selector)

        label = QLabel("Parameters:")
        label.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 5px;")
        param_layout.addWidget(label)
        self.param_inputs = {}
        self.param_form = QVBoxLayout()
        param_layout.addLayout(self.param_form)

        content_layout.addWidget(param_box)

        # Right: Visualisation and update options
        graph_box = QGroupBox("Visualisation Settings")
        graph_layout = QVBoxLayout()
        graph_box.setLayout(graph_layout)

        self.log_button = QPushButton("Log Experiment Results to File")
        self.log_button.setCheckable(True)
        self.log_button.setChecked(False)
        self.log_button.setMinimumHeight(40)
        graph_layout.addWidget(self.log_button)

        self.export_diagrams_button = QPushButton("Export Final + Desired State Graphs")
        self.export_diagrams_button.setCheckable(True)
        self.export_diagrams_button.setChecked(False)
        self.export_diagrams_button.setMinimumHeight(40)
        graph_layout.addWidget(self.export_diagrams_button)

        cost_label = QLabel("Cost Visuals")
        cost_label.setStyleSheet("font-weight: bold; margin-top: 5px;")
        graph_layout.addWidget(cost_label)

        cost_buttons = QGridLayout()
        self.cost_button = QPushButton("Live Cost Graph")
        self.fullplot_button = QPushButton("Full Resolution Cost Graph after Evolution")
        for b in (self.cost_button, self.fullplot_button):
            b.setCheckable(True)
            b.setChecked(False)
            b.setMinimumHeight(80)
            b.setMinimumWidth(150)
        cost_buttons.addWidget(self.cost_button, 0, 0)
        cost_buttons.addWidget(self.fullplot_button, 0, 1)



        graph_layout.addLayout(cost_buttons)

        graph_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))

        struct_label = QLabel("Network Structure")
        struct_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        graph_layout.addWidget(struct_label)
        struct_buttons = QHBoxLayout()
        self.wiring_button = QPushButton("Entity Interaction Wiring")
        self.attractors_button = QPushButton("Attractor Diagram")
        for b in (self.wiring_button, self.attractors_button):
            b.setCheckable(True)
            b.setChecked(False)
            b.setMinimumHeight(60)
            struct_buttons.addWidget(b)
        graph_layout.addLayout(struct_buttons)

        rate_layout = QHBoxLayout()
        self.realtime_radio = QRadioButton("Real-time")
        self.custom_radio = QRadioButton("Custom:")
        self.update_rate_input = QLineEdit()
        self.update_rate_input.setFixedWidth(60)
        self.update_rate_input.setEnabled(False)
        rate_group = QButtonGroup()
        rate_group.addButton(self.realtime_radio)
        rate_group.addButton(self.custom_radio)
        self.custom_radio.toggled.connect(lambda checked: self.update_rate_input.setEnabled(checked))
        rate_layout.addWidget(QLabel("Update Rate:"))
        rate_layout.addWidget(self.realtime_radio)
        rate_layout.addWidget(self.custom_radio)
        rate_layout.addWidget(self.update_rate_input)
        rate_layout.addWidget(QLabel("updates/sec"))
        graph_layout.addLayout(rate_layout)

        interval_layout = QHBoxLayout()
        self.interval_label = QLabel("Update Interval (Generations):")
        self.interval_input = QLineEdit()
        self.interval_input.setFixedWidth(60)
        self.interval_input.setText("1")
        self.log_checkbox = QPushButton("Logarithmic Y-Axis")
        self.log_checkbox.setCheckable(True)
        self.log_checkbox.setChecked(False)



        interval_layout.addWidget(self.interval_label)
        interval_layout.addWidget(self.interval_input)
        interval_layout.addSpacing(10)
        interval_layout.addWidget(self.log_checkbox)
        interval_layout.addStretch()
        graph_layout.addLayout(interval_layout)

        content_layout.addWidget(graph_box)

        self.go_button = QPushButton("ðŸš€ Start Evolution")
        self.go_button.setFixedWidth(300)
        self.main_layout.addWidget(self.go_button, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.go_button.clicked.connect(self.start_evolution)

        self.timer = QTimer()
        self.live_json_path = os.path.join(tempfile.gettempdir(), "current_evolution.json")
        self.last_step = -1
        self.target_rules = {}
        self.attractor_windows = []


        self.update_params_fields()

    def populate_file_selector(self):
        directory = "saved_networks"
        if not os.path.exists(directory):
            os.makedirs(directory)
        for file in os.listdir(directory):
            if file.endswith(".json"):
                self.file_selector.addItem(file)

    def update_params_fields(self):
        while self.param_form.count():
            child = self.param_form.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self.param_inputs = {}
        method = self.meta_selector.currentText()

        if method == "Genetic Algorithm":
            fields = ["Population Size", "Mutation Rate", "Crossover Rate", "Generations"]
        else:
            fields = ["Initial Temperature", "Cooling Rate", "Generations"]
            self.interval_label.setText("Update Interval (Iterations):")

        for name in fields:
            label = QLabel(name)
            field = QLineEdit()
            field.setFixedWidth(200)
            self.param_inputs[name] = field
            self.param_form.addWidget(label)
            self.param_form.addWidget(field)

        cost_label = QLabel("Cost Function")
        cost_dropdown = QComboBox()
        cost_dropdown.addItems(["hamming_distance", "attractor_difference"])
        cost_dropdown.setFixedWidth(200)

        mut_label = QLabel("Mutation Function")
        mut_dropdown = QComboBox()
        mut_dropdown.addItems(["flip_mutation (bit-flip)", "edame_mutation (attractor-based)"])
        mut_dropdown.setFixedWidth(200)



        self.param_inputs["Cost Function"] = cost_dropdown
        self.param_inputs["Mutation Function"] = mut_dropdown
        self.param_form.addWidget(cost_label)
        self.param_form.addWidget(cost_dropdown)
        self.param_form.addWidget(mut_label)
        self.param_form.addWidget(mut_dropdown)

    def start_evolution(self):
        # Cleanup from previous run if needed
        if hasattr(self, "backend_thread") and self.backend_thread.isRunning():
            self.backend_thread.quit()
            self.backend_thread.wait()
            print("🧹 Previous backend thread cleaned up.")

        if hasattr(self, "worker"):
            self.worker.deleteLater()
            self.worker = None

        if hasattr(self, "cost_window") and self.cost_window:
            self.cost_window.close()
            self.cost_window = None

        if hasattr(self, "wiring_window") and self.wiring_window:
            self.wiring_window.close()
            self.wiring_window = None

        if hasattr(self, "attractors_window") and self.attractors_window:
            self.attractors_window.close()
            self.attractors_window = None


        target_file = os.path.join("saved_networks", self.file_selector.currentText())
        method = self.meta_selector.currentText()

        # GUI → backend key mapping
        backend_keys = {
            "Population Size": "pop_size",
            "Mutation Rate": "mutation_rate",
            "Crossover Rate": "crossover_rate",
            "Generations": "max_gens",
            "Initial Temperature": "initial_temp",
            "Cooling Rate": "cooling_rate"
        }

        # Extract user inputs
        raw_parameters = {}
        for key, field in self.param_inputs.items():
            if isinstance(field, QComboBox):
                raw_parameters[key] = field.currentText().split()[0]
            else:
                raw_parameters[key] = field.text()

        # Normalise to keys
        flat_params = {}
        for gui_key, backend_key in backend_keys.items():
            val = raw_parameters.get(gui_key)
            try:
                flat_params[backend_key] = float(val) if "." in val or "e" in val.lower() else int(val)
            except (TypeError, ValueError):
                flat_params[backend_key] = None  # fallback

        # Update rate
        try:
            update_interval = int(self.interval_input.text())
        except ValueError:
            update_interval = 1

        self.update_rate_ms = (
            0 if self.realtime_radio.isChecked()
            else max(200, int(1000 / float(self.update_rate_input.text() or 1)))
        )

        # validation check
        if method == "Genetic Algorithm":
            try:
                if not (0 <= flat_params.get("mutation_rate", 0) <= 1):
                    raise ValueError("Mutation rate must be between 0 and 1.")
                if not (0 <= flat_params.get("crossover_rate", 0) <= 1):
                    raise ValueError("Crossover rate must be between 0 and 1.")
            except ValueError as e:
                QMessageBox.warning(self, "Parameter Error", str(e))
                return

        # Build config
        config_dict = {
            "metaheuristic": "simulated_annealing" if method == "Simulated Annealing" else "genetic_algorithm",
            "cost_function": "hamming" if raw_parameters["Cost Function"] == "hamming_distance" else "attractor",
            "mutation_function": "flip_bit" if "flip" in raw_parameters["Mutation Function"] else "edame",
            "log_results": self.log_button.isChecked(),
            "log_interval": update_interval,
            "live_update_interval": update_interval,
            "generate_graphs": self.export_diagrams_button.isChecked(),
        }

        if method == "Simulated Annealing":
            config_dict["temperature"] = {
                "initial": flat_params.get("initial_temp", 100),
                "cooling_rate": flat_params.get("cooling_rate", 0.95)
            }
            config_dict["max_iterations"] = flat_params.get("max_gens", 1000)
        else:
            config_dict.update({
                "pop_size": flat_params.get("pop_size", 50),
                "max_gens": flat_params.get("max_gens", 100),
                "mutation_rate": flat_params.get("mutation_rate", 0.1),
                "crossover_rate": flat_params.get("crossover_rate", 0.7)
            })

        # target trace
        with open(target_file, "r") as f:
            full_data = json.load(f)

        self.target_rules = full_data.get("rules")
        flat_table = full_data.get("truth_table", full_data)
        flat_table = {k: v if isinstance(v, list) else list(v) for k, v in flat_table.items()}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as temp_json:
            json.dump(flat_table, temp_json)
            legacy_json_path = temp_json.name

        config_dict["load_network_path"] = legacy_json_path
        config_dict["network_name"] = self.file_selector.currentText().replace(".json", "")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as temp_yaml:
            yaml.dump(config_dict, temp_yaml)
            config_path = temp_yaml.name

        print(f"Running {method} with config at {config_path}")
        self.show_final_plot = self.fullplot_button.isChecked()

        if self.cost_button.isChecked():
            self.cost_window = CostPlotWindow(
                log_scale=self.log_checkbox.isChecked(),
                method=self.meta_selector.currentText()
            )
            self.cost_window.show()
        else:
            self.cost_window = None

        self.backend_thread = QThread()
        self.worker = BackendRunner(
            config_path,
            show_full_plot=self.fullplot_button.isChecked(),
            log_scale=self.log_checkbox.isChecked(),
            method=self.meta_selector.currentText(),
        )

        self.worker.desired_attractor_edges = set()
        self.worker.wiring_update.connect(self.update_wiring_diagram)
        self.worker.attractors_update.connect(self.handle_attractor_update)
        self.worker.moveToThread(self.backend_thread)

        if self.cost_window:
            self.worker.progress.connect(self.cost_window.append)

        self.worker.finished.connect(self.backend_thread.quit)
        self.worker.done_with_history.connect(self.show_full_resolution_plot)
        self.worker.finished.connect(self.show_wiring_diagram)

        self.backend_thread.started.connect(self.worker.run)
        self.backend_thread.start()
        self.last_step = -1
        self.cost_data = []

    def show_wiring_diagram(self):
        if hasattr(self, 'wiring_button') and self.wiring_button.isChecked():
            try:
                from src.boolean_network_representation.network import BooleanNetwork
                from src.gui.visualisation.wiring_diagram_window import WiringDiagramWindow

                if not self.latest_wiring_diagram:
                    print("⚠️ No wiring graph available yet.")
                    return

                # Use the final evolved network directly
                G_current = self.latest_wiring_diagram

                target_net = BooleanNetwork(entity_count=len(self.target_rules))
                target_net.current_rules = target_net._rule_loader.parse_rule_dict(self.target_rules)
                deps_target = target_net.infer_wiring()
                G_target = target_net.build_wiring_graph(deps_target)

                self.wiring_window = WiringDiagramWindow(G_current, G_target)
                self.wiring_window.show()
            except Exception as e:
                print("⚠️ Failed to open wiring diagram:", e)

    def update_wiring_diagram(self, latest_graph):
        self.latest_wiring_diagram = latest_graph

        if self.target_rules:
            from src.boolean_network_representation.network import BooleanNetwork
            target_net = BooleanNetwork(entity_count=len(self.target_rules))
            target_net.current_rules = target_net._rule_loader.parse_rule_dict(self.target_rules)
            deps_target = target_net.infer_wiring()
            G_target = target_net.build_wiring_graph(deps_target)
        else:
            G_target = nx.DiGraph()  # empty fallback

        if self.wiring_button.isChecked():
            if not hasattr(self, "wiring_window") or self.wiring_window is None:
                self.wiring_window = WiringDiagramWindow(latest_graph, G_target)
                self.wiring_window.destroyed.connect(lambda: setattr(self, "wiring_window", None))
                self.wiring_window.show()
            else:
                self.wiring_window.draw_graph(latest_graph, G_target)

    def handle_attractor_update(self, data):
        if not self.attractors_button.isChecked():
            return

        from src.gui.visualisation.attractor_diagram_window import AttractorDiagramWindow

        step, attractors = data
        method = self.meta_selector.currentText()
        label = "Generation" if "Genetic" in method else "Iteration"
        title = f"Attractors Only ({label} {step})"

        if not hasattr(self, "attractors_window") or self.attractors_window is None:
            self.attractors_window = AttractorDiagramWindow(
                attractors=attractors,
                title=title,
                step=step,
                method=method
            )
            self.attractors_window.destroyed.connect(lambda: setattr(self, "attractors_window", None))
            self.attractors_window.show()
        else:
            self.attractors_window.setWindowTitle(title)
            self.attractors_window.update_data(attractors)


    def run_backend_with_config(self, config_path):
        with open(self.live_json_path, "w") as f:
            f.write(json.dumps({"step": -1, "rules": {}, "cost": None}))

        script_path = os.path.join("experiments", "experiment_setup", "run_experiment.py")
        run_backend(
            config_path,
            progress_callback=self.cost_window.append if self.cost_window else None,
            show_full_plot=self.show_final_plot
        )

    def update_graph(self):
        if not os.path.exists(self.live_json_path):
            return

        try:
            with open(self.live_json_path, "r") as f:
                content = f.read().strip()
                if not content:
                    return
                data = json.loads(content)
        except Exception as e:
            print(f"Live JSON read error: {e}")
            return

        if data.get("step") == self.last_step:
            return

        # Skip ahead to latest step — only show latest
        self.last_step = data["step"]

        # Draw graph (still every step)
        if self.show_graph_checkbox.isChecked():
            rules = data.get("rules", {})
            score = draw_wiring_overlay_arrows(rules, self.target_rules, self.ax) if self.target_rules else 1.0
            self.canvas.draw()
            self.score_label.setText(f"Wiring Similarity: {score * 100:.1f}%")


        # Push to external plot window — only newest value
        if self.self.cost_button.isChecked() and "cost" in data:
            if not hasattr(self, "cost_window"):
                self.cost_window = CostPlotWindow(
                    log_scale=self.log_checkbox.isChecked(),
                    method=self.meta_selector.currentText()
                )
                self.cost_window.show()
            self.cost_window.append(data["step"], data["cost"])

    def show_full_resolution_plot(self, history, method, log_scale):
        try:
            self.full_window = CostPlotWindow(log_scale=log_scale, method=method)

            steps = list(range(len(history)))
            self.full_window.set_history(steps, history)

            self.full_window.show()
        except Exception as e:
            print("❗ Could not show full-resolution plot:", e)

    def export_final_and_desired_graphs(self):
        try:
            os.makedirs("graph_exports", exist_ok=True)

            if self.target_rules is None or not hasattr(self.worker, "latest_network"):
                QMessageBox.warning(self, "Export Error", "Target or final network not available yet.")
                return

            from src.boolean_network_representation.network import BooleanNetwork


            target_net = BooleanNetwork(entity_count=len(self.target_rules))
            target_net.current_rules = target_net._rule_loader.parse_rule_dict(self.target_rules)

            # Final evolved network------
            final_net = self.worker.latest_network

            target_net.generate_state_graph(filename="graph_exports/state_graph_desired")
            final_net.generate_state_graph(filename="graph_exports/state_graph_final")
            target_net.generate_wiring_diagram(filename="graph_exports/wiring_diagram_desired")
            final_net.generate_wiring_diagram(filename="graph_exports/wiring_diagram_final")

            QMessageBox.information(self, "Export Complete", "Graphs exported to 'graph_exports/'.")

        except Exception as e:
            print("❌ Export failed:", e)
            QMessageBox.warning(self, "Export Failed", f"An error occurred:\n{e}")

    def maybe_export_diagrams(self):
        if self.export_diagrams_button.isChecked():
            self.export_final_and_desired_graphs()


if __name__ == "__main__":
    app = QApplication([])
    window = LiveEvolutionWindow()
    window.show()
    app.exec()
