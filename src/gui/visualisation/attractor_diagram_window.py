from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import networkx as nx

from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import networkx as nx

from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import networkx as nx

class AttractorDiagramWindow(QMainWindow):
    """
    Displays attractor diagram either over live evolution or static
    """
    def __init__(self, attractors, title="Attractor Diagram", step=None, method="Genetic Algorithm", parent=None):
        super().__init__(parent)
        label = "Generation" if "Genetic" in method else "Iteration"
        if step is not None:
            self.setWindowTitle(f"{title} ({label} {step})")
        else:
            self.setWindowTitle(title)
        self.resize(800, 600)

        self.attractors = attractors


        layout = QVBoxLayout()
        self.canvas = FigureCanvas(Figure(figsize=(6, 4)))
        layout.addWidget(self.canvas)
        self.ax = self.canvas.figure.subplots()

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.draw_graph()

    def draw_graph(self):
        self.ax.clear()
        masterG = nx.DiGraph()
        pos = {}

        cycles_per_row = 3
        x_spacing = 6.0
        y_spacing = 6.0
        circle_scale = 2.0

        for idx, cycle in enumerate(self.attractors):
            subG = nx.DiGraph()
            for i in range(len(cycle)):
                src = cycle[i]
                dst = cycle[(i + 1) % len(cycle)]
                subG.add_edge(src, dst)

            if len(subG.nodes) < 1:
                continue

            subpos = nx.circular_layout(subG, scale=circle_scale)
            row = idx // cycles_per_row
            col = idx % cycles_per_row
            offset_x = col * x_spacing
            offset_y = -row * y_spacing
            for node in subpos:
                subpos[node][0] += offset_x
                subpos[node][1] += offset_y

            masterG.add_nodes_from(subG.nodes())
            masterG.add_edges_from(subG.edges())
            pos.update(subpos)

        if len(masterG.nodes) == 0:
            self.ax.text(0.5, 0.5, "No Attractors Found",
                         ha='center', va='center', fontsize=14, color='red',
                         transform=self.ax.transAxes)
            self.canvas.draw()
            return

        arrow_params = dict(
            arrows=True,
            arrowsize=20,
            min_source_margin=15,
            min_target_margin=15
        )

        nx.draw_networkx_nodes(masterG, pos, ax=self.ax, node_color='lightgray', node_size=1400)
        nx.draw_networkx_labels(masterG, pos, ax=self.ax, font_size=10)
        nx.draw_networkx_edges(masterG, pos, ax=self.ax, edgelist=masterG.edges(),
                               edge_color='black', connectionstyle='arc3,rad=0.1', width=2, **arrow_params)

        self.ax.set_title("Boolean Network Attractors (Separated by Offsets)")
        self.ax.axis("off")
        self.canvas.draw()

    def update_data(self, new_attractors):
        self.attractors = new_attractors
        self.draw_graph()
