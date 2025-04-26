import os
from graphviz import Digraph
from src.boolean_network_representation.network import BooleanNetwork
from src.boolean_network_representation.storage import BooleanNetworkStorage


def generate_state_graph(network_name: str, output_folder='saved_networks'):
    """Generates a state graph for a saved Boolean Network - GRAPHVIZ IMPLEMENTATION
    """
    try:

        network_data = BooleanNetworkStorage.load_network(network_name)
        entities = network_data.get("entities", [])
        truth_table = network_data.get("truth_table", {})


        if not isinstance(truth_table, dict) or len(truth_table) == 0:
            raise ValueError(f"The network '{network_name}' has no valid truth table. Please check the JSON file.")


        entity_count = len(entities)
        bn = BooleanNetwork(entity_count)


        dot = Digraph(comment=f'{entity_count}-Entity Boolean Network State Graph')
        dot.attr(rankdir='LR')

        for state, next_state in truth_table.items():
            next_state_str = "".join(str(bit) for bit in next_state)
            dot.node(state, state)
            dot.edge(state, next_state_str)

        graph_filename = os.path.join(output_folder, f"{network_name.split('.')[0]}_state_graph")
        dot.render(graph_filename, format='png', view=True)

        print(f"State graph generated successfully: {graph_filename}.png")

    except Exception as e:
        print(f"Error generating state graph: {e}")