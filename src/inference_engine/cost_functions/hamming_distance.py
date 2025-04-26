def calculate_hamming_distance(desired_trace, current_trace):
    """
    Calculates the physical Hamming Distance between two truth tables.
    """
    hamming_distance = 0
    for state, desired_output in desired_trace.items(): # Iterate over every state in the desired trace
        current_output = current_trace.get(state)

        if current_output is None:
            raise ValueError(f"State {state} not found in the current trace. Check your network generation.")

        for i in range(len(desired_output)): # Compare each bit in the output list
            if desired_output[i] != current_output[i]:
                hamming_distance += 1 # increment each mismatch
    return hamming_distance;



