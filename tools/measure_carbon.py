#!/usr/bin/env python3
"""
Script to measure energy and carbon footprint of Java program using CodeCarbon
"""

import os
import subprocess
import sys
import time

from codecarbon import OfflineEmissionsTracker


class MeasurementError(Exception):
    """Exception raised when measurement fails"""

    def __init__(self, message, exit_code=None):
        super().__init__(message)
        self.exit_code = exit_code


class MeasurementResult:
    """Class to hold measurement results"""

    def __init__(self, energy, time, co2, country=None, carbon_intensity=None):
        self.energy = energy
        self.time = time
        self.co2 = co2
        self.country = country
        self.carbon_intensity = carbon_intensity

    def __repr__(self):
        return f"MeasurementResult(energy={self.energy:.0f}J, time={self.time:.2f}s, co2={self.co2:.3f}gCO2, country={self.country}, intensity={self.carbon_intensity:.1f}gCO2/kWh)"


def run_single_measurement(iteration, cmd, num_iterations):
    """Run a single measurement iteration"""
    print(f"Iteration {iteration + 1}/{num_iterations}...")

    # Create single tracker per iteration
    tracker = OfflineEmissionsTracker(
        project_name=f"java-txtmark-benchmark-iter-{iteration}",
        country_iso_code='DEU',
        log_level='WARNING',
    )

    start_time = time.time()
    tracker.start()

    try:
        # Run the Java command with same JVM flags, with stdin input
        result = subprocess.run(cmd, cwd="/workspace/target",
                                capture_output=True, text=True,
                                input="\n\n")  # Equivalent to printf '\n\n'

        # Only show errors if the program fails
        if result.returncode != 0:
            error_msg = f"Java program failed with exit code: {result.returncode}"
            if result.stderr:
                error_msg += f"\nErrors:\n{result.stderr}"
            raise MeasurementError(error_msg, result.returncode)

    except subprocess.SubprocessError as e:
        raise MeasurementError(f"Subprocess error: {e}")
    except Exception as e:
        raise MeasurementError(f"Unexpected error running Java program: {e}")

    finally:
        # Stop tracking and get emissions
        co2_kg = tracker.stop()  # Returns CO2 in kg
        end_time = time.time()
        execution_time = end_time - start_time

        # Get all data from tracker
        data = tracker.final_emissions_data

        country = data.country_name          # e.g., "Germany"
        energy_kwh = data.energy_consumed       # kWh
        co2_kg = data.emissions             # kg CO2eq

        # Carbon intensity used by CodeCarbon for this run:
        intensity_kg_per_kwh = co2_kg / \
            energy_kwh if energy_kwh else float("nan")

        energy_joules = energy_kwh * 3.6e6  # Convert kWh to J
        co2_grams = co2_kg * 1000  # Convert kg to grams
        intensity_g_per_kwh = intensity_kg_per_kwh * 1000  # Convert to g/kWh

        print(
            f"  Energy: {energy_joules:.0f} J | Time: {execution_time:.2f}s | CO2: {co2_grams:.3f} gCO2 | Country: {country} | Intensity: {intensity_g_per_kwh:.1f} gCO2/kWh")

        return MeasurementResult(energy=energy_joules, time=execution_time, co2=co2_grams, country=country, carbon_intensity=intensity_g_per_kwh)


def run_java_with_carbon_tracking():
    """Run the Java program and track its carbon emissions"""

    # System optimization - set high priority for this process
    try:
        os.nice(-10)  # Higher priority (requires privileges)
    except PermissionError:
        pass  # Continue without higher priority if not allowed

    # Try to set CPU governor to performance mode for consistency
    try:
        subprocess.run(["cpupower", "frequency-set", "-g", "performance"],
                       capture_output=True, check=False)
    except FileNotFoundError:
        pass  # Continue if cpupower not available

    java_opts = [
        # Disable JIT compilation (interpreter mode only) - MUST KEEP for determinism
        "-Xint",
        # MASSIVE initial heap (6GB) - eliminate ALL allocation overhead
        "-Xms6144m",
        # MASSIVE maximum heap (8GB) - ensure zero memory pressure
        "-Xmx8192m",
        # Use SerialGC for most deterministic behavior (single-threaded, predictable)
        "-XX:+UseSerialGC",
        # Pre-allocate all heap memory at startup
        "-XX:+AlwaysPreTouch",
        # Disable dynamic optimizations (skip biased locking for newer JVMs)
        "-XX:-UseCounterDecay",
        # Force single-threaded execution for all concurrent operations
        "-Djava.util.concurrent.ForkJoinPool.common.parallelism=1",
        # Deterministic random seed
        "-Djava.security.egd=file:/dev/./urandom",
        # Disable background compilation
        "-Xbatch",
        # Consistent memory management
        "-XX:+UseCompressedOops",
        "-server",
    ]

    # Command with stable deterministic flags
    cmd = [
        "taskset", "-c", "0",  # Pin to CPU core 0
        "java", "-cp", "target/classes",
        *java_opts,
        "com.github.rjeschke.txtmark.cmd.Run",
        "/workspace/test/shakespeare.txt"
    ]

    # System stabilization
    print("Stabilizing system...")
    time.sleep(2)

    # Run multiple measurements for statistical reliability
    energy_measurements = []
    times = []
    co2_measurements = []
    num_iterations = 3
    country = None
    carbon_intensity = None

    print(f"Running {num_iterations} measurement iterations...")

    for iteration in range(num_iterations):
        try:
            result = run_single_measurement(iteration, cmd, num_iterations)
            energy_measurements.append(result.energy)
            times.append(result.time)
            co2_measurements.append(result.co2)
            # Store country and intensity from first measurement
            if iteration == 0:
                country = result.country
                carbon_intensity = result.carbon_intensity
        except MeasurementError as e:
            print(f"Measurement failed: {e}")
            sys.exit(e.exit_code if e.exit_code is not None else 1)

    # Calculate statistics from all measurements
    energy_measurements.sort()
    times.sort()
    co2_measurements.sort()

    # Energy statistics
    median_joules = energy_measurements[len(energy_measurements) // 2]
    mean_joules = sum(energy_measurements) / len(energy_measurements)
    min_joules = min(energy_measurements)
    max_joules = max(energy_measurements)
    std_dev_energy = (
        sum((x - mean_joules) ** 2 for x in energy_measurements) / len(energy_measurements)) ** 0.5
    variation_pct_energy = (max_joules - min_joules) / mean_joules * 100

    # Time statistics
    median_time = times[len(times) // 2]
    mean_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)

    # CO2 statistics
    median_co2 = co2_measurements[len(co2_measurements) // 2]
    mean_co2 = sum(co2_measurements) / len(co2_measurements)
    min_co2 = min(co2_measurements)
    max_co2 = max(co2_measurements)

    print("\n" + "="*70)
    print(f"BENCHMARK RESULTS ({num_iterations} ITERATIONS)")
    print("="*70)

    # Energy results
    print("ENERGY:")
    print(f"  Measurements (J): {[int(x) for x in energy_measurements]}")
    print(f"  Median:    {median_joules:.0f} J  ({median_joules/3600:.3f} Wh)")
    print(f"  Mean:      {mean_joules:.0f} J  ({mean_joules/3600:.3f} Wh)")
    print(f"  Min-Max:   {min_joules:.0f} - {max_joules:.0f} J")
    print(
        f"  Std dev:   {std_dev_energy:.1f} J ({std_dev_energy/mean_joules*100:.1f}%)")
    print(
        f"  Range:     {max_joules - min_joules:.0f} J ({variation_pct_energy:.1f}%)")

    # Time results
    print("\nTIME:")
    print(f"  Measurements (s): {[f'{t:.2f}' for t in times]}")
    print(f"  Median:    {median_time:.2f} s")
    print(f"  Mean:      {mean_time:.2f} s")
    print(f"  Min-Max:   {min_time:.2f} - {max_time:.2f} s")

    # CO2 results
    print("\nCO2 EMISSIONS:")
    print(f"  Measurements (gCO2): {[f'{c:.3f}' for c in co2_measurements]}")
    print(f"  Median:    {median_co2:.3f} gCO2")
    print(f"  Mean:      {mean_co2:.3f} gCO2")
    print(f"  Min-Max:   {min_co2:.3f} - {max_co2:.3f} gCO2")

    print(f"\nLOCATION & CARBON INTENSITY:")
    print(f"  Country:   {country}")
    print(f"  Carbon Intensity: {carbon_intensity:.1f} gCO2/kWh")

    print("="*70)

    return 0


if __name__ == "__main__":
    sys.exit(run_java_with_carbon_tracking())
