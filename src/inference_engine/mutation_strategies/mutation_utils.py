def replace_entities_with_state(rule, entities):
    """
    Replaces entity names with state[i] references.
    """
    if rule is None or rule == "":
        return "0"
    rule = rule.replace("AND", "and").replace("OR", "or").replace("NOT", "not")
    for i, entity in enumerate(entities):
        rule = rule.replace(entity, f"state[{i}]")
    return rule
