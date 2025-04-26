# src/inference_engine/cost_functions/attractor_difference.py
from collections import Counter

def attractor_difference_cost(target_attractors, observed_attractors, weight_missing=1.0, weight_extra=1.0):
    """
    Computes a cost based on mismatches in attractors between target and observed.
    Each attractor is a list of state strings.
    """

    def normalise(attractor):
        # Rotate to canonical form for cycle comparison (handles different starting points)
        return min([attractor[i:] + attractor[:i] for i in range(len(attractor))])

    # Normalise attractors to canonical form
    norm_target = [normalise(a) for a in target_attractors]
    norm_observed = [normalise(a) for a in observed_attractors]

    # Count occurrences
    count_target = Counter(tuple(a) for a in norm_target)
    count_observed = Counter(tuple(a) for a in norm_observed)

    # Calculate unmatched
    missing = count_target - count_observed
    extra = count_observed - count_target

    # Weighted cost: missing and extra attractors
    cost = weight_missing * sum(missing.values()) + weight_extra * sum(extra.values())
    return cost
