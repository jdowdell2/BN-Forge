import re
import random
from sympy.logic.boolalg import SOPform
from sympy.abc import A, B, C, D, E, F, G, H, I, J  # max 10
from sympy import simplify_logic
from sympy import symbols, simplify_logic

class RuleLoader:
    def __init__(self, entity_count):
        """
        Class for rule management.
        """
        self.entity_count = entity_count
        self.rules = [None] * self.entity_count  # Initialise empty rules list

    def load_rules(self, rule_source="gui"):
        """
        Loads rules from a specified source.
        """
        if rule_source == "gui":
            return self.load_from_gui()
        elif rule_source == "manual":
            return self.rules
        else:
            raise ValueError("Unsupported rule source")

    def set_rule(self, entity_index, rule_function):
        if not (0 <= entity_index < self.entity_count):
            raise IndexError("Entity index out of range")

        self.rules[entity_index] = rule_function

    def load_from_gui(self):
        print("Not implemented")
        return self.rules

    def clear_rules(self):
        self.rules = [None] * self.entity_count

    @staticmethod
    def parse_rule_dict(rule_dict):
        def convert_entity_names(expr, node_list):
            # Replace variable names like A, B with state[0], state[1], etc.
            for i, name in enumerate(node_list):
                expr = re.sub(rf"\b{name}\b", f"state[{i}]", expr)
            return expr

        parsed = []
        node_list = list(rule_dict.keys())  # e.g., ["A", "B", "C", "D", "E"]
        for node, expr in rule_dict.items():
            if expr.strip() == "0":
                parsed.append(lambda state, index: 0)
            else:
                expr_clean = RuleLoader.format_rule_for_python(expr)
                expr_ready = convert_entity_names(expr_clean, node_list)
                parsed.append(eval(f"lambda state, index: int({expr_ready})"))
        return parsed


    @staticmethod
    @staticmethod
    @staticmethod
    def format_rule_for_python(rule_expression):
        """
        Converts GUI-style Boolean expressions into Python-compatible eval expressions.
        Ensures 'A XOR NOT B' becomes 'A ^ (not B)'.
        """
        if not isinstance(rule_expression, str):
            return rule_expression

        # Normalise spacing
        rule_expression = rule_expression.replace("(", " ( ").replace(")", " ) ")
        tokens = rule_expression.split()
        output = []
        i = 0

        while i < len(tokens):
            token = tokens[i].upper()

            if token == "AND":
                output.append("and")
            elif token == "OR":
                output.append("or")
            elif token == "XOR":
                output.append("^")
            elif token == "NOT":
                # Look ahead for the operand
                if i + 1 < len(tokens):
                    next_token = tokens[i + 1]
                    # if it's an entity like A, B, etc.
                    if next_token not in {"AND", "OR", "XOR", "NOT", ")", "("}:
                        output.append(f"(not {next_token})")
                        i += 1  # skip next token
                    else:
                        output.append("not")
                else:
                    output.append("not")
            else:
                output.append(token)

            i += 1

        return " ".join(output)

    from sympy.logic.boolalg import SOPform
    from sympy import symbols, simplify_logic

class TruthTableToRules:
    """Converts a truth table to Boolean rule expressions.

    - `minimise=False`: Uses fast Sum-of-Products (SOP) expansion (default)
    - `minimise=True`: Uses Quine-McCluskey logic simplification (via sympy) - more computationally intensive.
    - `readable=True`: Returns GUI-readable form using A, B, C... instead of state[0], etc.
    """

    @staticmethod
    def convert(truth_table, entities, minimise=False, readable=False):
        from sympy.logic.boolalg import SOPform
        from sympy import symbols, simplify_logic

        rules = {}
        sym_vars = symbols(entities)

        for i, entity in enumerate(entities):
            if minimise:
                # Minimisation via Quine-McCluskey - longer
                minterms = [
                    [int(b) for b in input_state]
                    for input_state, output_state in truth_table.items()
                    if output_state[i] == 1
                ]

                if not minterms:
                    rules[entity] = "0"
                    continue

                expr = SOPform(sym_vars, minterms)
                simplified = simplify_logic(expr, form='dnf')

                if readable:
                    # GUI-readable format
                    rule_str = str(simplified).replace("~", "NOT ")
                    rule_str = rule_str.replace("&", "AND")
                    rule_str = rule_str.replace("|", "OR")
                    rule_str = rule_str.replace("(", "( ").replace(")", " )")
                else:
                    # Eval-compatible format
                    rule_str = str(simplified)
                    for idx, var in enumerate(sym_vars):
                        rule_str = rule_str.replace(str(var), f"state[{idx}]")
                    rule_str = rule_str.replace("~", "not ")
                    rule_str = rule_str.replace("&", "and")
                    rule_str = rule_str.replace("|", "or")

                rules[entity] = rule_str

            else:
                # Fast SOP (no minimisation)
                terms = []
                for input_state, output_state in truth_table.items():
                    if output_state[i] == 1:
                        term = []
                        for j, val in enumerate(input_state):
                            if val == "0":
                                term.append(f"NOT {entities[j]}" if readable else f"not state[{j}]")
                            else:
                                term.append(entities[j] if readable else f"state[{j}]")
                        terms.append(f"({' AND '.join(term)})" if readable else f"({' and '.join(term)})")
                rules[entity] = " OR ".join(terms) if readable else " or ".join(terms) if terms else "0"

        return rules



"""""""""
class TruthTableToRules:
    #Converts a truth table to Boolean rule expressions (Sum of Products form).

    @staticmethod
    def convert(truth_table, entities):
        rules = {}
        for i, entity in enumerate(entities):
            terms = []
            for input_state, output_state in truth_table.items():
                if output_state[i] == 1:  # If the entity's next state is 1
                    term = []
                    for j, val in enumerate(input_state):
                        if val == "0":
                            term.append(f"NOT {entities[j]}")
                        else:
                            term.append(entities[j])
                    terms.append(f"({' AND '.join(term)})")
            rules[entity] = " OR ".join(terms) if terms else "0"
        return rules
"""""""""
"""""""""
class TruthTableToRules:
    # Converts a truth table to Boolean rule expressions, compatible with eval(state) usage.

    @staticmethod
    def convert(truth_table, entities):
        rules = {}
        sym_vars = symbols(entities)  # e.g., A, B, C, D

        for i, entity in enumerate(entities):
            minterms = []
            for input_state, output_state in truth_table.items():
                if output_state[i] == 1:
                    minterms.append([int(b) for b in input_state])

            if not minterms:
                rules[entity] = "0"
                continue

            # Use Quine-McCluskey minimization via SOPform
            expr = SOPform(sym_vars, minterms)
            simplified = simplify_logic(expr, form='dnf')

            # Convert sympy expr to eval-safe rule using state[i]
            rule_str = str(simplified)
            for idx, var in enumerate(sym_vars):
                rule_str = rule_str.replace(str(var), f"state[{idx}]")
            rule_str = rule_str.replace("~", "not ")
            rule_str = rule_str.replace("&", "and")
            rule_str = rule_str.replace("|", "or")
            rule_str = rule_str.replace("(", "( ").replace(")", " )")

            rules[entity] = rule_str

        return rules
"""""""""

