from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import networkx as nx

class StateGraphWindow(QMainWindow):
    """
    A window that displays the state-transition graph of a Boolean Network,
    highlighting the attractors (cycles) in a different color.
    """
    def __init__(self, transitions, attractors, title="State Graph", parent=None):
        """
        Args:
            transitions: dict of {state_str: next_state_str}
            attractors: list of attractor cycles, each cycle is a list of states
            title: Window title
            parent: Optional parent widget
        """
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(800, 600)

        # Store data for later re-draw
        self.transitions = transitions
        self.attractors = attractors

        # Set up the Matplotlib canvas
        layout = QVBoxLayout()
        self.canvas = FigureCanvas(Figure(figsize=(6, 4)))
        layout.addWidget(self.canvas)
        self.ax = self.canvas.figure.subplots()

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Initial draw
        self.draw_graph()

    def draw_graph(self):
        """Builds a directed graph from self.transitions, highlights attractors, and draws it."""
        self.ax.clear()

        # 1. Build NetworkX DiGraph
        G = nx.DiGraph()
        for state, next_state in self.transitions.items():
            G.add_node(state)
            G.add_node(next_state)
            G.add_edge(state, next_state)

        # 2. Identify attractor nodes/edges
        # Flatten all states in attractors into one set for easy highlight
        attractor_nodes = set()
        attractor_edges = set()
        for cycle in self.attractors:
            # cycle might be something like ["0111", "1111"] for a 2-cycle
            attractor_nodes.update(cycle)
            # edges: cycle[i] -> cycle[i+1], plus wrap the last to first
            for i in range(len(cycle)):
                src = cycle[i]
                dst = cycle[(i + 1) % len(cycle)]
                attractor_edges.add((src, dst))

        # 3. Layout
        # We'll keep a consistent layout by sorting states, or you can use spring_layout
        # for a more dynamic display. For large networks, spring_layout might look better.
        pos = nx.spring_layout(G, seed=42)

        # 4. Draw nodes
        #    - attractor nodes in one color, non-attractor in another
        node_colors = []
        for node in G.nodes():
            if node in attractor_nodes:
                node_colors.append("orange")  # highlight
            else:
                node_colors.append("lightgray")

        nx.draw_networkx_nodes(G, pos, node_size=1200, ax=self.ax, node_color=node_colors)
        nx.draw_networkx_labels(G, pos, ax=self.ax, font_size=10)

        # 5. Draw edges
        #    - attractor edges in thick red, others in black
        normal_edges = []
        for e in G.edges():
            if e in attractor_edges:
                continue
            normal_edges.append(e)

        nx.draw_networkx_edges(G, pos, edgelist=normal_edges, ax=self.ax,
                               edge_color="black", arrows=True, connectionstyle='arc3,rad=0.1')

        # highlight attractor edges
        nx.draw_networkx_edges(G, pos, edgelist=list(attractor_edges), ax=self.ax,
                               edge_color="red", width=2.5, arrows=True,
                               connectionstyle='arc3,rad=0.2')

        self.ax.set_title("Boolean Network State Graph\n(Attractors in Red)")
        self.ax.axis("off")

        self.canvas.draw()

    def update_data(self, transitions, attractors):
        """
        If you want to refresh the window with new transitions or attractors
        (e.g. in a progress callback), call this method.
        """
        self.transitions = transitions
        self.attractors = attractors
        self.draw_graph()
