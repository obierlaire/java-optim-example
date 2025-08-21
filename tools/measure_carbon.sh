#!/bin/bash
"""
Shell script to measure carbon footprint of Java program
Usage: ./tools/measure_carbon.sh
"""

# Ensure we're in the right directory
cd /workspace

# Install codecarbon if not already installed
if ! python3 -c "import codecarbon" 2>/dev/null; then
    echo "Installing codecarbon..."
    pip install codecarbon
fi

sdk use java 8.0.422-tem

# Create results directory if it doesn't exist
mkdir -p /workspace/results

cd /workspace/target
mvn install -Dmaven.compiler.debug=true

# Run the carbon measurement script
python3 /workspace/tools/measure_carbon.py