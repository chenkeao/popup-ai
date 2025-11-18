#!/bin/bash
# Quick development run script

# Ensure we're in the project directory
cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Virtual environment not found. Run ./setup-dev.sh first."
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Run the application
export PYTHONPATH="${PWD}:${PYTHONPATH}"
python -m popup_ai.main "$@"
