
import os
import matplotlib.pyplot as plt
import json
from tempfile import gettempdir

from src.boolean_network_representation.network import BooleanNetwork
from src.inference_engine.mutation_strategies.mutation_utils import replace_entities_with_state
from src.boolean_network_representation.rules import TruthTableToRules


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

class TemperatureSchedule:
    def __init__(self, initial_temp, cooling_rate):
        self.initial_temp = initial_temp
        self.cooling_rate = cooling_rate

    def cool(self, temp):
        return temp * self.cooling_rate

def simulated_annealing(
    network,
    desired_trace,
    cost_function,
    mutation_function,
    acceptance_function,
    temperature_schedule,
    entities,
    max_iterations=1000000,
    log_interval=1000,
    live_update_interval=1000,
    output_dir="results",
    cost_window=None,
    progress_callback=None,
    log_results=False,

):
    initial_trace = network.generate_truth_table()
    entities = [f"N{i + 1}" for i in range(len(initial_trace[next(iter(initial_trace))]))]
    rules_dict = TruthTableToRules.convert(initial_trace, entities)

    print("✅ [DEBUG] Rebuilding SA rules with entity-safe lambdas...")  # <--- this line

    network.current_rules = [
        eval(f"lambda state, index: int({replace_entities_with_state(rule, entities)})")
        if rule != '0' else (lambda state, index: 0)
        for rule in rules_dict.values()
    ]

    current_trace = network.generate_truth_table()
    current_cost = cost_function(desired_trace, current_trace)
    best_cost = current_cost
    best_trace = current_trace.copy()
    best_rules = network.current_rules.copy()

    temperature = temperature_schedule.initial_temp
    iteration = 0
    cost_progress = [current_cost]
    temperatures = [temperature] # logging

    run_dir = output_dir
    os.makedirs(run_dir, exist_ok=True)

    while iteration < max_iterations:
        mutated_trace, mutated_rules = mutation_function(network, current_trace)
        new_cost = cost_function(desired_trace, mutated_trace)
        delta_cost = new_cost - current_cost

        if acceptance_function(delta_cost, temperature):
            current_trace = mutated_trace
            current_cost = new_cost
            network.current_rules = mutated_rules

            if current_cost < best_cost:
                best_cost = current_cost
                best_trace = mutated_trace.copy()
                best_rules = mutated_rules.copy()
                best_network = BooleanNetwork(len(entities))

        cost_progress.append(current_cost)
        temperature = temperature_schedule.cool(temperature)
        temperatures.append(temperature)

        if iteration % log_interval == 0:
            print(f"Iter {iteration}: Cost = {current_cost:.4f}, Temp = {temperature:.4f}")

        if best_cost == 0:
            break


        iteration += 1
        # Sends current iteration cost - meanwhile ga sends best in the generation not ever
        if progress_callback and (iteration % live_update_interval == 0):
            print(f"[DEBUG] Emitting progress at {iteration}")
            progress_callback(iteration, current_cost, network)
    if log_results:
        _plot_progress(cost_progress, iteration, run_dir)
    best_rules_named = {entities[i]: rule for i, rule in enumerate(best_rules)}
    best_network = BooleanNetwork(len(entities))
    best_network.current_rules = best_rules
    final_step = len(cost_progress) - 1
    return best_rules_named, best_cost, cost_progress, temperatures, final_step

def _plot_progress(costs, step, out_dir):
    plt.figure(figsize=(10, 5))
    plt.plot(costs)
    plt.yscale('linear')
    plt.xlabel("Mutation Attempt")
    plt.ylabel("Cost")
    plt.title(f"Simulated Annealing Progress @ Step {step}")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, f"progress_{step}.png"))
    plt.close()



