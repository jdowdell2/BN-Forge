#!/usr/bin/env python3
import os
import csv
import yaml
import matplotlib.pyplot as plt

results_dir = "results"
run_dirs = sorted([d for d in os.listdir(results_dir) if d.startswith("run_")])

cost_series = []
match_series = []
labels = []
summary_rows = []

for run in run_dirs:
    csv_path = os.path.join(results_dir, run, "metrics.csv")
    config_path = None
    for root, _, files in os.walk(""):
        for file in files:
            if file.endswith(".yaml") and run.split("_")[-1] in file:
                config_path = os.path.join(root, file)
                break

    if not os.path.exists(csv_path):
        continue

    iterations, costs, matched = [], [], []
    with open(csv_path, 'r') as f:
        next(f)
        for row in csv.reader(f):
            i, c, _, m = row
            iterations.append(int(i))
            costs.append(float(c))
            matched.append(int(m))

    max_iter = max(iterations)
    norm_iter = [i / max_iter for i in iterations]
    label = run
    try:
        if config_path and os.path.exists(config_path):
            with open(config_path) as cf:
                config = yaml.safe_load(cf)
                label = f"{run} | n={config.get('entity_count')} | {config.get('cost_function')} | {config.get('mutation_function')}"
    except:
        pass

    best_cost = min(costs)
    iter_to_best = iterations[costs.index(best_cost)]
    max_match = max(matched)

    summary_rows.append([run, best_cost, iter_to_best, max_match, len(matched)])

    cost_series.append((norm_iter, costs))
    match_series.append((norm_iter, matched))
    labels.append(label)

# Plot normalised cost comparison
plt.figure(figsize=(10, 5))
for (x, y), label in zip(cost_series, labels):
    plt.plot(x, y, label=label)
plt.xlabel("Normalised Iteration")
plt.ylabel("Cost")
plt.title("Cost Over Normalised Time")
plt.legend(fontsize='small')
plt.grid(True)
plt.tight_layout()
plt.savefig("results/comparison_cost_progress.png")
plt.close()

# Plot normalised attractor match comparison
plt.figure(figsize=(10, 5))
for (x, y), label in zip(match_series, labels):
    plt.plot(x, y, label=label)
plt.xlabel("Normalised Iteration")
plt.ylabel("Matched Attractors")
plt.title("Attractor Match Over Normalised Time")
plt.legend(fontsize='small')
plt.grid(True)
plt.tight_layout()
plt.savefig("results/comparison_attractor_matches.png")
plt.close()

# Write summary CSV
summary_path = os.path.join(results_dir, "summary_metrics.csv")
with open(summary_path, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["Run", "Best Cost", "Iteration to Best", "Max Attractors Matched", "Total Iterations"])
    writer.writerows(summary_rows)
