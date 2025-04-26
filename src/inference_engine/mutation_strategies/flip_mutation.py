import random
import copy
from src.boolean_network_representation.rules import TruthTableToRules
from src.inference_engine.mutation_strategies.mutation_utils import replace_entities_with_state

def flip_bit(truth_table, entities):
    """
    Randomly flips a single bit in the truth table and returns the modified truth table
    and the corresponding new Boolean rules (as callables).
    """
    if not isinstance(truth_table, dict):
        raise ValueError("Expected a dictionary representing the truth table.")

    # Copy truth table to avoid mutating original
    mutated = copy.deepcopy(truth_table)

    # Randomly choose state and output bit to flip
    random_state = random.choice(list(mutated.keys()))
    bit_index = random.randint(0, len(mutated[random_state]) - 1)
    mutated[random_state][bit_index] = 1 - mutated[random_state][bit_index]

    new_rules_dict = TruthTableToRules.convert(mutated, entities)

    # Make the rules callable transform each rule to a lambda function
    new_rules = [
        eval(f"lambda state, index: int({replace_entities_with_state(rule, entities)})")
        if rule != '0' else (lambda state, index: 0)
        for rule in new_rules_dict.values()
    ]

    return mutated, new_rules  # Return mutated trace and callable rules
