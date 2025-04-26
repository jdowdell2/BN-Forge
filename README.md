# BNForge - a Boolean Network Metaheuristic Tool

This tool provides an interactive environment for defining, simulating, visualising, and inferring Boolean Networks using metaheuristic approaches, specifically Genetic Algorithms and Simulated Annealing.

Designed for experimentation and visual feedback, the tool is modular, extensible, and aims to be suitable for both research and educational use.

---

## Features

- Define Boolean Networks using rules or truth tables, or import trace data through csv or Excel file.
- Interactive GUI for viewing and exporting static visualisation.
- Metaheuristic inference optimisation via Genetic Algorithm (GA) or Simulated Annealing (SA)
- Live evolution tracking with cost function plots, entity-interaction diagrams and attractor diagrams in real-time, and optional logging+plotting of final results.

---

## Project Structure

```
src/
 ├── boolean_network_representation/   # BN simulation engine and storage
 ├── inference_engine/                 # Metaheuristic algorithms and search operators
 ├── data_processing/                  # Validation, parsing, truth table helpers
 ├── experiments/                      # Experiment runners and setup scripts
 ├── gui/                               # GUI interface, split by window/component
 ├── static_visualisations/             # Standalone graph visualisation utilities
outputs/
 ├── saved_networks/                    # Saved user networks
 ├── experiment_results/                # Saved experiment outputs (batch and single-run)
example_files/                           # Example input networks and configs
main.py                                  # Entry point for launching the tool
```

---

## Installation

Python 3.10+ is recommended. This project was developed in Python 3.12.6, but has been compatibility tested in 3.10 and 3.13.

1. Clone the repository:
```bash
git clone https://github.com/jdowdell2/BNForge.git
cd BNForge
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

---

## Running the Tool

Start the GUI:
```bash
python main.py
```

You will be presented with a main menu allowing you to:
- Import, define or modify networks
- Visualise entity interaction diagrams, synchronous state graphs or attractor diagrams of a Boolean Network.
- Launch inference experiments with metaheuristics in single runs and batch experiments.
- Visualise live inference evolution with cost (accuracy to desired trace) progress, entity interaction and wiring diagrams

---

## Example Files
The `example_files/` folder contains:
- Sample networks (`.json`). - Shows the format of importing via JSON. Only one of the next-state rules or truth table trace must be complete - as long as JSON keys are correct.
- Example experiment configs (`.yaml`) - Shows the format of how yamls files are run with parameters for inference, allows for inference via CLI.
- Example import files (.csv and .xlsx) - Shows the format of importing via CSV or XLSV (Excel file). Header row will be automatically removed if exists. 

##Outputs
The tool automatically generates outputs during usage:

- Saved Boolean Networks are stored in the outputs/saved_networks/ folder.

- Results from experiments (both batch and single-run), including logging and plotting are stored in the  outputs/experiment_results/ folder, with the name of the network as a subfolder.






## Future Work

- Add support for asynchronous Boolean networks
- Have a step-based visualisation engine so users can control pace of evolution during inference.
- Export attractor basins as images.
- Expanded import support to infer noisy traces or real-world systems.

---

## License

MIT License – see `LICENSE` file for full details.

---

## Author

**[James Dowdell]**  
BSc Computer Science Final Year Student
Newcastle University
Year: 2025
The tool was developed as part of my Undergraduate dissertation project titled:
> Investigating Metaheuristic Approaches to Evolve Boolean Networks.