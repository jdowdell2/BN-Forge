import random


def one_point_crossover(parent1, parent2):
    # Ensure that parents have == number of rules (same length)
    if len(parent1.current_rules) != len(parent2.current_rules):
        raise ValueError("The parent networks must have the same number of rules.")

    # Choose a random point for crossover
    crossover_point = random.randint(1, len(parent1.current_rules) - 1)

    # Create offspring by combining the rules from both parents atcrossover point
    offspring_rules = parent1.current_rules[:crossover_point] + parent2.current_rules[crossover_point:]

    # Return offspring network
    child_network = type(parent1)(len(parent1.current_rules))
    child_network.current_rules = offspring_rules

    return child_network
