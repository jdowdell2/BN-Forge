from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import networkx as nx

class WiringDiagramWindow(QMainWindow):
    def __init__(self, current_graph, target_graph, display_names=None):
        super().__init__()
        self.pos = None  # Store layout positions to reuse
        self.setWindowTitle("Wiring Diagram Comparison")
        self.resize(800, 600)
        self.display_names = display_names or {}

        layout = QVBoxLayout()
        self.canvas = FigureCanvas(Figure(figsize=(6, 4)))
        layout.addWidget(self.canvas)
        self.ax = self.canvas.figure.subplots()

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.draw_graph(current_graph, target_graph)

    def draw_graph(self, current_graph, target_graph):
        self.ax.clear()
        if not hasattr(self, "pos") or self.pos is None or set(self.pos.keys()) != set(current_graph.nodes):
            self.pos = nx.spring_layout(current_graph, seed=42)
        pos = self.pos

        # No zorder here
        nx.draw_networkx_nodes(current_graph, pos, ax=self.ax, node_color="lightgray", node_size=1000)

        labels = {n: self.display_names.get(n, n) for n in current_graph.nodes}
        nx.draw_networkx_labels(current_graph, pos, labels=labels, ax=self.ax)

        current_edges = set(current_graph.edges())
        target_edges = set(target_graph.edges())

        correct = current_edges & target_edges
        extra = current_edges - target_edges
        missing = target_edges - current_edges

        arrow_params = dict(
            arrows=True,
            arrowsize=20,
            min_source_margin=15,
            min_target_margin=15
        )

        def separate_self_loops(edges):
            return [e for e in edges if e[0] == e[1]], [e for e in edges if e[0] != e[1]]

        correct_loops, correct_edges = separate_self_loops(correct)
        extra_loops, extra_edges = separate_self_loops(extra)
        missing_loops, missing_edges = separate_self_loops(missing)

        # Regular edges
        nx.draw_networkx_edges(current_graph, pos, edgelist=correct_edges, edge_color="green",
                               connectionstyle='arc3,rad=0.1', ax=self.ax, width=2, **arrow_params)
        nx.draw_networkx_edges(current_graph, pos, edgelist=extra_edges, edge_color="blue",
                               connectionstyle='arc3,rad=0.1', ax=self.ax, width=2, **arrow_params)
        nx.draw_networkx_edges(target_graph, pos, edgelist=missing_edges, edge_color="red", style="dashed",
                               connectionstyle='arc3,rad=0.1', ax=self.ax, width=2, **arrow_params)

        # Self-loops
        nx.draw_networkx_edges(current_graph, pos, edgelist=correct_loops, edge_color="green",
                               connectionstyle='arc3,rad=0.5', ax=self.ax, width=2, **arrow_params)
        nx.draw_networkx_edges(current_graph, pos, edgelist=extra_loops, edge_color="blue",
                               connectionstyle='arc3,rad=0.6', ax=self.ax, width=2, **arrow_params)
        nx.draw_networkx_edges(target_graph, pos, edgelist=missing_loops, edge_color="red", style="dashed",
                               connectionstyle='arc3,rad=0.6', ax=self.ax, width=2, **arrow_params)

        self.ax.set_title("Wiring Diagram (Green = correct, Red = missing, Blue = extra)")
        self.ax.axis("off")
        self.canvas.draw()
        print("GRAPH UPDATED")
