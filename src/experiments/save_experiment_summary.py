import os
import json
import csv
import string
from datetime import datetime


def save_experiment_summary(
        run_dir,
        config,
        best_rules,
        best_cost,
        cost_progress,
        time_taken,
        final_network,
        desired_trace,
        target_attractors,
        final_attractors,
        final_truth_table,
        final_rules_readable,
        temperature_log=None
):
    os.makedirs(run_dir, exist_ok=True)

    # 1. Time taken
    with open(os.path.join(run_dir, "time_taken.txt"), "w") as f:
        f.write(f"{time_taken:.2f} seconds\n")

    # 2. Cost log
    cost_log_path = os.path.join(run_dir, "cost_log.csv")
    with open(cost_log_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)

        headers = ["Step", "Cost"]
        if temperature_log:
            headers.append("Temperature")
        writer.writerow(headers)

        for step, cost in enumerate(cost_progress):
            row = [step, cost]
            if temperature_log:
                row.append(temperature_log[step] if step < len(temperature_log) else "")
            writer.writerow(row)

    # 3. Parameters summary (dump config YAML to .txt)
    with open(os.path.join(run_dir, "parameters_summary.txt"), "w") as f:
        json.dump(config, f, indent=2)

    #rename from Nx to alphabetical form
    original_names = list(best_rules.keys())  # ['N1', 'N2', ...]
    renamed = {orig: new for orig, new in zip(original_names, string.ascii_uppercase)}

    # 4. Rule comparison (diff style)
    diff_lines = []
    for old_key in best_rules:
        new_key = renamed[old_key]
        desired_raw = config.get("rules", {}).get(old_key, "N/A")
        inferred_raw = final_rules_readable.get(old_key, "N/A")

        # Replace variable names in expressions
        for orig, new in renamed.items():
            desired_raw = desired_raw.replace(orig, new)
            inferred_raw = inferred_raw.replace(orig, new)

        diff_lines.append(f"{new_key}': desired = {desired_raw:<35} → inferred = {inferred_raw}")

    diff_path = os.path.join(run_dir, "rule_differences.txt")
    with open(diff_path, "w", encoding="utf-8") as f:
        f.write("\n".join(diff_lines))

    # 5. Final rules and truth table combined JSON
    original_names = list(best_rules.keys())  # ['N1', 'N2', ...]
    renamed = {orig: new for orig, new in zip(original_names, string.ascii_uppercase)}

    # 6. Update rules with renamed keys
    renamed_rules = {}
    for old_key, rule in final_rules_readable.items():
        new_key = renamed[old_key]
        for orig, new in renamed.items():
            rule = rule.replace(orig, new)
        renamed_rules[new_key] = rule

    # 7. Save final data
    final_data = {
        "entities": list(renamed.values()),
        "rules": renamed_rules,
        "truth_table": final_truth_table
    }

    with open(os.path.join(run_dir, "final_network.json"), "w") as f:
        json.dump(final_data, f, indent=2)

    # Attractor comparison
    def format_attractors(attractors):
        return [" → ".join(cycle) for cycle in attractors]

        with open(os.path.join(run_dir, "attractors_final.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(format_attractors(final_attractors)))

        with open(os.path.join(run_dir, "attractors_target.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(format_attractors(target_attractors)))
