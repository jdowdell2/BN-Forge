# experiments/logging.py
import os
import json

def log_attractors(network, label, log_dir):
    """
    Logs attractors to text file.
    """
    attractors = network.detect_attractors()
    filepath = os.path.join(log_dir, f"{label}_attractors.txt")
    with open(filepath, 'w') as f:
        for i, cycle in enumerate(attractors):
            f.write(f"Attractor {i+1}: {' -> '.join(cycle)}\n")


def log_experiment_results(config, best_cost, best_rules, output_dir):
    """
    Logs the experiment configuration and results to a JSON file.
    """
    # Convert the best_rules to strings so they can be serialized
    serializable_best_rules = {
        name: str(rule) if callable(rule) else rule
        for name, rule in best_rules.items()
    }

    results = {
        'config': config,
        'best_cost': best_cost,
        'best_rules': serializable_best_rules
    }

    # Save results to a JSON file
    log_filename = f"experiment_results_{config['entity_count']}_entities.json"
    with open(f"{output_dir}/{log_filename}", 'w') as f:
        json.dump(results, f, indent=4)