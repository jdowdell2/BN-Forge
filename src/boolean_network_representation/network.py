import string
from src.boolean_network_representation.rules import RuleLoader
from graphviz import Digraph
import networkx as nx


class BooleanNetwork:
    """
    Boolean Network representation - connected to RuleLoader
    """
    def __init__(self, entity_count, rule_source="manual"):
        self.entity_count = entity_count
        self.nodes = list(string.ascii_uppercase[:entity_count]) # entities can go up to Z (26) - limit is 10 entities anyway
        self.states = [f"{i:0{entity_count}b}" for i in range(2 ** entity_count)]

        # Initialize RuleLoader as a blueprint for rules
        self._rule_loader = RuleLoader(entity_count)
        self.initial_rules = self._rule_loader.load_rules(rule_source)
        self.current_rules = self.initial_rules.copy()

        # Check that the number of rules matches the number of entities
        self._validate_rules()

    def _validate_rules(self):
        """
        Checks that the number of rules matches the number of entities.
        """
        if len(self.current_rules) != self.entity_count:
            raise ValueError("Number of rules must match the number of entities")

    def get_next_state(self, current_state):
        """
        Calculates the next state for each entity using current_rules.

        Args:
        - current_state: A list of integers representing the current state of each entity.

        Returns:
        - next_state: A list of integers representing the next state of each entity.
        """
        next_state = []
        for i, rule in enumerate(self.current_rules):
            if rule is not None:
                next_state.append(rule(current_state, i))
            else:
                next_state.append(current_state[i])  # If no rule, keep current state
        return next_state

    def get_state_transition(self):
        """
        Generates all state transitions for the Boolean Network.

        Returns:
        - transitions: A dictionary with current state as keys and next state as values.
        """
        transitions = {}
        for state in self.states:
            current_state = list(map(int, state))
            next_state = self.get_next_state(current_state)
            next_state_str = ''.join(map(str, next_state))
            transitions[state] = next_state_str
        return transitions

    def generate_state_graph(self, filename='state_graph', view=True):
        """
        Generates the state graph for the Boolean Network.
        """
        dot = Digraph(comment=f'{self.entity_count}-Entity Boolean Network State Graph')
        dot.attr(rankdir='LR')

        for state, next_state in self.get_state_transition().items():
            dot.node(state, state)
            dot.edge(state, next_state, label=f"{state} → {next_state}")

        dot.render(filename, format='png', view=view)

    def print_truth_table(self):
        """
        Generates and prints the truth table for the Boolean Network.
        """
        print("\nTruth Table for Boolean Network")
        header = " | ".join(self.nodes) + " | " + " | ".join([f"{n}'" for n in self.nodes]) + " | Description"
        print(header)
        print("-" * len(header))

        for state in self.states:
            current_state = list(map(int, state))
            next_state = self.get_next_state(current_state)
            next_state_str = ''.join(map(str, next_state))

            transition_desc = ", ".join(
                [f"{self.nodes[i]}'={current_state[i]}->{next_state[i]}" for i in range(self.entity_count)]
            )
            print(f"  {' '.join(state)} | {' '.join(map(str, next_state))} | {transition_desc}")

    def generate_truth_table(self):
        """
        Generates and returns the truth table for the Boolean Network as a dictionary.
        """
        truth_table = {}  # Dictionary to store the truth table

        for state in self.states:
            current_state = list(map(int, state))
            next_state = self.get_next_state(current_state)
            next_state_str = ''.join(map(str, next_state))

            truth_table[state] = next_state  # Store the next state as list

        return truth_table


    def detect_attractors(self):
        """
        Detects attractors in the Boolean Network.
        """
        attractors = []

        for initial_state in self.states:
            visited = {}
            current_state = initial_state

            while current_state not in visited:
                visited[current_state] = len(visited)
                current_state_list = list(map(int, list(current_state)))
                next_state_list = self.get_next_state(current_state_list)
                next_state = ''.join(map(str, next_state_list))
                current_state = next_state

            start = visited[current_state]
            cycle = list(visited.keys())[start:]
            min_rotation = min([cycle[i:] + cycle[:i] for i in range(len(cycle))])
            attractors.append(min_rotation)

        unique_attractors = []
        for attractor in attractors:
            if attractor not in unique_attractors:
                unique_attractors.append(attractor)

        print("\nDetected Attractors:")
        for attractor in unique_attractors:
            print("Cycle:", " → ".join(attractor))

        return unique_attractors

    def build_attractor_graph(self, cycles):
        """
        Builds a networkx attractor graph - for static visualisation not live visualisation
        Each cycle is drawn as a ring of states.

        """
        import networkx as nx
        G = nx.DiGraph()
        for cycle in cycles:
            # For each cycle, connect every state[i] to state[i+1], wrapping at the end
            for i in range(len(cycle)):
                src = cycle[i]
                dst = cycle[(i + 1) % len(cycle)]
                G.add_node(src)
                G.add_node(dst)
                G.add_edge(src, dst)
        return G

    def infer_wiring(self):
        """
        Uses input flipping to detect which nodes influence each output node. Used in building entity-interaction wiring diagrams.
        Returns dict: {target_node: set(input_nodes_that_affect_it)}
        """
        dependencies = {target: set() for target in self.nodes}
        all_inputs = [list(map(int, f"{i:0{self.entity_count}b}")) for i in range(2 ** self.entity_count)]

        for state in all_inputs:
            original = self.get_next_state(state)

            for i in range(self.entity_count):
                flipped = state[:]
                flipped[i] ^= 1
                flipped_next = self.get_next_state(flipped)

                for j in range(self.entity_count):
                    if original[j] != flipped_next[j]:
                        dependencies[self.nodes[j]].add(self.nodes[i])

        return dependencies

    def build_wiring_graph(self, deps):
        """
        Uses dict from infer_wiring to build static entity-interaction wiring diagram (in networkx).
        """
        G = nx.DiGraph()
        for target, sources in deps.items():
            for source in sources:
                G.add_edge(source, target)
        return G

    def generate_wiring_diagram(self, filename='wiring_diagram', view=True):
        """
        Generates a entity-interaction wiring diagram PNG using Graphviz.
        """
        deps = self.infer_wiring()
        dot = Digraph(comment=f'{self.entity_count}-Entity Boolean Network Wiring Diagram')
        dot.attr(rankdir='LR')
        dot.attr(label="Wiring Diagram", fontsize="20", labelloc="t", fontname="Segoe UI")

        for node in self.nodes:
            dot.node(node)

        for target, sources in deps.items():
            for source in sources:
                dot.edge(source, target)

        dot.render(filename, format='png', view=view)
