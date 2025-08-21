#!/bin/bash
#
# JFR Analyzer Installation Script
# Builds and prepares the JFR analyzer for profiling
#

echo "🔨 Building JFR Analyzer..."

# Navigate to analyzer directory
cd /workspace/tools/jfr-analyser

# Remove target directory manually and build
echo "🏗️  Building JFR analyzer..."
mvn clean compile package