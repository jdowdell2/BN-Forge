import os
import json
import traceback
from datetime import datetime
import copy
import numpy as np
import pandas as pd
import seaborn as sns

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QLineEdit, QPushButton, QProgressBar, QTextEdit, QGroupBox
)
from PySide6.QtCore import Qt

import matplotlib.pyplot as plt


from PySide6.QtCore import QThread, Signal, QObject

class ExperimentWorker(QObject):
    finished = Signal()
    progress = Signal(int, str)  # run number, message
    result = Signal(str, int, float, float)  # experiment name, run number, cost, time
    failed = Signal(str, int, str)  # experiment name, run number, error

    def __init__(self, config_list):
        super().__init__()
        self.config_list = config_list  # List of tuples: (experiment_name, num_runs, config_dict)

    def run(self):
        import tempfile
        import yaml
        from src.experiments.run_experiment import main as run_experiment_main

        for exp_index, (exp_name, num_runs, config_dict) in enumerate(self.config_list):
            for run_index in range(num_runs):
                try:
                    self.progress.emit(run_index + 1, f"▶️ Running {exp_name} Run {run_index + 1}/{num_runs}...")

                    config_copy = copy.deepcopy(config_dict)
                    config_copy["experiment_name"] = exp_name
                    config_copy["batch_output_dir"] = config_dict["batch_output_dir"]
                    config_copy["is_batch"] = True

                    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as temp_yaml:
                        yaml.dump(config_copy, temp_yaml)
                        config_path = temp_yaml.name

                    history, final_net, elapsed, _ = run_experiment_main(config_path, show_full_plot=False)

                    if isinstance(history, list) and history:
                        final_cost = 0 if len(history) < config_dict.get("max_gens", config_dict.get("max_iterations",
                                                                                                     float('inf'))) else \
                        history[-1]
                    else:
                        final_cost = float("inf")
                    self.result.emit(exp_name, run_index + 1, final_cost, elapsed)

                except Exception as e:
                    self.failed.emit(exp_name, run_index + 1, traceback.format_exc())

        self.finished.emit()




class ExperimentWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Batch Boolean Network Experiment")
        self.setGeometry(200, 200, 1000, 700)

        self.setStyleSheet("""
            QLabel { font-size: 14px; }
            QPushButton {
                padding: 12px;
                font-weight: bold;
                min-height: 60px;
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

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        self.title_label = QLabel("Live Boolean Network Batch Experiment")
        self.title_label.setStyleSheet("font-size: 26px; font-weight: bold; margin-top: 10px;")
        self.main_layout.addWidget(self.title_label, alignment=Qt.AlignmentFlag.AlignHCenter)

        content_layout = QHBoxLayout()
        self.main_layout.addLayout(content_layout)

        # Left
        param_box = QGroupBox("Metaheuristic Settings")
        param_layout = QVBoxLayout()
        param_box.setLayout(param_layout)

        # Network selector
        label_net = QLabel("Target Network:")
        label_net.setStyleSheet("font-weight: bold; font-size: 14px;")
        param_layout.addWidget(label_net)
        self.file_selector = QComboBox()
        self.populate_file_selector()
        param_layout.addWidget(self.file_selector)

        # Metaheuristic selector
        label_meta = QLabel("Metaheuristic:")
        label_meta.setStyleSheet("font-weight: bold; font-size: 14px;")
        param_layout.addWidget(label_meta)
        self.meta_selector = QComboBox()
        self.meta_selector.addItems(["Genetic Algorithm", "Simulated Annealing"])
        self.meta_selector.currentIndexChanged.connect(self.update_params_fields)
        param_layout.addWidget(self.meta_selector)

        # Parameters block
        label_param = QLabel("Parameters:")
        label_param.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 5px;")
        param_layout.addWidget(label_param)

        self.param_inputs = {}
        self.param_form = QVBoxLayout()
        param_layout.addLayout(self.param_form)

        content_layout.addWidget(param_box)

        # Right panel
        output_box = QGroupBox("Output")
        output_layout = QVBoxLayout()
        output_box.setLayout(output_layout)

        self.progress = QProgressBar()
        output_layout.addWidget(self.progress)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        output_layout.addWidget(self.output)

        content_layout.addWidget(output_box)

        self.run_button = QPushButton("ðŸš€ Run Batch")
        self.run_button.clicked.connect(self.run_experiments)
        self.run_button.setFixedWidth(300)
        self.main_layout.addWidget(self.run_button, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Queue controls
        queue_layout = QHBoxLayout()

        self.queue_button = QPushButton("➕ Add to Queue")
        self.queue_button.clicked.connect(self.add_to_queue)
        queue_layout.addWidget(self.queue_button)

        self.start_queue_button = QPushButton("🚀 Run Queue")
        self.start_queue_button.clicked.connect(self.run_experiment_queue)
        queue_layout.addWidget(self.start_queue_button)

        self.main_layout.addLayout(queue_layout)

        self.queue_display = QTextEdit()
        self.queue_display.setReadOnly(True)
        self.queue_display.setFixedHeight(100)
        self.main_layout.addWidget(self.queue_display)

        # Internal experiment queue
        self.experiment_queue = []

        self.update_params_fields()

    def populate_file_selector(self):
        self.file_selector.clear()
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
            fields = ["Initial Temperature", "Cooling Rate", "Iterations"]

        # Add shared controls once
        label_runs = QLabel("Number of Runs:")
        self.param_form.addWidget(label_runs)
        self.runs_input = QLineEdit()
        self.runs_input.setFixedWidth(200)
        self.runs_input.setText("30")
        self.param_form.addWidget(self.runs_input)

        label_cost = QLabel("Cost Function")
        self.cost_dropdown = QComboBox()
        self.cost_dropdown.addItems(["hamming_distance", "attractor_difference"])
        self.cost_dropdown.setFixedWidth(200)
        self.param_form.addWidget(label_cost)
        self.param_form.addWidget(self.cost_dropdown)

        label_mut = QLabel("Mutation Function")
        self.mut_dropdown = QComboBox()
        self.mut_dropdown.addItems(["flip_mutation (bit-flip)", "edame_mutation (attractor-based)"])
        self.mut_dropdown.setFixedWidth(200)
        self.param_form.addWidget(label_mut)
        self.param_form.addWidget(self.mut_dropdown)

        for name in fields:
            label = QLabel(name)
            field = QLineEdit()
            field.setFixedWidth(200)
            self.param_inputs[name.lower()] = field
            self.param_form.addWidget(label)
            self.param_form.addWidget(field)

    def run_experiments(self):
        import tempfile

        self.output.clear()
        self.progress.setValue(0)

        selected_file = self.file_selector.currentText()
        path = os.path.join("saved_networks", selected_file)
        with open(path, "r") as f:
            data = json.load(f)

        if "truth_table" not in data:
            self.output.append("❌ Invalid network file (missing truth_table).")
            return

        flat_table = {k: v if isinstance(v, list) else list(v) for k, v in data["truth_table"].items()}
        real_name = os.path.splitext(selected_file)[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        batch_output_dir = os.path.join("experiment_results", real_name, f"batch_{timestamp}")
        os.makedirs(batch_output_dir, exist_ok=True)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as temp_json:
            json.dump(flat_table, temp_json)
            legacy_json_path = temp_json.name

        try:
            num_runs = int(self.runs_input.text())
        except Exception as e:
            self.output.append(f"❌ Invalid input: {e}")
            return

        # multiple experiment configs
        experiments = []
        # GA configs

        try:
            ga_params = {
                "pop_size": int(self.param_inputs["population size"].text()),
                "mutation_rate": float(self.param_inputs["mutation rate"].text()),
                "crossover_rate": float(self.param_inputs["crossover rate"].text()),
                "max_gens": int(self.param_inputs["generations"].text())
            }
            config_ga = {
                "metaheuristic": "genetic_algorithm",
                "cost_function": "hamming" if self.cost_dropdown.currentText() == "hamming_distance" else "attractor",
                "mutation_function": "flip_bit" if "flip" in self.mut_dropdown.currentText() else "edame",
                "load_network_path": legacy_json_path,
                "network_name": real_name,
                "batch_output_dir": batch_output_dir,
                "log_interval": 9999,
                "live_update_interval": 9999,
                "generate_graphs": False,
                "is_batch": True,
                "log_results": True
            }
            config_ga.update(ga_params)
            experiments.append(("Genetic Algorithm", num_runs, config_ga))
        except Exception:
            pass  # Don't add GA if form isn't filled

        # SA config
        try:
            sa_params = {
                "temperature": {
                    "initial": float(self.param_inputs["initial temperature"].text()),
                    "cooling_rate": float(self.param_inputs["cooling rate"].text())
                },
                "max_iterations": int(self.param_inputs["iterations"].text())
            }
            config_sa = {
                "metaheuristic": "simulated_annealing",
                "cost_function": "hamming" if self.cost_dropdown.currentText() == "hamming_distance" else "attractor",
                "mutation_function": "flip_bit" if "flip" in self.mut_dropdown.currentText() else "edame",
                "load_network_path": legacy_json_path,
                "network_name": real_name,
                "batch_output_dir": batch_output_dir,
                "log_interval": 9999,
                "live_update_interval": 9999,
                "generate_graphs": False,
                "is_batch": True,
                "log_results": True
            }
            config_sa.update(sa_params)
            experiments.append(("Simulated Annealing", num_runs, config_sa))
        except Exception:
            pass  # Dont add SA if form not filled

        if not experiments:
            self.output.append("❌ No valid experiment configurations found.")
            return

        total_runs = num_runs * len(experiments)
        self.progress.setMaximum(total_runs)

        # Launch worker
        self.thread = QThread()
        self.worker = ExperimentWorker(experiments)
        self.worker.moveToThread(self.thread)

        # Signal wiring
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.finished.connect(self._on_finished)
        self.thread.finished.connect(self.thread.deleteLater)

        self.worker.progress.connect(lambda _, msg: self.output.append(msg))
        self.worker.result.connect(self._on_run_success_multi)
        self.worker.failed.connect(self._on_run_failure_multi)

        self.thread.start()

    def add_to_queue(self):
        import tempfile

        selected_file = self.file_selector.currentText()
        path = os.path.join("saved_networks", selected_file)
        with open(path, "r") as f:
            data = json.load(f)

        if "truth_table" not in data:
            self.output.append("❌ Invalid network file (missing truth_table).")
            return

        flat_table = {k: v if isinstance(v, list) else list(v) for k, v in data["truth_table"].items()}
        real_name = os.path.splitext(selected_file)[0]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as temp_json:
            json.dump(flat_table, temp_json)
            legacy_json_path = temp_json.name

        method = self.meta_selector.currentText()
        try:
            if method == "Genetic Algorithm":
                params = {
                    "pop_size": int(self.param_inputs["population size"].text()),
                    "mutation_rate": float(self.param_inputs["mutation rate"].text()),
                    "crossover_rate": float(self.param_inputs["crossover rate"].text()),
                    "max_gens": int(self.param_inputs["generations"].text())
                }
            else:
                params = {
                    "temperature": {
                        "initial": float(self.param_inputs["initial temperature"].text()),
                        "cooling_rate": float(self.param_inputs["cooling rate"].text())
                    },
                    "max_iterations": int(self.param_inputs["iterations"].text())
                }
            num_runs = int(self.runs_input.text())
        except Exception as e:
            self.output.append(f"❌ Invalid input: {e}")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        batch_output_dir = os.path.join("experiment_results", real_name, f"batch_{timestamp}")
        os.makedirs(batch_output_dir, exist_ok=True)

        config = {
            "metaheuristic": "simulated_annealing" if method == "Simulated Annealing" else "genetic_algorithm",
            "cost_function": "hamming" if self.cost_dropdown.currentText() == "hamming_distance" else "attractor",
            "mutation_function": "flip_bit" if "flip" in self.mut_dropdown.currentText() else "edame",
            "load_network_path": legacy_json_path,
            "network_name": real_name,
            "batch_output_dir": batch_output_dir,
            "log_interval": 9999,
            "live_update_interval": 9999,
            "generate_graphs": False,
            "is_batch": True,
            "log_results": True
        }
        config.update(params)

        display_name = f"{method} ({self.cost_dropdown.currentText()})"
        self.experiment_queue.append((display_name, num_runs, config))
        self.queue_display.append(f"✅ Queued: {display_name} x{num_runs}")

    def run_experiment_queue(self):
        if not self.experiment_queue:
            self.output.append("⚠️ Queue is empty. Add experiments first.")
            return

        total_runs = sum(num for _, num, _ in self.experiment_queue)
        self.progress.setValue(0)
        self.progress.setMaximum(total_runs)

        self.thread = QThread()
        self.worker = ExperimentWorker(self.experiment_queue)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.finished.connect(self._on_finished)
        self.thread.finished.connect(self.thread.deleteLater)

        self.worker.progress.connect(lambda _, msg: self.output.append(msg))
        self.worker.result.connect(self._on_run_success_multi)
        self.worker.failed.connect(self._on_run_failure_multi)

        self.thread.start()
        self.output.append("🚀 Running all queued experiments...")

    def _on_run_success(self, run_num, final_cost, elapsed):
        self.progress.setValue(run_num)
        self.output.append(f"✅ Run {run_num} complete. Final Cost = {final_cost} | Time Taken = {elapsed:.2f} sec")

    def _on_run_failure(self, run_num, traceback_str):
        self.progress.setValue(run_num)
        self.output.append(f"❌ Run {run_num} failed with error:\n{traceback_str}")

    def _on_run_success_multi(self, exp_name, run_num, final_cost, elapsed):
        self.progress.setValue(self.progress.value() + 1)
        self.output.append(
            f"✅ [{exp_name}] Run {run_num} complete. Final Cost = {final_cost} | Time Taken = {elapsed:.2f} sec")

    def _on_run_failure_multi(self, exp_name, run_num, traceback_str):
        self.progress.setValue(self.progress.value() + 1)
        self.output.append(f"❌ [{exp_name}] Run {run_num} failed with error:\n{traceback_str}")

    def _on_finished(self):
        self.output.append("✅ All experiments complete.")
        generate_batch_plots(self.worker.config_dict["batch_output_dir"])


def collect_batch_data(batch_dir):
    costs, times, methods = [], [], []

    for root, _, files in os.walk(batch_dir):
        if "cost_log.csv" in files:
            exp_name = os.path.basename(os.path.dirname(root))
            cost_path = os.path.join(root, "cost_log.csv")
            df = pd.read_csv(cost_path)
            if not df.empty:
                final_cost = df["Cost"].iloc[-1]
                costs.append(final_cost)
                methods.append(exp_name)

        if "time_taken.txt" in files:
            with open(os.path.join(root, "time_taken.txt")) as f:
                try:
                    times.append(float(f.readline().split()[0]))
                except:
                    pass

    return costs, times, methods


def plot_cost_violin(costs, methods, out_dir):
    if not methods:
        return
    df = pd.DataFrame({"Cost": costs, "Method": methods})
    plt.figure()
    sns.violinplot(x="Method", y="Cost", data=df, inner="point")
    plt.title("Final Cost by Experiment")
    plt.xticks(rotation=30)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "plot_cost_violin.png"))
    plt.close()


def plot_average_progress(batch_dir):
    experiment_runs = {}

    for root, _, files in os.walk(batch_dir):
        if "cost_log.csv" in files:
            exp_name = os.path.basename(os.path.dirname(root))
            path = os.path.join(root, "cost_log.csv")
            df = pd.read_csv(path)
            if not df.empty:
                if exp_name not in experiment_runs:
                    experiment_runs[exp_name] = []
                experiment_runs[exp_name].append(df["Cost"].values)

    if not experiment_runs:
        return

    plt.figure(figsize=(10, 6))

    for exp_name, runs in experiment_runs.items():
        max_len = max(len(r) for r in runs)
        padded = np.full((len(runs), max_len), np.nan)
        for i, r in enumerate(runs):
            padded[i, :len(r)] = r

        mean_progress = np.nanmean(padded, axis=0)
        std_progress = np.nanstd(padded, axis=0)
        steps = np.arange(1, len(mean_progress) + 1)

        plt.plot(steps, mean_progress, label=exp_name)
        plt.fill_between(steps, mean_progress - std_progress, mean_progress + std_progress, alpha=0.2)

    plt.xlabel("Step (Iteration/Generation)")
    plt.ylabel("Average Cost")
    plt.title("Average Cost Progress by Experiment")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(batch_dir, "plot_average_progress.png"))
    plt.close()


def plot_final_cost_histogram(costs, out_dir):
    plt.figure()
    plt.hist(costs, bins=15, edgecolor='black')
    plt.title("Final Cost Distribution")
    plt.xlabel("Final Cost")
    plt.ylabel("Frequency")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "plot_cost_histogram.png"))
    plt.close()


def plot_runtime_boxplot(times, out_dir):
    if not times:
        return
    plt.figure()
    plt.boxplot(times, vert=True, patch_artist=True)
    plt.title("Runtime per Run")
    plt.ylabel("Time (seconds)")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "plot_runtime_boxplot.png"))
    plt.close()


def plot_success_rate(costs, out_dir, threshold=0.01):
    success = sum(c <= threshold for c in costs)
    fail = len(costs) - success
    plt.figure()
    plt.bar(["Success", "Fail"], [success, fail], color=["green", "red"])
    plt.title(f"Runs with Cost ≤ {threshold}")
    plt.ylabel("Count")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "plot_success_rate.png"))
    plt.close()


def save_batch_summary(costs, times, out_dir):
    summary = {
        "total_runs": int(len(costs)),
        "mean_cost": float(np.mean(costs)),
        "std_cost": float(np.std(costs)),
        "mean_runtime": float(np.mean(times)) if times else "N/A",
        "success_count": int(sum(c <= 0.01 for c in costs)),
        "fail_count": int(sum(c > 0.01 for c in costs))
    }

    with open(os.path.join(out_dir, "batch_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)


def generate_batch_plots(batch_dir):
    costs, times, methods = collect_batch_data(batch_dir)
    if not costs:
        return
    plot_final_cost_histogram(costs, batch_dir)
    plot_runtime_boxplot(times, batch_dir)
    plot_success_rate(costs, batch_dir)
    plot_cost_violin(costs, methods, batch_dir)
    save_batch_summary(costs, times, batch_dir)
    plot_average_progress(batch_dir)




