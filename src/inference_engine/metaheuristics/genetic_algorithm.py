
import random
import os
import matplotlib.pyplot as plt
import json
from tempfile import gettempdir
from src.inference_engine.crossover_strategies.one_point_crossover import one_point_crossover


def write_live_json(step, rules, fitness, attractors=None):
    if attractors is None:
        attractors = []
    output = {
        "step": step,
        "rules": {f"N{i + 1}": str(rules[i]) for i in range(len(rules))},
        "fitness": fitness,
        "attractors": attractors
    }
    path = os.path.join(gettempdir(), "current_evolution.json")
    with open(path, "w") as f:
        json.dump(output, f)

def genetic_algorithm(
    network_class,
    desired_trace,
    pop_size,
    max_gens,
    crossover_rate,
    mutation_rate,
    entities,
    cost_function,
    mutation_function,
    output_dir="results",
    live_update_interval=2,
    cost_window=None,
    progress_callback=None,
    log_results=False
):
    population = [network_class(len(entities)) for _ in range(pop_size)]
    best_network = None
    best_cost = float('inf')
    cost_progress = []

    run_dir = output_dir
    os.makedirs(run_dir, exist_ok=True)

    #timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    #run_dir = os.path.join(output_dir, f"run_{timestamp}")
    #os.makedirs(run_dir, exist_ok=True)

    def evaluate_population(population):
        return [
            cost_function(desired_trace, net.generate_truth_table())
            for net in population
        ]

    for gen in range(max_gens):
        costs = evaluate_population(population)
        cost_progress.append(min(costs))

        current_best = min(population, key=lambda net: cost_function(desired_trace, net.generate_truth_table()))
        current_fitness = cost_function(desired_trace, current_best.generate_truth_table())

        # ✅ Always emit progress
        if progress_callback and (gen % live_update_interval == 0):
            progress_callback(gen, current_fitness, current_best)

        sorted_population = [x for _, x in sorted(zip(costs, population), key=lambda pair: pair[0])]
        selected_parents = sorted_population[:pop_size // 2]

        next_generation = []
        while len(next_generation) < pop_size:
            parent1, parent2 = random.sample(selected_parents, 2)
            child = one_point_crossover(parent1, parent2) if random.random() < crossover_rate else parent1
            if random.random() < mutation_rate:
                truth_table = child.generate_truth_table()
                _, mutated_rules = mutation_function(child, truth_table)
                child.current_rules = mutated_rules
            next_generation.append(child)

        population = next_generation
        best_network = min(population, key=lambda net: cost_function(desired_trace, net.generate_truth_table()))
        best_cost = cost_function(desired_trace, best_network.generate_truth_table())

        if gen % live_update_interval == 0:
            print(f"Generation {gen}: Best Cost = {best_cost}")
            _plot_progress(cost_progress, gen, run_dir)

        # ✅ Early stopping condition
        if best_cost == 0:
            print(f"✅ Early stopping at generation {gen} — cost reached 0.")
            break


    if log_results:
        _plot_progress(cost_progress, max_gens, run_dir)
    # ✅ Delete all other progress plots except the final one
    final_plot = f"progress_{len(cost_progress) - 1}.png"
    for fname in os.listdir(run_dir):
        if fname.startswith("progress_") and fname.endswith(".png") and fname != final_plot:
            try:
                os.remove(os.path.join(run_dir, fname))
            except Exception as e:
                print(f"⚠️ Could not delete {fname}: {e}")

    best_rules_named = {entities[i]: rule for i, rule in enumerate(best_network.current_rules)}
    final_step = len(cost_progress) - 1
    return best_rules_named, best_cost, cost_progress, final_step

def _plot_progress(costs, step, out_dir):
    plt.figure(figsize=(10, 5))
    plt.plot(costs)
    plt.yscale('linear')
    plt.xlabel("Generation")
    plt.ylabel("Cost")
    plt.title(f"Genetic Algorithm Progress @ Generation {step}")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, f"progress_{step}.png"))
    plt.close()

