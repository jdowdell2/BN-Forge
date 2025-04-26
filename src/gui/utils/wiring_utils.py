
import networkx as nx
import matplotlib.pyplot as plt


def infer_wiring_from_boolean_network(network):
    entity_count = network.entity_count
    dependencies = {f"N{i + 1}": set() for i in range(entity_count)}
    inputs = [list(map(int, f"{i:0{entity_count}b}")) for i in range(2 ** entity_count)]

    for state in inputs:
        base_next = network.get_next_state(state)

        for i in range(entity_count):
            flipped = state[:]
            flipped[i] ^= 1
            flipped_next = network.get_next_state(flipped)

            for j in range(entity_count):
                if base_next[j] != flipped_next[j]:
                    dependencies[f"N{j + 1}"].add(f"N{i + 1}")

    return dependencies
def build_graph_from_dependencies(deps):
    G = nx.DiGraph()
    for target, sources in deps.items():
        for src in sources:
            G.add_edge(src, target)
    return G