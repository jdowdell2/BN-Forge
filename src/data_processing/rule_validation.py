import re

def validate_rule(rule_expression, entity_names):
    """
    Validates a rule expression to ensure it can be safely evaluated.
    Validation Rules:
------------------
1. Empty Rule Check:
    - The rule cannot be empty or consist only of whitespace.
    - Example (Invalid): ""
    - Example (Valid): "A AND B"

2. Valid Operators Check:
    - The rule must use only allowed logical operators: AND, OR, NOT, XOR.
    - These operators are converted to Python-compatible versions: "and", "or", "not", "^".
    - Example (Invalid): "A AN B" (Typo in 'AND')
    - Example (Valid): "A AND B"

3. Valid Entities Check:
    - Entities must be part of the defined network and should be case-sensitive.
    - Example (Invalid): "a AND B" (assuming network has 'A', 'B', 'C')
    - Example (Valid): "A AND B"

4. Unbalanced Parentheses Check:
    - The rule must contain balanced parentheses.
    - Example (Invalid): "A AND (B OR C" (Missing closing parenthesis)
    - Example (Valid): "(A AND B) OR C"

5. Consecutive Operators Check:
    - Operators should not be placed consecutively without an operand in between.
    - Example (Invalid): "A AND OR B"
    - Example (Valid): "A AND (B OR C)"

6. Empty Parentheses Check:
    - No expression should contain empty parentheses.
    - Example (Invalid): "A AND ()"
    - Example (Valid): "A AND (B OR C)"

7. Dangling Operators Check:
    - The expression cannot end with an operator.
    - Example (Invalid): "A AND B OR"
    - Example (Valid): "A AND B OR C"

8. Operand Placement Check:
    - Two entities cannot be placed next to each other without an operator.
    - Example (Invalid): "A B C"
    - Example (Valid): "A AND B AND C"

    Args:
        rule_expression (str): The formatted rule expression to validate.
        entity_names (list): List of valid entity names (e.g., ["A", "B", "C"]).

    Returns:
        bool, str: True if valid, otherwise False and an error message.
    """
    # 1. Empty Rules check
    if not rule_expression or not isinstance(rule_expression, str) or rule_expression.strip() == "":
        return False, "Rule is empty."

    # 2. Valid Operators Check:
    valid_operators = {"and", "or", "not", "xor", "^", "(", ")"}
    valid_operators_case_insensitive = {op.upper() for op in valid_operators}.union(valid_operators)
    valid_tokens = set(entity_names).union(valid_operators_case_insensitive)

    tokens = re.findall(r'\w+|[()^]', rule_expression)

    # 3. Valid Entities Check:
    for token in tokens:
        if token not in valid_tokens:
            return False, f"Invalid token detected: '{token}'"

    # 4. Unbalanced Parentheses Check:
    if rule_expression.count("(") != rule_expression.count(")"):
        return False, "Unbalanced parentheses detected."

    # 5 Consecutive Operators Check:
    upper_tokens = [t.upper() for t in tokens]
    prev_token = None
    for token in upper_tokens:
        if token in {"AND", "OR", "XOR"} and prev_token in {"AND", "OR", "NOT", "XOR"}:
            return False, f"Invalid sequence of operators and operands: '{prev_token} {token}'"
        prev_token = token

    # 6. Empty parenthesis chck
    if re.search(r'\(\s*\)', rule_expression):
        return False, "Empty parentheses detected."

    # 7. Dangling operators Check:
    if re.search(r'(AND|OR|NOT|XOR|and|or|not|xor|\^)\s*$', rule_expression):
        return False, "Expression ends with an incomplete operator."

    # 8. Operand Placement Check: no two entities in a row
    prev_token = None
    for token in tokens:
        if token in entity_names and prev_token in entity_names:
            return False, "Operands placed next to each other without an operator."
        prev_token = token

    for i in range(len(tokens) - 2):
        if (
                tokens[i] in entity_names and
                tokens[i + 1].upper() == "NOT" and
                tokens[i + 2] in entity_names
        ):
            return False, "Operands placed next to each other without an operator (e.g., 'A NOT B')."


    return True, "Valid rule."