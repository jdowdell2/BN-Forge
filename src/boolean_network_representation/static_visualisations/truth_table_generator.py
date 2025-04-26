from src.boolean_network_representation.storage import BooleanNetworkStorage


def generate_truth_table(network_name: str):
    """Generates and returns a truth table for a saved Boolean Network.

    Args:
        network_name (str): Name of the network to load (must be in saved_networks).

    Returns:
        str: Formatted truth table as a string.
    """
    try:
        # Load network
        network_data = BooleanNetworkStorage.load_network(network_name)
        entities = network_data["entities"]
        truth_table = network_data.get("truth_table", {})


        output = f"Truth Table for {network_name}:\n"
        header = " | ".join(entities) + " | " + " | ".join([f"{e}'" for e in entities])
        output += header + "\n" + "-" * len(header) + "\n"

        # Display truth table
        for state, next_state in truth_table.items():
            current_state = " ".join(str(bit) for bit in state)
            next_state_str = " ".join(str(bit) for bit in next_state)
            output += f"  {current_state} | {next_state_str}\n"

        return output

    except Exception as e:
        return f"Error generating truth table: {str(e)}"
