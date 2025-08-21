#!/bin/bash

echo "Analysing..."
claude -p --verbose --output-format stream-json < tools/prompts/analyse.txt | tee results/usage/analyse.json
./tools/claude-usage/claude-usage results/usage/analyse.json > results/usage/analyse-agg.json
echo "Analyse done."

echo "Optimising..."
claude -p --verbose --output-format stream-json < tools/prompts/optimise.txt | tee results/usage/optimise.json
./tools/claude-usage/claude-usage results/usage/optimise.json > results/usage/optimise.json
echo "Optimisation done."
