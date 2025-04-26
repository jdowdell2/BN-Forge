import matplotlib.pyplot as plt
import os

def plot_progress(costs, output_dir, config):
    """
    Plots the cost progression
    """
    plt.figure(figsize=(10, 5))
    plt.plot(costs)
    plt.yscale('linear')
    plt.xlabel("Mutation Attempt")
    plt.ylabel("Cost")

    # Add experiment metadata to the plot legend
    legend_label = f"Entities: {config['entity_count']} | " \
                   f"Mutation: {config['mutation_function']} | " \
                   f"Cost Function: {config['cost_function']} | " \
                   f"Max Iterations: {config['max_iterations']}"

    plt.title("Simulated Annealing Progress")
    plt.grid(True)
    plt.legend([legend_label], loc="upper right")
    plt.tight_layout()

    plot_filename = os.path.join(output_dir, "progress_plot.png")
    plt.savefig(plot_filename)
    plt.close()


def plot_experiment_results(cost_progress, config, output_dir):
    """
    Plots the results of the experiment with metadata in the legend.

    Args:
        cost_progress (list): List of cost values over iterations.
        config (dict): Experiment configuration (e.g., mutation strategy, entity count).
        output_dir (str): Directory to save the plot.
    """
    legend_label = f"Entities: {config['entity_count']}, Mutation: {config['mutation_function']}, Cost: {config['cost_function']}"

    plt.plot(cost_progress)
    plt.xlabel('Iterations')
    plt.ylabel('Cost')
    plt.title('Simulated Annealing Progress')
    plt.legend([legend_label])
    plt.grid(True)

    plot_filename = f"cost_progress_{config['entity_count']}_entities.png"
    plt.savefig(f"{output_dir}/{plot_filename}")
    plt.close()
