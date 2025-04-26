import random
from src.boolean_network_representation.rules import TruthTableToRules
from src.inference_engine.mutation_strategies.mutation_utils import replace_entities_with_state


def edame_mutation(network, current_trace, target_attractors):
    """
    EDAME-inspired mutation
    - Detects attractors in current network
    - Compares to target attractors
    - Chooses entity likely responsible for mismatch
    - Mutates only that entity's next-state rule in the truth table

    Adapted from:
    EDAME (Efficient Directed Acyclic Mutation Engine)
    https://github.com/Jojo6297/edame

    Original concept by Jojo6297 et al. (2022).
    Modifications have been made for integration with this project.

    """
    current_attractors = network.detect_attractors()

    # set attractors to state sets
    target_states = set(s for cycle in target_attractors for s in cycle)
    current_states = set(s for cycle in current_attractors for s in cycle)

    # Find states present in target but not current - and vice versa
    missing_states = list(target_states - current_states)
    extra_states = list(current_states - target_states)

    # identify entities that differ in mismatched states
    differing_nodes = set()
    for state in missing_states + extra_states:
        if state in current_trace:
            current = current_trace[state]
            desired = list(map(int, list(state)))  # target state itself is desired next state
            for i in range(len(current)):
                if int(current[i]) != desired[i]:
                    differing_nodes.add(i)

    # If no mismatched states found, fallback to random node
    if not differing_nodes:
        differing_nodes = {random.randint(0, network.entity_count - 1)}

    # Choose one node from differing ones to mutate
    target_node = random.choice(list(differing_nodes))

    # Choose a random input state to flip entity output
    mutated_trace = current_trace.copy()
    state_keys = list(mutated_trace.keys())
    state_to_flip = random.choice(state_keys)

    # Flip random state entity output 0
    new_next_state = mutated_trace[state_to_flip][:]
    new_next_state[target_node] ^= 1
    mutated_trace[state_to_flip] = new_next_state

    # Regenerate rules
    mutated_rules_dict = TruthTableToRules.convert(mutated_trace, network.nodes)
    mutated_rules = [
        eval(f"lambda state, index: int({replace_entities_with_state(rule, network.nodes)})")
        if rule != '0' else (lambda state, index: 0)
        for rule in mutated_rules_dict.values()
    ]

    return mutated_trace, mutated_rules