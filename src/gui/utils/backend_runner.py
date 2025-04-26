from PySide6.QtCore import QObject, Signal
from src.experiments.run_experiment import main as run_backend
import yaml

class BackendRunner(QObject):
    finished = Signal()
    progress = Signal(int, float)
    done_with_history = Signal(list, str, bool)
    wiring_update = Signal(object)
    attractors_update = Signal(list)

    def __init__(self, config_path, show_full_plot=False, log_scale=False, method="Genetic Algorithm"):
        super().__init__()
        self.config_path = config_path
        self.show_full_plot = show_full_plot
        self.log_scale = log_scale
        self.method = method
        self.latest_network = None
        self.log_interval = 1  # default fallback

        # Load log_interval from config
        try:
            with open(self.config_path, "r") as f:
                config_data = yaml.safe_load(f)
                self.log_interval = config_data.get("log_interval", 1)
        except Exception as e:
            print("⚠️ Could not read log_interval from config, using default 1:", e)

    def run(self):
        history, final_network, _, final_step = run_backend(
            self.config_path,
            progress_callback=self._handle_progress,
            show_full_plot=self.show_full_plot,
        )

        self.latest_network = final_network

        if self.show_full_plot:
            self.done_with_history.emit(history, self.method, self.log_scale)
        # Emit final wiring and attractor updates if available
        if self.latest_network:
            try:
                deps = self.latest_network.infer_wiring()
                graph = self.latest_network.build_wiring_graph(deps)
                self.wiring_update.emit(graph)

                attractors = self.latest_network.detect_attractors()
                self.attractors_update.emit((final_step, attractors))  # use large step to avoid duplication
            except Exception as e:
                print(f"Could not emit final wiring/attractors: {e}")


    def _handle_progress(self, step, cost, evolving_network=None):
        self.progress.emit(step, cost)
        self.latest_network = evolving_network

        if evolving_network is None:
            return

        if step % self.log_interval == 0:
            deps = evolving_network.infer_wiring()
            graph = evolving_network.build_wiring_graph(deps)
            self.wiring_update.emit(graph)

            attractors = evolving_network.detect_attractors()
            self.attractors_update.emit((step, attractors))

    def get_current_rules(self):
        return self.latest_network.current_rules if self.latest_network else None
