import os

def validate_truth_table_inputs(network_name, truth_table, entity_count, saved_folder="saved_networks"):
    """
    Validates the truth table before saving.

    Returns:
        bool, str: True if valid, otherwise False and an error message.
    """

    if not network_name or not network_name.strip():
        return False, "Network name is required."

    filename = network_name if network_name.endswith(".json") else network_name + ".json"
    path = os.path.join(saved_folder, filename)
    if os.path.exists(path):
        return False, f"A network named '{filename}' already exists."

    for row_index, (input_state, output_values) in enumerate(truth_table.items()):
        if len(output_values) != entity_count:
            return False, f"Row {row_index + 1}: Expected {entity_count} outputs, got {len(output_values)}."

        for i, val in enumerate(output_values):
            val_str = str(val).strip()
            if val_str not in ("0", "1"):
                col_letter = chr(65 + i) + "'"  # A', B', etc.
                return False, f"Row {row_index + 1}: Output at column '{col_letter}' must be 0 or 1."

    return True, "Valid truth table input."

