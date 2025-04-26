import itertools

def generate_truth_table(entities, rules, format_rule_for_python):


    entity_count = len(entities)
    states = list(itertools.product([0, 1], repeat=entity_count))
    truth_table = {}

    for state in states:
        inputs = {entities[i]: state[i] for i in range(entity_count)}
        next_state = []

        for entity in entities:
            rule_expr = rules[entity]

            # Apply formatting before evaluation
            rule_expr = format_rule_for_python(rule_expr)

            try:
                next_state_value = eval(rule_expr, {}, inputs)
                next_state.append(int(next_state_value))
            except Exception as e:
                print(f"Error evaluating rule for {entity}: {e} | Rule: {rule_expr}")
                next_state.append(0)

        truth_table["".join(map(str, state))] = next_state

    return truth_table
