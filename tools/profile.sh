#!/bin/bash
#
# JFR Profiling Script
# Profiles Java application with JFR and analyzes hotspots
#

# Configuration constants
RESULT_PATH="/workspace/results"
JFR_FILE="$RESULT_PATH/profile.jfr"
JSON_REPORT="hotspots_profile.json"
PACKAGE_FILTER="com.github"

echo "🔍 Starting JFR Profiling..."

# Initialize SDKman 
source "/home/ubuntu/.sdkman/bin/sdkman-init.sh"


# Force reload SDKman in case it's not in PATH
source "$HOME/.sdkman/bin/sdkman-init.sh" 2>/dev/null || true

# Install and switch to Java 8 for running txtmark (skip if sdk not available)
echo "☕ Setting up Java 8..."
sdk use java 8.0.422-tem
java -version

# Java optimization flags for deterministic execution (from measure_carbon.py)
JAVA_OPTS=(
    # Disable JIT compilation (interpreter mode only) - MUST KEEP for determinism
    "-Xint"
    # MASSIVE initial heap (6GB) - eliminate ALL allocation overhead
    "-Xms6144m"
    # MASSIVE maximum heap (8GB) - ensure zero memory pressure  
    "-Xmx8192m"
    # Use SerialGC for most deterministic behavior (single-threaded, predictable)
    "-XX:+UseSerialGC"
    # Pre-allocate all heap memory at startup
    "-XX:+AlwaysPreTouch"
    # Disable dynamic optimizations
    "-XX:-UseCounterDecay"
    # Force single-threaded execution for all concurrent operations
    "-Djava.util.concurrent.ForkJoinPool.common.parallelism=1"
    # Deterministic random seed
    "-Djava.security.egd=file:/dev/./urandom"
    # Disable background compilation
    "-Xbatch"
    # Consistent memory management
    "-XX:+UseCompressedOops"
    "-server"
)

# JFR profiling flags (Java 8 compatible)
JFR_OPTS=(
    "-XX:+UnlockCommercialFeatures"
    "-XX:+FlightRecorder"
    "-XX:StartFlightRecording=duration=30s,filename=$JFR_FILE,settings=profile,disk=true"
)

echo "📊 Running Java application with JFR profiling..."
echo "   JFR file: $JFR_FILE"
echo "   Package filter: $PACKAGE_FILTER"

# Run with profiling (taskset for CPU pinning in Docker)
java -cp target/classes \
    "${JAVA_OPTS[@]}" \
    "${JFR_OPTS[@]}" \
    com.github.rjeschke.txtmark.cmd.Run \
    /workspace/test/test.txt > /dev/null

if [ $? -ne 0 ]; then
    echo "❌ Java application failed"
    exit 1
fi

echo "✅ JFR recording complete: $JFR_FILE"

# Analyze JFR file with pre-built analyzer
echo "🔍 Analyzing JFR hotspots..."

# Check if analyzer exists
if [ ! -f /workspace/tools/jfr-analyser/target/jfr-analyser-1.0.0.jar ]; then
    echo "❌ JFR analyzer not found! Run /workspace/tools/install.sh first"
    exit 1
fi

# Run analysis with Java 21
sdk use java 21.0.4-tem
java -jar /workspace/tools/jfr-analyser/target/jfr-analyser-1.0.0.jar \
    "$JFR_FILE" \
    "$PACKAGE_FILTER" \
    "$RESULT_PATH/$JSON_REPORT" \
    -s "/workspace/target"

if [ $? -eq 0 ]; then
    echo "✅ Analysis complete!"
    echo "📄 Hotspot report: $RESULT_PATH/$JSON_REPORT"
    echo "🔥 Top 5 CPU hotspots:"
    head -20 "$RESULT_PATH/$JSON_REPORT" | grep -A 5 '"cpuPercent"'
else
    echo "❌ Analysis failed"
    exit 1
fi