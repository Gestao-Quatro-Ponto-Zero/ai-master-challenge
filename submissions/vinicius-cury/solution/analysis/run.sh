#!/bin/bash
# Execute a notebook headlessly and show output
# Usage: ./analysis/run.sh 01_data_exploration
NOTEBOOK="analysis/${1}.ipynb"
OUTPUT="analysis/output/${1}_output.ipynb"
mkdir -p analysis/output
analysis/.venv/bin/python3 -m papermill "$NOTEBOOK" "$OUTPUT" --kernel optiflow --log-output
echo "Output saved to $OUTPUT"
