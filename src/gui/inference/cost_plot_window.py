import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget

class CostPlotWindow(QMainWindow):
    def __init__(self, log_scale=False, method="Genetic Algorithm"):
        super().__init__()
        self.setWindowTitle("Cost Plot")
        self.resize(700, 400)

        self.canvas = FigureCanvas(plt.Figure())
        self.ax = self.canvas.figure.add_subplot(111)

        central_widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.log_scale = log_scale
        self.method = method  # store for later use

        self.steps = []
        self.costs = []

    def append(self, step, cost):
        self.steps.append(step)
        self.costs.append(cost)
        self.update_plot()

    def update_plot(self):
        self.ax.clear()
        self.ax.plot(self.steps, self.costs)

        self.ax.set_yscale('log' if self.log_scale else 'linear')
        self.ax.set_ylabel("Cost")
        self.ax.grid(True)

        if self.method == "Simulated Annealing":
            self.ax.set_xlabel("Mutation Attempt")
            self.ax.set_title(f"Simulated Annealing Cost Progress @ Iteration {self.steps[-1]}")
        else:
            self.ax.set_xlabel("Generation")
            self.ax.set_title(f"Genetic Algorithm Cost Progress @ Generation {self.steps[-1]} (Generation Interval)")

        self.canvas.draw()

    def set_history(self, steps, costs):
        self.steps = steps
        self.costs = costs
        self.update_plot()

