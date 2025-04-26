# experiments/run_experiment.py
import yaml
import math
import random
import os
from datetime import datetime
import json
import itertools
import time

from src.inference_engine.cost_functions.hamming_distance import calculate_hamming_distance
from src.inference_engine.cost_functions.attractor_difference import attractor_difference_cost
from src.inference_engine.mutation_strategies.flip_mutation import flip_bit
from src.inference_engine.mutation_strategies.edame_mutation import edame_mutation
from src.inference_engine.mutation_strategies.mutation_utils import replace_entities_with_state
from src.inference_engine.metaheuristics.genetic_algorithm import genetic_algorithm
from src.inference_engine.metaheuristics.simulated_annealing import simulated_annealing, TemperatureSchedule

from src.boolean_network_representation.network import BooleanNetwork
from src.boolean_network_representation import rules
from src.boolean_network_representation.rules import TruthTableToRules
from src.experiments.save_experiment_summary import save_experiment_summary


def log_attractors(network, label, log_dir):
    attractors = network.detect_attractors()
    filepath = os.path.join(log_dir, f"{label}_attractors.txt")
    with open(filepath, 'w') as f:
        for i, cycle in enumerate(attractors):
            f.write(f"Attractor {i+1}: {' -> '.join(cycle)}\n")


def main(config_path, progress_callback=None, show_full_plot=True):
    start_time = time.time()

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # 1. Load target truth table
    with open(config["load_network_path"], 'r') as jf:
        loaded_trace = json.load(jf)
        sample_key = next(iter(loaded_trace))
        entity_count = len(sample_key)
        entities = [f'N{i + 1}' for i in range(entity_count)]
        desired_trace = {k: v for k, v in loaded_trace.items()}

    desired_network = BooleanNetwork(entity_count, rule_source="manual")
    rules_dict = rules.TruthTableToRules.convert(desired_trace, entities)
    formatted_rules = {
        entity: replace_entities_with_state(rule, entities)
        for entity, rule in rules_dict.items()
    }
    desired_network.current_rules = [
        eval(f"lambda state, index: int({formatted_rules[entity]})") if formatted_rules[entity] != '0'
        else (lambda state, index: 0)
        for entity in entities
    ]

    # 2. Attractors (if needed)
    target_attractors = desired_network.detect_attractors()
    #edges for graph
    desired_attractor_edges = set()
    desired_attractor_edges = set()
    for cycle in target_attractors:
        for i in range(len(cycle)):
            src = str(cycle[i])  # <-- make sure it's string
            dst = str(cycle[(i + 1) % len(cycle)])
            desired_attractor_edges.add((src, dst))
    # print("[DEBUG] Desired Attractor Edges:", sorted(desired_attractor_edges))

    # Output dir

    # Base naming setup
    if config.get("is_batch"):
        # Create subfolder per run inside the batch directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        run_dir = os.path.join(config["batch_output_dir"], f"run_{timestamp}")
    else:
        # Create a unique folder for single run experiments - live_evolution
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        network_path = config.get("load_network_path", "")
        network_filename = os.path.basename(network_path)
        network_name = config.get("network_name") or os.path.splitext(network_filename)[0]
        base_dir = os.path.join("experiment_results", network_name)
        run_dir = os.path.join(base_dir, f"run_{timestamp}")


    graphs_dir = os.path.join(run_dir, "graphs")

    os.makedirs(graphs_dir, exist_ok=True)

    net = BooleanNetwork(entity_count, rule_source="manual")
    input_states = [''.join(bits) for bits in itertools.product('01', repeat=entity_count)]
    random_trace = {
        state: [random.randint(0, 1) for _ in range(entity_count)]
        for state in input_states
    }

    # Convert truth table to rule strings SOP form
    random_rules_dict = TruthTableToRules.convert(random_trace, entities)
    print("\n🔧 Initial Random Rules for Starting Network:")
    for entity in entities:
        print(f"  {entity}: {random_rules_dict[entity]}")


    # Set starting rules
    net.current_rules = [
        eval(f"lambda state, index: int({replace_entities_with_state(rule, entities)})")
        if rule != '0' else (lambda state, index: 0)
        for rule in random_rules_dict.values()
    ]

    def wrapped_edame_mutation(network, current_trace):
        return edame_mutation(network, current_trace, target_attractors)

    mutation_map = {
        'flip_bit': lambda net, trace: flip_bit(trace, entities),
        'edame': wrapped_edame_mutation,
    }

    cost_map = {
        'hamming': lambda desired, current: calculate_hamming_distance(desired, current),
        'attractor': lambda _, __: attractor_difference_cost(
            target_attractors,
            net.detect_attractors(),
            weight_missing=config.get('weight_missing', 1.0),
            weight_extra=config.get('weight_extra', 1.0)
        )
    }

    metaheuristic = config.get('metaheuristic', 'simulated_annealing')
    temperature_log = None

    if metaheuristic == 'simulated_annealing':
        temperature = TemperatureSchedule(
            initial_temp=config['temperature']['initial'],
            cooling_rate=config['temperature']['cooling_rate']
        )
        best_rules, best_cost, history, temperature_log, final_step = simulated_annealing(
            network=net,
            desired_trace=desired_trace,
            cost_function=cost_map[config['cost_function']],
            mutation_function=mutation_map[config['mutation_function']],
            acceptance_function=lambda delta, temp: (delta <= 0 or random.random() < math.exp(-delta / temp)),
            temperature_schedule=temperature,
            entities=entities,
            max_iterations=config['max_iterations'],
            log_interval=config.get('log_interval', 250),
            output_dir=run_dir,
            progress_callback=progress_callback,
            log_results = config.get("log_results", False),
        )

    elif metaheuristic == 'genetic_algorithm':
        best_rules, best_cost, history, final_step = genetic_algorithm(
            network_class=BooleanNetwork,
            desired_trace=desired_trace,
            cost_function=cost_map[config['cost_function']],
            mutation_function=mutation_map[config['mutation_function']],
            entities=entities,
            pop_size=config.get('pop_size', 50),
            max_gens=config.get('max_gens', 100),
            crossover_rate=config.get('crossover_rate', 0.7),
            mutation_rate=config.get('mutation_rate', 0.01),
            output_dir=run_dir,
            live_update_interval=config.get('live_update_interval', 2),
            progress_callback=progress_callback,
            log_results = config.get("log_results", False)
        )
    else:
        raise ValueError(f"Unknown metaheuristic '{metaheuristic}'")


    # Show full-resolution cost plot
    if progress_callback is None and show_full_plot:
        try:
            import matplotlib.pyplot as plt
            from src.gui.inference.cost_plot_window import CostPlotWindow

            full_steps = list(range(len(history)))  # _ is `history`
            full_window = CostPlotWindow(
                log_scale=config.get("log_y", False),
                method=metaheuristic.replace("_", " ").title()
            )
            for step, cost in enumerate(history):
                full_window.append(step, cost)

            full_window.show()


            input("🟢 Press Enter in console to close the full-resolution plot window...")
        except Exception as e:
            print("❗ Couldn't show final plot window:", e)

    # Create new final network and assign the best evolved rules
    final_net = BooleanNetwork(entity_count, rule_source="manual")
    final_net.current_rules = [
        rule if callable(rule)
        else eval(f"lambda state, index: int({replace_entities_with_state(rule, entities)})")
        if rule != '0' else (lambda state, index: 0)
        for rule in best_rules.values()
    ]

    generate_graphs = config.get("generate_graphs", True)
    if generate_graphs:

        # Generate final graphs and return
        desired_network.generate_state_graph(filename=os.path.join(graphs_dir, "state_graph_desired"))
        final_net.generate_state_graph(filename=os.path.join(graphs_dir, "state_graph_final"))
        desired_network.generate_wiring_diagram(filename=os.path.join(graphs_dir, "wiring_diagram_desired"))
        final_net.generate_wiring_diagram(filename=os.path.join(graphs_dir, "wiring_diagram_final"))

        log_attractors(final_net, "final", run_dir)
        log_attractors(desired_network, "desired", run_dir)

    # Format readable Quine-McCluskey BN strings
    final_rules_dict = TruthTableToRules.convert(
        final_net.generate_truth_table(),
        entities,
        minimise=True,
        readable=True
    )
    final_rules_readable = {
        entity: rule for entity, rule in final_rules_dict.items()
    }
    final_truth_table = final_net.generate_truth_table()

    desired_rules_dict = TruthTableToRules.convert(
        desired_trace,
        entities,
        minimise=True,
        readable=True
    )
    config["rules"] = desired_rules_dict
    if config.get("log_results", False):
        save_experiment_summary(
            run_dir=run_dir,
            config=config,
            best_rules=best_rules,
            best_cost=best_cost,
            cost_progress=history,
            time_taken=time.time() - start_time if "start_time" in locals() else 0,
            final_network=final_net,
            desired_trace=desired_trace,
            target_attractors=target_attractors,
            final_attractors=final_net.detect_attractors(),
            final_truth_table=final_truth_table,
            final_rules_readable=final_rules_readable,
            temperature_log = temperature_log

        )



    return history, final_net, time.time() - start_time, final_step

